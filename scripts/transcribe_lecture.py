#!/usr/bin/env python3
"""
transcribe_lecture.py
=====================
Two-tier lecture transcription:
  1. PRIMARY  – mlx-qwen3-asr running directly on Apple Silicon GPU (default).
  2. FALLBACK – SoundScribe Agent CLI (soundscribe_fallback.py), triggered
                automatically when the primary path raises any exception.

Pass --no-fallback to disable the second tier.
"""
import os
import sys
import argparse
import time
import subprocess
import re
import signal
from dotenv import load_dotenv

# Load environment variables (such as HF_TOKEN) from .env
load_dotenv()

# Global for graceful shutdown cleanup
_temp_wav_path = None

def _sigterm_handler(signum, frame):
    """Clean up temp files on SIGTERM (sent by the cancel endpoint)."""
    if _temp_wav_path and os.path.exists(_temp_wav_path):
        try:
            os.remove(_temp_wav_path)
        except Exception:
            pass
    print("\n[CANCELLED] Transcription stopped by user.", flush=True)
    sys.exit(130)

signal.signal(signal.SIGTERM, _sigterm_handler)

def extract_audio(video_path: str, wav_path: str):
    """Extracts 16kHz mono audio from video file using ffmpeg"""
    print(f"Extracting audio track from '{video_path}'...")
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        wav_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def get_media_duration(path: str) -> float:
    """Returns media duration in seconds using ffprobe, or 0 if unavailable."""
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            path,
        ]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return float(result.stdout.strip())
    except Exception:
        return 0.0

def format_srt_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        secs += 1
        millis -= 1000
    if secs >= 60:
        minutes += 1
        secs -= 60
    if minutes >= 60:
        hours += 1
        minutes -= 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def write_srt(segments, srt_path):
    with open(srt_path, "w", encoding="utf-8") as f:
        for idx, seg in enumerate(segments, 1):
            start = seg.get("start", 0.0)
            end = seg.get("end", start + 2.0)
            text = seg.get("text", "").strip()
            
            f.write(f"{idx}\n")
            f.write(f"{format_srt_time(start)} --> {format_srt_time(end)}\n")
            f.write(f"{text}\n\n")

def parse_srt_end_time(srt_path: str) -> float:
    if not os.path.exists(srt_path):
        return 0.0
    pattern = re.compile(r"-->\s*(\d+):(\d{2}):(\d{2}),(\d{3})")
    end_time = 0.0
    with open(srt_path, "r", encoding="utf-8") as f:
        for line in f:
            match = pattern.search(line)
            if not match:
                continue
            h, m, s, ms = map(int, match.groups())
            end_time = max(end_time, h * 3600 + m * 60 + s + ms / 1000)
    return end_time

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Two-tier lecture transcriber.\n"
            "  Primary : mlx-qwen3-asr on Apple Silicon GPU (fast, offline).\n"
            "  Fallback: SoundScribe Agent CLI (same Qwen3-ASR model, via app).\n"
        )
    )
    parser.add_argument("--input", required=True, help="Path to input video or audio file")
    parser.add_argument("--output-dir", default="lecture-input", help="Directory to save the transcripts")
    parser.add_argument("--model", default="mlx-community/Qwen3-ASR-1.7B-4bit", 
                        help="MLX model repository name on Hugging Face")
    parser.add_argument("--language", default="hi", help="Language code, e.g. hi (Hindi), en (English) or auto")
    parser.add_argument("--context", default="", help="Optional domain vocabulary/context to bias recognition")
    parser.add_argument("--min-duration-ratio", type=float, default=0.85,
                        help="Fail if final SRT ends before this ratio of the input media duration")
    parser.add_argument("--allow-truncated", action="store_true",
                        help="Do not fail when the ASR model reports length truncation")
    parser.add_argument("--keep-temp-audio", action="store_true",
                        help="Keep extracted 16 kHz WAV beside the transcript for debugging")
    parser.add_argument("--timestamps", action="store_true",
                        help="Enable word-level timestamps via native forced aligner (slower, requires downloading Forced Aligner model)")
    parser.add_argument("--draft-model", default=None,
                        help="Hugging Face repo name of the draft model for speculative decoding (e.g. mlx-community/Qwen3-ASR-0.6B-8bit)")
    parser.add_argument("--num-draft-tokens", type=int, default=4,
                        help="Number of tokens to generate with the draft model during speculative decoding")
    # ── Fallback control ────────────────────────────────────────────────────
    parser.add_argument("--no-fallback", action="store_true",
                        help="Disable SoundScribe fallback; exit with error if the primary path fails")
    parser.add_argument("--fallback-timeout", type=int,
                        default=int(os.environ.get("SOUNDSCRIBE_FALLBACK_TIMEOUT", "3600")),
                        help="Max seconds to wait for the SoundScribe fallback job (default: 3600)")

    args = parser.parse_args()
    
    input_file = args.input
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
        
    os.makedirs(args.output_dir, exist_ok=True)
    
    is_video = input_file.lower().endswith((".mp4", ".mov", ".mkv", ".avi", ".webm"))
    temp_wav = None
    if is_video:
        global _temp_wav_path
        temp_wav = os.path.join(args.output_dir, "_temp_audio.wav")
        _temp_wav_path = temp_wav
        try:
            extract_audio(input_file, temp_wav)
            audio_to_transcribe = temp_wav
        except Exception as e:
            print(f"Error extracting audio: {e}")
            sys.exit(1)
    else:
        audio_to_transcribe = input_file
        
    start_time = time.time()
    
    try:
        from mlx_qwen3_asr import transcribe
        is_mlx = True
    except ImportError:
        is_mlx = False
        
    try:
        if is_mlx:
            print(f"Loading mlx-qwen3-asr model: {args.model}")
            # Map simple language codes to what Qwen3-ASR expects
            language = args.language
            if language == "hi":
                language = "Hindi"
            elif language == "en":
                language = "English"
            elif language == "auto":
                language = None
                
            print(f"Transcribing '{audio_to_transcribe}' on Apple Silicon GPU (Metal) using Qwen3-ASR (model: {args.model})...")
            
            def progress(event):
                name = event.get("event", "progress")
                pct = float(event.get("progress", 0.0)) * 100
                chunk = event.get("chunk_index")
                total = event.get("total_chunks")
                if chunk and total:
                    print(f"ASR progress: {pct:5.1f}% | {name} | chunk {chunk}/{total}", flush=True)
                else:
                    print(f"ASR progress: {pct:5.1f}% | {name}", flush=True)

            result = transcribe(
                audio=audio_to_transcribe,
                model=args.model,
                draft_model=args.draft_model,
                num_draft_tokens=args.num_draft_tokens,
                context=args.context,
                language=language,
                return_timestamps=args.timestamps,
                return_chunks=True,
                verbose=True,
                on_progress=progress
            )
        else:
            print("mlx-qwen3-asr not found. Falling back to faster-whisper on CPU/non-macOS system...")
            from faster_whisper import WhisperModel
            
            # For Ryzen 7 CPU, we run the fast and accurate base model using int8 quantization
            print(f"Loading faster-whisper model ('base') on CPU...")
            model = WhisperModel("base", device="cpu", compute_type="int8")
            
            # Map simple language codes
            language = args.language
            if language == "auto":
                language = None
                
            print(f"Transcribing '{audio_to_transcribe}' using faster-whisper...")
            segments, info = model.transcribe(audio_to_transcribe, beam_size=5, language=language)
            
            segments_list = []
            full_text = []
            for segment in segments:
                segments_list.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text
                })
                full_text.append(segment.text)
                print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}", flush=True)
                
            class MockResult:
                def __init__(self, text, segments):
                    self.text = text
                    self.segments = segments
                    self.chunks = segments
                    
            result = MockResult(" ".join(full_text), segments_list)
        
        # Paths for output files
        final_txt_path = os.path.join(args.output_dir, "transcript.txt")
        final_srt_path = os.path.join(args.output_dir, "transcript.srt")
        
        # Write text output
        with open(final_txt_path, "w", encoding="utf-8") as f:
            f.write(result.text)
        print(f"Saved TXT: {final_txt_path}")
        
        # Write SRT output
        if args.timestamps:
            # If word-level timestamps were explicitly requested, try segments first
            segments_to_write = result.segments or result.chunks or []
        else:
            # Otherwise use chunks for cleaner phrase-level layout with proper spelling
            segments_to_write = result.chunks or result.segments or []
            
        if segments_to_write:
            write_srt(segments_to_write, final_srt_path)
            print(f"Saved SRT: {final_srt_path}")
        else:
            print(f"WARNING: No segments/chunks returned by Qwen3-ASR. Falling back to single-segment SRT.", flush=True)
            duration = get_media_duration(audio_to_transcribe) or get_media_duration(input_file)
            fallback_segments = [{"start": 0.0, "end": duration or 10.0, "text": result.text}]
            write_srt(fallback_segments, final_srt_path)
            print(f"Saved SRT (fallback single segment): {final_srt_path}")

        if getattr(result, "truncated", False) and not args.allow_truncated:
            # Check actual SRT coverage before deciding if this is truly a problem
            duration = get_media_duration(audio_to_transcribe) or get_media_duration(input_file) or 0
            srt_end = 0.0
            if segments_to_write:
                srt_end = max(s.get("end", 0) for s in segments_to_write)
            coverage = srt_end / duration if duration > 0 else 1.0
            if coverage >= args.min_duration_ratio:
                print(f"WARNING: Some chunks were token-truncated, but overall SRT coverage is {coverage:.1%} (≥{args.min_duration_ratio:.0%}). Treating as success.")
            else:
                raise RuntimeError(
                    f"Qwen3-ASR reported length truncation and SRT coverage is only {coverage:.1%}. "
                    f"Re-run with --allow-truncated or check chunk sizes."
                )

        media_duration = get_media_duration(input_file)
        transcript_end = parse_srt_end_time(final_srt_path)
        if media_duration > 0 and transcript_end > 0:
            ratio = transcript_end / media_duration
            print(f"Completeness check: transcript ends at {transcript_end:.1f}s / media {media_duration:.1f}s ({ratio:.1%})")
            if ratio < args.min_duration_ratio:
                raise RuntimeError(
                    f"Transcript appears incomplete: end ratio {ratio:.1%} is below required {args.min_duration_ratio:.0%}."
                )

        elapsed = time.time() - start_time
        print(f"Success! Transcribed in {elapsed:.2f} seconds using Qwen3-ASR.")
        
    except Exception as primary_exc:
        print(f"\n[PRIMARY ASR FAILED] {primary_exc}")
        import traceback
        traceback.print_exc()

        if args.no_fallback:
            print("--no-fallback is set. Exiting.")
            # Clean up temp WAV before exit
            if temp_wav and os.path.exists(temp_wav) and not args.keep_temp_audio:
                try:
                    os.remove(temp_wav)
                except Exception:
                    pass
            sys.exit(1)

        # ── Tier 2: SoundScribe fallback ────────────────────────────────────
        print(
            "\n" + "=" * 60 + "\n"
            "[FALLBACK] Switching to SoundScribe Agent CLI (Qwen3-ASR 1.7B)\n"
            + "=" * 60,
            flush=True,
        )
        try:
            # Import the fallback module (same package directory)
            import importlib.util, pathlib
            _fb_path = pathlib.Path(__file__).parent / "soundscribe_fallback.py"
            _spec = importlib.util.spec_from_file_location("soundscribe_fallback", _fb_path)
            _mod = importlib.util.module_from_spec(_spec)
            _spec.loader.exec_module(_mod)

            # Use the original media path so SoundScribe can apply its own
            # audio extraction and duration handling consistently.
            fb_input = input_file

            _mod.transcribe_via_soundscribe(
                input_path=fb_input,
                output_dir=args.output_dir,
                language=args.language,  # pass the raw code; fallback normalises
                timeout=args.fallback_timeout,
            )

            fb_txt = os.path.join(args.output_dir, "transcript.txt")
            fb_srt = os.path.join(args.output_dir, "transcript.srt")
            if not os.path.exists(fb_txt):
                raise RuntimeError("SoundScribe fallback did not produce transcript.txt")
            if not os.path.exists(fb_srt):
                raise RuntimeError("SoundScribe fallback did not produce transcript.srt")

            media_duration = get_media_duration(input_file)
            transcript_end = parse_srt_end_time(fb_srt)
            if media_duration > 0:
                if transcript_end <= 0:
                    raise RuntimeError("SoundScribe fallback produced an SRT with no parseable end timestamp")
                ratio = transcript_end / media_duration
                print(f"Fallback completeness check: transcript ends at {transcript_end:.1f}s / media {media_duration:.1f}s ({ratio:.1%})")
                if ratio < args.min_duration_ratio:
                    raise RuntimeError(
                        f"Fallback transcript appears incomplete: end ratio {ratio:.1%} is below required {args.min_duration_ratio:.0%}."
                    )

            elapsed = time.time() - start_time
            print(
                f"\nSuccess via SoundScribe fallback! Transcribed in {elapsed:.2f}s."
                f"\n  TXT: {fb_txt}\n  SRT: {fb_srt}",
                flush=True,
            )
        except Exception as fb_exc:
            print(f"\n[FALLBACK ASR FAILED] {fb_exc}")
            traceback.print_exc()
            sys.exit(1)
    finally:
        # Clean up temporary WAV file
        if temp_wav and os.path.exists(temp_wav) and not args.keep_temp_audio:
            try:
                os.remove(temp_wav)
            except Exception:
                pass

if __name__ == "__main__":
    main()
