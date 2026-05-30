#!/usr/bin/env python3
"""
Auto-crop all frames in screenshots/ directory.
Removes black bars, uniform borders, and irrelevant desktop area
by detecting the content bounding box.
"""
import os
import sys

try:
    from PIL import Image, ImageChops
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow", file=sys.stderr)
    sys.exit(1)


def crop_content(img_path, padding=5):
    """Crop an image to its content bounding box with optional padding."""
    im = Image.open(img_path).convert('RGB')
    # Sample the corner pixel as the assumed background colour
    bg = Image.new('RGB', im.size, im.getpixel((0, 0)))
    diff = ImageChops.difference(im, bg)
    # Convert to greyscale and apply a small threshold to ignore compression artefacts
    grey = diff.convert('L')
    bbox = grey.point(lambda x: 0 if x < 15 else 255).getbbox()
    if bbox:
        # Add padding while staying within image bounds
        x0 = max(0, bbox[0] - padding)
        y0 = max(0, bbox[1] - padding)
        x1 = min(im.width, bbox[2] + padding)
        y1 = min(im.height, bbox[3] + padding)
        cropped = im.crop((x0, y0, x1, y1))
        cropped.save(img_path)
        return True
    return False


def main():
    screenshots_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'screenshots')
    if not os.path.isdir(screenshots_dir):
        print(f"No screenshots/ directory found at {screenshots_dir}. Nothing to crop.")
        return

    files = sorted(f for f in os.listdir(screenshots_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png')))
    if not files:
        print("No image files found in screenshots/.")
        return

    print(f"Cropping {len(files)} frame(s) in {screenshots_dir}...")
    for fname in files:
        path = os.path.join(screenshots_dir, fname)
        if crop_content(path):
            print(f"  ✓ Cropped: {fname}")
        else:
            print(f"  – Skipped (no distinct content bbox): {fname}")

    print("Done.")


if __name__ == '__main__':
    main()
