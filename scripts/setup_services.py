#!/usr/bin/env python3
"""
Cross-Platform Background Service Installer
=============================================
Registers background daemons for the lecture-notes pipeline:
  1. ASR Watcher  – 24/7 transcription daemon
  2. Downloads Tracker – scheduled pipeline orchestrator (every 20 min, 7 AM–1 PM)
  3. Web UI – FastAPI dashboard (optional)

Supported platforms:
  - macOS:   ~/Library/LaunchAgents/*.plist
  - Windows: Task Scheduler via schtasks.exe / PowerShell
  - Linux:   ~/.config/systemd/user/*.service

Usage:
  python scripts/setup_services.py install     # install all services
  python scripts/setup_services.py install --service asr_watcher
  python scripts/setup_services.py uninstall   # remove all services
  python scripts/setup_services.py status       # show service status
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

# ── Constants ─────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
LOGS_DIR = PROJECT_ROOT / "logs"

# Detect venv python
if sys.platform == "win32":
    VENV_PYTHON = PROJECT_ROOT / "venv" / "Scripts" / "python.exe"
else:
    VENV_PYTHON = PROJECT_ROOT / "venv" / "bin" / "python"

if not VENV_PYTHON.exists():
    # Fallback to current interpreter
    VENV_PYTHON = Path(sys.executable)


SERVICE_DEFS = {
    "asr_watcher": {
        "label": "com.tejasmahadik.asr-watcher",
        "description": "24/7 ASR Transcription Watcher Daemon",
        "script": SCRIPTS_DIR / "asr_watcher.py",
        "args": [],
        "keep_alive": True,   # long-running daemon
        "schedule": None,     # runs continuously
        "win_task_name": "LectureNotes_ASR_Watcher",
    },
    "downloads_tracker": {
        "label": "com.tejasmahadik.downloads-tracker",
        "description": "Downloads Tracker Pipeline Scheduler",
        "script": SCRIPTS_DIR / "downloads_tracker.py",
        "args": ["--force"],
        "keep_alive": False,
        "schedule": {"minute": "*/20", "hour": "7-13"},
        "win_task_name": "LectureNotes_Downloads_Tracker",
    },
    "web_ui": {
        "label": "com.tejasmahadik.asr-webui",
        "description": "Lecture Notes Web Dashboard",
        "script": SCRIPTS_DIR / ".." / "web_ui" / "app.py",
        "args": [],
        "keep_alive": True,
        "schedule": None,
        "win_task_name": "LectureNotes_WebUI",
        "run_cmd": [str(VENV_PYTHON), "-m", "uvicorn", "web_ui.app:app", "--host", "0.0.0.0", "--port", "8000"],
    },
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def ensure_logs_dir():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def get_env_path():
    """Return the .env file as a dict for injection into services."""
    env_file = PROJECT_ROOT / ".env"
    env = {}
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def print_ok(msg):
    print(f"  ✅ {msg}")


def print_warn(msg):
    print(f"  ⚠️  {msg}")


def print_err(msg):
    print(f"  ❌ {msg}")


# ══════════════════════════════════════════════════════════════════════════════
#  macOS – LaunchAgents
# ══════════════════════════════════════════════════════════════════════════════

def _macos_plist_path(label: str) -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{label}.plist"


def _macos_build_plist(name: str, sdef: dict) -> str:
    python = str(VENV_PYTHON)
    script = str(Path(sdef["script"]).resolve())
    working_dir = str(PROJECT_ROOT)
    label = sdef["label"]

    # Build ProgramArguments
    if "run_cmd" in sdef:
        prog_items = "\n".join(f"        <string>{a}</string>" for a in sdef["run_cmd"])
    else:
        items = [python, script] + sdef["args"]
        prog_items = "\n".join(f"        <string>{a}</string>" for a in items)

    # KeepAlive or StartCalendarInterval
    if sdef["keep_alive"]:
        run_policy = """    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>ThrottleInterval</key>
    <integer>10</integer>"""
    elif sdef["schedule"]:
        s = sdef["schedule"]
        run_policy = f"""    <key>StartCalendarInterval</key>
    <dict>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>StartInterval</key>
    <integer>1200</integer>"""
    else:
        run_policy = """    <key>RunAtLoad</key>
    <true/>"""

    stdout_log = str(Path.home() / "Library" / "Logs" / f"{name}_stdout.log")
    stderr_log = str(Path.home() / "Library" / "Logs" / f"{name}_stderr.log")

    return textwrap.dedent(f"""\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{label}</string>

    <key>ProgramArguments</key>
    <array>
{prog_items}
    </array>

    <key>WorkingDirectory</key>
    <string>{working_dir}</string>

{run_policy}

    <key>StandardOutPath</key>
    <string>{stdout_log}</string>

    <key>StandardErrorPath</key>
    <string>{stderr_log}</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    </dict>

    <key>ProcessType</key>
    <string>Background</string>
</dict>
</plist>
""")


def macos_install(name: str, sdef: dict):
    plist_path = _macos_plist_path(sdef["label"])
    plist_path.parent.mkdir(parents=True, exist_ok=True)

    # Unload if already loaded
    subprocess.run(
        ["launchctl", "unload", str(plist_path)],
        capture_output=True, check=False
    )

    plist_content = _macos_build_plist(name, sdef)
    plist_path.write_text(plist_content, encoding="utf-8")

    result = subprocess.run(
        ["launchctl", "load", str(plist_path)],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print_ok(f"Installed & loaded: {sdef['label']}")
    else:
        print_err(f"Failed to load {sdef['label']}: {result.stderr.strip()}")


def macos_uninstall(name: str, sdef: dict):
    plist_path = _macos_plist_path(sdef["label"])
    if plist_path.exists():
        subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True, check=False)
        plist_path.unlink()
        print_ok(f"Uninstalled: {sdef['label']}")
    else:
        print_warn(f"Not installed: {sdef['label']}")


def macos_status(name: str, sdef: dict):
    result = subprocess.run(
        ["launchctl", "list"],
        capture_output=True, text=True
    )
    label = sdef["label"]
    for line in result.stdout.splitlines():
        if label in line:
            parts = line.split()
            pid = parts[0] if parts[0] != "-" else "not running"
            status = parts[1]
            print(f"  📋 {label}: PID={pid}, LastExitStatus={status}")
            return
    print(f"  ⏸️  {label}: not loaded")


# ══════════════════════════════════════════════════════════════════════════════
#  Windows – Task Scheduler
# ══════════════════════════════════════════════════════════════════════════════

def windows_install(name: str, sdef: dict):
    task_name = sdef["win_task_name"]
    python = str(VENV_PYTHON)

    if "run_cmd" in sdef:
        program = sdef["run_cmd"][0]
        arguments = " ".join(sdef["run_cmd"][1:])
    else:
        script = str(Path(sdef["script"]).resolve())
        program = python
        arguments = f'"{script}" ' + " ".join(sdef["args"])

    # Delete existing task if present
    subprocess.run(
        ["schtasks", "/Delete", "/TN", task_name, "/F"],
        capture_output=True, check=False
    )

    if sdef["schedule"]:
        # Scheduled task (every 20 min between 7 AM and 1 PM)
        s = sdef["schedule"]
        cmd = [
            "schtasks", "/Create",
            "/TN", task_name,
            "/TR", f'"{program}" {arguments}',
            "/SC", "MINUTE",
            "/MO", "20",
            "/ST", "07:00",
            "/ET", "13:00",
            "/F",
        ]
    elif sdef["keep_alive"]:
        # Long-running daemon: start at logon
        cmd = [
            "schtasks", "/Create",
            "/TN", task_name,
            "/TR", f'"{program}" {arguments}',
            "/SC", "ONLOGON",
            "/F",
        ]
    else:
        cmd = [
            "schtasks", "/Create",
            "/TN", task_name,
            "/TR", f'"{program}" {arguments}',
            "/SC", "ONLOGON",
            "/F",
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print_ok(f"Scheduled task created: {task_name}")
        # Start it now for keep_alive daemons
        if sdef["keep_alive"]:
            subprocess.run(
                ["schtasks", "/Run", "/TN", task_name],
                capture_output=True, check=False
            )
            print_ok(f"Started: {task_name}")
    else:
        print_err(f"Failed to create task {task_name}: {result.stderr.strip()}")


def windows_uninstall(name: str, sdef: dict):
    task_name = sdef["win_task_name"]
    # End the task first
    subprocess.run(
        ["schtasks", "/End", "/TN", task_name],
        capture_output=True, check=False
    )
    result = subprocess.run(
        ["schtasks", "/Delete", "/TN", task_name, "/F"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print_ok(f"Removed task: {task_name}")
    else:
        print_warn(f"Task not found or error: {task_name}")


def windows_status(name: str, sdef: dict):
    task_name = sdef["win_task_name"]
    result = subprocess.run(
        ["schtasks", "/Query", "/TN", task_name, "/FO", "LIST"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            if "Status" in line or "Next Run" in line or "Last Run" in line:
                print(f"  📋 {line.strip()}")
    else:
        print(f"  ⏸️  {task_name}: not registered")


# ══════════════════════════════════════════════════════════════════════════════
#  Linux – systemd user units
# ══════════════════════════════════════════════════════════════════════════════

def _systemd_unit_path(name: str) -> Path:
    return Path.home() / ".config" / "systemd" / "user" / f"lecturenotes-{name}.service"


def _systemd_timer_path(name: str) -> Path:
    return Path.home() / ".config" / "systemd" / "user" / f"lecturenotes-{name}.timer"


def linux_install(name: str, sdef: dict):
    unit_dir = Path.home() / ".config" / "systemd" / "user"
    unit_dir.mkdir(parents=True, exist_ok=True)

    python = str(VENV_PYTHON)
    working_dir = str(PROJECT_ROOT)
    unit_name = f"lecturenotes-{name}"

    if "run_cmd" in sdef:
        exec_start = " ".join(sdef["run_cmd"])
    else:
        script = str(Path(sdef["script"]).resolve())
        args = " ".join(sdef["args"])
        exec_start = f"{python} {script} {args}".strip()

    # Load .env vars
    env_vars = get_env_path()
    env_lines = "\n".join(f"Environment={k}={v}" for k, v in env_vars.items()) if env_vars else ""

    if sdef["keep_alive"]:
        restart_policy = "Restart=always\nRestartSec=10"
    else:
        restart_policy = "Type=oneshot"

    service_content = textwrap.dedent(f"""\
[Unit]
Description={sdef['description']}
After=network.target

[Service]
WorkingDirectory={working_dir}
ExecStart={exec_start}
{restart_policy}
{env_lines}

[Install]
WantedBy=default.target
""")

    unit_path = _systemd_unit_path(name)
    unit_path.write_text(service_content, encoding="utf-8")

    # If scheduled, create a timer unit
    if sdef["schedule"] and not sdef["keep_alive"]:
        timer_content = textwrap.dedent(f"""\
[Unit]
Description=Timer for {sdef['description']}

[Timer]
OnCalendar=*-*-* 07..13:00/20:00
Persistent=true

[Install]
WantedBy=timers.target
""")
        timer_path = _systemd_timer_path(name)
        timer_path.write_text(timer_content, encoding="utf-8")

    subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True, check=False)

    if sdef["schedule"] and not sdef["keep_alive"]:
        subprocess.run(["systemctl", "--user", "enable", "--now", f"{unit_name}.timer"], capture_output=True, check=False)
        print_ok(f"Installed & enabled timer: {unit_name}.timer")
    else:
        subprocess.run(["systemctl", "--user", "enable", "--now", f"{unit_name}.service"], capture_output=True, check=False)
        print_ok(f"Installed & started: {unit_name}.service")


def linux_uninstall(name: str, sdef: dict):
    unit_name = f"lecturenotes-{name}"
    subprocess.run(["systemctl", "--user", "stop", f"{unit_name}.service"], capture_output=True, check=False)
    subprocess.run(["systemctl", "--user", "disable", f"{unit_name}.service"], capture_output=True, check=False)
    subprocess.run(["systemctl", "--user", "stop", f"{unit_name}.timer"], capture_output=True, check=False)
    subprocess.run(["systemctl", "--user", "disable", f"{unit_name}.timer"], capture_output=True, check=False)

    for p in [_systemd_unit_path(name), _systemd_timer_path(name)]:
        if p.exists():
            p.unlink()

    subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True, check=False)
    print_ok(f"Uninstalled: {unit_name}")


def linux_status(name: str, sdef: dict):
    unit_name = f"lecturenotes-{name}"
    result = subprocess.run(
        ["systemctl", "--user", "status", f"{unit_name}.service", "--no-pager"],
        capture_output=True, text=True
    )
    if result.returncode <= 3:
        for line in result.stdout.splitlines()[:5]:
            print(f"  📋 {line.strip()}")
    else:
        print(f"  ⏸️  {unit_name}: not installed")


# ══════════════════════════════════════════════════════════════════════════════
#  Dispatcher
# ══════════════════════════════════════════════════════════════════════════════

def get_platform_funcs():
    system = platform.system()
    if system == "Darwin":
        return macos_install, macos_uninstall, macos_status
    elif system == "Windows":
        return windows_install, windows_uninstall, windows_status
    elif system == "Linux":
        return linux_install, linux_uninstall, linux_status
    else:
        print_err(f"Unsupported platform: {system}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Cross-platform background service installer for Lecture Notes pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python scripts/setup_services.py install
              python scripts/setup_services.py install --service asr_watcher
              python scripts/setup_services.py uninstall
              python scripts/setup_services.py status
        """)
    )
    parser.add_argument("action", choices=["install", "uninstall", "status"],
                        help="Action to perform")
    parser.add_argument("--service", choices=list(SERVICE_DEFS.keys()),
                        help="Target a specific service (default: all)")
    args = parser.parse_args()

    ensure_logs_dir()
    install_fn, uninstall_fn, status_fn = get_platform_funcs()

    services = {args.service: SERVICE_DEFS[args.service]} if args.service else SERVICE_DEFS

    system = platform.system()
    print(f"\n🖥️  Platform: {system}")
    print(f"📂 Project:  {PROJECT_ROOT}")
    print(f"🐍 Python:   {VENV_PYTHON}\n")

    for name, sdef in services.items():
        print(f"{'─'*50}")
        print(f"  🔧 {sdef['description']} ({name})")
        if args.action == "install":
            install_fn(name, sdef)
        elif args.action == "uninstall":
            uninstall_fn(name, sdef)
        elif args.action == "status":
            status_fn(name, sdef)

    print(f"{'─'*50}")
    print(f"\n✨ Done.\n")


if __name__ == "__main__":
    main()
