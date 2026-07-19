"""Shared helpers for the fika tools. Not a public API."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CAD_DIR = REPO_ROOT / "cad"
ESPHOME_DIR = REPO_ROOT / "esphome"
OUTPUTS_DIR = REPO_ROOT / "outputs"
SIM_DIR = REPO_ROOT / "sim"

GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
BOLD = "\033[1m"
RESET = "\033[0m"


def ok(msg: str) -> None:
    print(f"{GREEN}✔{RESET} {msg}")


def fail(msg: str) -> None:
    print(f"{RED}✘{RESET} {msg}")


def warn(msg: str) -> None:
    print(f"{YELLOW}⚠{RESET} {msg}")


def heading(msg: str) -> None:
    print(f"\n{BOLD}── {msg} {'─' * max(0, 60 - len(msg))}{RESET}")


def run(
    cmd: list[str],
    cwd: Path | None = None,
    env: dict | None = None,
    timeout: int = 600,
) -> subprocess.CompletedProcess:
    """Run a command, capturing output."""
    merged_env = {**os.environ, **(env or {})}
    return subprocess.run(
        cmd,
        cwd=str(cwd or REPO_ROOT),
        env=merged_env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def require(binary: str, hint: str = "enter the devshell: nix develop") -> str:
    """Resolve a binary on PATH or exit with a hint."""
    path = shutil.which(binary)
    if not path:
        fail(f"'{binary}' not found on PATH - {hint}")
        sys.exit(2)
    return path


def mqtt_client(client_id: str, username: str | None = None,
                password: str | None = None):
    """Create a paho-mqtt client, compatible with paho 1.x and 2.x."""
    import paho.mqtt.client as mqtt

    try:
        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id,
        )
    except (AttributeError, TypeError):  # paho 1.x
        client = mqtt.Client(client_id=client_id)
    if username:
        client.username_pw_set(username, password)
    return client
