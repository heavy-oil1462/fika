#!/usr/bin/env python3
"""fika simulation integration test: the REAL firmware, no hardware.

Compiles esphome/sim-fika.yaml (actual esp32 build), boots it under
Espressif QEMU against a throwaway authenticated mosquitto, drives it
through sim/webui.py's HTTP API exactly like a person at the control panel,
and asserts that the on-device behavior holds:

    1. node comes up: retained status "online" + MQTT discovery
    2. injected sensor values surface under the real sensor ids
       (boiler_temp, cup_weight)
    3. moving the boiler_temp slider moves the boiler_temp state topic
    4. a 210 g cup on the scale changes the detected_cup text sensor
    5. brew/steam panel injections surface as the brew_switch/steam_switch
       binary sensors

Deliberately basic: it proves the injection -> firmware -> state-topic loop
end to end. Rule-level assertions (PID heater duty, gravimetric stop) can
grow here once those packages settle.

Needs: esphome able to *compile* (pip install esphome if the nix platformio
wrapper can't sandbox), qemu-system-xtensa with the esp32 machine (in the
devshell / QEMU_ESP32 env), mosquitto + mosquitto_passwd, paho-mqtt, and the
ability to bind udp/123 (root or CAP_NET_BIND_SERVICE) so the firmware's
SNTP can reach the simulated clock; port 123 is fixed in lwIP.

    sudo -E nix develop -c python3 tools/test_sim.py

Slow: one esp32 compile (cached in .esphome-sim/) plus a few minutes of
emulated boot and control-loop time. Not part of the default validation
gate.
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _lib import REPO_ROOT, fail, heading, mqtt_client, ok, require, warn  # noqa: E402,F401
from sim import _build  # noqa: E402

NODE = "sim-fika"
ROOT = "fika"
PREFIX = f"{ROOT}/{NODE}"
USER, PASSWORD = "sim", "simpass"
BROKER_PORT = 1883  # fixed: baked into the compiled firmware (10.0.2.2:1883)
NTP_PORT = 123      # fixed: lwIP SNTP always queries udp/123
WORKDIR = REPO_ROOT / ".esphome-sim"


def find_esphome() -> str:
    for candidate in (os.environ.get("ESPHOME_BIN"),
                      str(REPO_ROOT / ".venv" / "bin" / "esphome"),
                      shutil.which("esphome")):
        if candidate and Path(candidate).exists():
            return candidate
    fail("no esphome binary found (ESPHOME_BIN / .venv / PATH)")
    sys.exit(2)


def find_qemu() -> str:
    candidate = os.environ.get("QEMU_ESP32") or shutil.which(
        "qemu-system-xtensa")
    if not candidate:
        fail("qemu-system-xtensa not found; enter the devshell "
             "(nix develop) or set QEMU_ESP32=/path/to/qemu-system-xtensa")
        sys.exit(2)
    return candidate


def port_bindable(port: int, udp: bool = False) -> bool:
    kind = socket.SOCK_DGRAM if udp else socket.SOCK_STREAM
    try:
        with socket.socket(socket.AF_INET, kind) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("0.0.0.0" if udp else "127.0.0.1", port))
        return True
    except OSError:
        return False


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def api(http_port: int, path: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(
        f"http://127.0.0.1:{http_port}{path}",
        data=json.dumps(body).encode() if body is not None else None,
        method="POST" if body is not None else "GET")
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read())


def inject(http_port: int, **values: float) -> None:
    for key, value in values.items():
        api(http_port, "/api/inject", {"key": key, "value": value})


class Collector:
    """MQTT test client collecting every message with its retain flag."""

    def __init__(self, port: int):
        self.messages: dict[str, tuple[str, bool]] = {}
        self.client = mqtt_client("simtest-watcher", USER, PASSWORD)
        self.client.on_message = self._on_message
        self.client.connect("127.0.0.1", port, keepalive=30)
        self.client.subscribe([(f"{ROOT}/#", 0), ("homeassistant/#", 0)])
        self.client.loop_start()

    def _on_message(self, _client, _userdata, msg) -> None:
        self.messages[msg.topic] = (msg.payload.decode(), bool(msg.retain))

    def wait_for(self, topic: str, predicate=lambda _v: True,
                 timeout: float = 30.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if topic in self.messages and predicate(self.messages[topic][0]):
                return self.messages[topic]
            time.sleep(0.2)
        return None

    def wait_any(self, topic_predicate, timeout: float = 30.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            for topic in list(self.messages):
                if topic_predicate(topic):
                    return topic
            time.sleep(0.2)
        return None

    def stop(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()


def main() -> int:
    require("mosquitto")
    require("mosquitto_passwd")
    esphome_bin = find_esphome()
    qemu_bin = find_qemu()

    if not port_bindable(BROKER_PORT):
        fail(f"tcp/{BROKER_PORT} is in use; the firmware is compiled for "
             "10.0.2.2:1883, stop whatever is listening there")
        return 2
    if not port_bindable(NTP_PORT, udp=True):
        fail(f"cannot bind udp/{NTP_PORT} (needs root or "
             "CAP_NET_BIND_SERVICE); required for simulated firmware time")
        return 2

    failures = 0

    def check(condition: bool, label: str) -> None:
        nonlocal failures
        if condition:
            ok(label)
        else:
            fail(label)
            failures += 1

    heading("compiling the real firmware (cached in .esphome-sim/)")
    _build.sync_config(REPO_ROOT / "esphome", WORKDIR / "config")
    _build.write_secrets(WORKDIR / "config", "10.0.2.2", USER, PASSWORD)
    try:
        factory = _build.compile_firmware(WORKDIR / "config", NODE,
                                          esphome_bin=esphome_bin)
        flash = _build.make_flash_image(factory, WORKDIR / "flash.bin")
    except RuntimeError as err:
        fail(str(err))
        return 1
    ok(f"flash image ready: {flash}")

    http_port = free_port()
    with tempfile.TemporaryDirectory(prefix="fika-simtest-") as tmp:
        tmp_path = Path(tmp)
        passwd = tmp_path / "passwd"
        passwd.touch()
        os.chmod(passwd, 0o700)
        subprocess.run(["mosquitto_passwd", "-b", str(passwd), USER, PASSWORD],
                       check=True, capture_output=True)
        conf = tmp_path / "mosquitto.conf"
        conf.write_text(
            f"listener {BROKER_PORT}\n"
            "allow_anonymous false\n"
            f"password_file {passwd}\n"
            "persistence false\n"
            + ("user root\n" if os.geteuid() == 0 else ""))

        heading("starting broker + web UI + QEMU")
        broker = subprocess.Popen(["mosquitto", "-c", str(conf)],
                                  stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL)
        webui_log = (tmp_path / "webui.log").open("w")
        qemu_log = (tmp_path / "qemu.log").open("w")
        webui = qemu = None
        watcher = None
        try:
            time.sleep(0.5)
            check(broker.poll() is None,
                  f"mosquitto up on 127.0.0.1:{BROKER_PORT}")

            webui = subprocess.Popen(
                [sys.executable, str(REPO_ROOT / "sim" / "webui.py"),
                 "--broker", "127.0.0.1", "--port", str(BROKER_PORT),
                 "--username", USER, "--password", PASSWORD,
                 "--node", NODE, "--root", ROOT,
                 "--http-port", str(http_port), "--ntp-port", str(NTP_PORT)],
                stdout=webui_log, stderr=subprocess.STDOUT)
            deadline = time.time() + 15
            ui_up = False
            while time.time() < deadline and not ui_up:
                try:
                    api(http_port, "/api/state")
                    ui_up = True
                except OSError:
                    time.sleep(0.5)
            check(ui_up, f"web UI answering on 127.0.0.1:{http_port}")

            watcher = Collector(BROKER_PORT)
            # Retained injections land the moment the firmware connects:
            # cold machine, empty tray, switches off.
            inject(http_port, boiler_temp=25, cup_weight=0,
                   brew_switch=0, steam_switch=0)

            qemu = subprocess.Popen(_build.qemu_cmd(qemu_bin, flash),
                                    stdout=qemu_log, stderr=subprocess.STDOUT,
                                    stdin=subprocess.DEVNULL)

            heading("1. boot: availability + discovery")
            status = watcher.wait_for(f"{PREFIX}/status",
                                      lambda v: v == "online", timeout=150)
            check(status is not None, "firmware connected: status 'online'")
            disco = watcher.wait_any(
                lambda t: t.startswith("homeassistant/")
                and f"/{NODE}/" in t and t.endswith("/config"))
            check(disco is not None, f"MQTT discovery published ({disco})")

            heading("2. injected sensors surface under real ids")
            boiler = watcher.wait_for(f"{PREFIX}/sensor/boiler_temp/state",
                                      lambda v: v and abs(float(v) - 25) < 1,
                                      timeout=90)
            check(boiler is not None, "boiler_temp injection 25 C -> boiler_temp")
            cup = watcher.wait_for(f"{PREFIX}/sensor/cup_weight/state",
                                   lambda v: v and abs(float(v)) < 1,
                                   timeout=90)
            check(cup is not None, "cup_weight injection 0 g -> cup_weight")

            heading("3. boiler_temp tracks the slider")
            inject(http_port, boiler_temp=93)
            boiler = watcher.wait_for(f"{PREFIX}/sensor/boiler_temp/state",
                                      lambda v: v and abs(float(v) - 93) < 1,
                                      timeout=120)
            check(boiler is not None, "boiler_temp state follows to 93 C")

            heading("4. cup recognition: 210 g on the scale")
            cup_topic = f"{PREFIX}/text_sensor/detected_cup/state"
            base = watcher.wait_for(cup_topic, timeout=90)
            check(base is not None, "detected_cup published a baseline state")
            baseline = base[0] if base else None
            inject(http_port, cup_weight=210)
            cup = watcher.wait_for(f"{PREFIX}/sensor/cup_weight/state",
                                   lambda v: v and abs(float(v) - 210) < 1,
                                   timeout=120)
            check(cup is not None, "cup_weight state follows to 210 g")
            detected = watcher.wait_for(
                cup_topic, lambda v: v and v != baseline, timeout=180)
            check(detected is not None,
                  f"detected_cup changed from {baseline!r} "
                  f"(now {watcher.messages.get(cup_topic, ('?',))[0]!r})")

            heading("5. panel switches surface as binary sensors")
            inject(http_port, brew_switch=1)
            brew = watcher.wait_for(f"{PREFIX}/binary_sensor/brew_switch/state",
                                    lambda v: v == "ON", timeout=90)
            check(brew is not None, "brew_switch 1 -> binary_sensor ON")
            inject(http_port, steam_switch=1)
            steam = watcher.wait_for(
                f"{PREFIX}/binary_sensor/steam_switch/state",
                lambda v: v == "ON", timeout=90)
            check(steam is not None, "steam_switch 1 -> binary_sensor ON")
            inject(http_port, brew_switch=0, steam_switch=0)
            brew = watcher.wait_for(f"{PREFIX}/binary_sensor/brew_switch/state",
                                    lambda v: v == "OFF", timeout=90)
            check(brew is not None, "brew_switch 0 -> binary_sensor OFF")

            if failures:
                print("\n[topics seen]")
                for topic in sorted(watcher.messages):
                    print(f"  {topic} = {watcher.messages[topic][0]!r}")
                print("\n[qemu log tail]")
                print("\n".join(
                    (tmp_path / "qemu.log").read_text().splitlines()[-80:]))
                print("\n[webui log]")
                print((tmp_path / "webui.log").read_text())
        finally:
            if watcher:
                watcher.stop()
            for proc in (qemu, webui, broker):
                if proc and proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        proc.kill()
            webui_log.close()
            qemu_log.close()

    heading("summary")
    (ok if failures == 0 else fail)(f"sim test: {failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
