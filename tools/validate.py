#!/usr/bin/env python3
"""fika validation gate - run every software check the repo must keep green.

Usage:
    python3 tools/validate.py                 # everything
    python3 tools/validate.py yaml esphome    # a subset
    python3 tools/validate.py --list          # show available checks

Checks:
    yaml       yamllint over the whole repo (.yamllint.yaml rules)
    esphome    `esphome config` on the example and sim compositions
               (auto-provisions esphome/secrets.yaml from the example)
    fabtags    every cad/*.scad header declares Fabrication: cnc|print|
               cots|lib|assembly
    protocol   the entity id table in docs/PROTOCOL.md exactly matches
               the Provides ids declared by esphome/packages/*.yaml
    cups       tools/test_cup_match.py passes and the cup_tolerance_g
               substitution in packages/cup_logic.yaml equals
               cup_match.TOLERANCE_G (the lambda mirrors the python)
    temps      brew/steam/max temperature substitution defaults in the
               packages equal cad/design_params.scad (one shared value)
    sim        web UI injection keys match sim-sensors.yaml topics;
               sim/Containerfile only COPYs paths that exist
    python     scripts/*.py + tools/*.py + sim/*.py byte-compile

Intended entry points: scripts/verify_design.sh, `.claude/skills/verify`,
CI, and pre-commit. Run inside the devshell (`nix develop`) so all
binaries are present. The CAD side (params guard, renders, manifold,
layout, budgets, drift) lives in scripts/verify_design.sh.
"""

from __future__ import annotations

import py_compile
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import (  # noqa: E402
    CAD_DIR,
    ESPHOME_DIR,
    REPO_ROOT,
    SIM_DIR,
    fail,
    heading,
    ok,
    run,
    warn,
)

FAB_TAGS = ("cnc", "print", "cots", "lib", "assembly")


def check_yaml() -> bool:
    if not shutil.which("yamllint"):
        fail("yamllint not on PATH - enter the devshell: nix develop")
        return False
    proc = run(["yamllint", "--strict", "."])
    if proc.returncode != 0:
        fail("yamllint:")
        print(proc.stdout or proc.stderr)
        return False
    ok("yamllint clean")
    return True


def check_esphome() -> bool:
    esphome = shutil.which("esphome")
    if not esphome:
        fail("esphome not found - enter the devshell: nix develop")
        return False

    secrets = ESPHOME_DIR / "secrets.yaml"
    if not secrets.exists():
        shutil.copy(ESPHOME_DIR / "secrets.yaml.example", secrets)
        warn("provisioned esphome/secrets.yaml from example (placeholders)")

    good = True
    for config in ("example-fika.yaml", "sim-fika.yaml"):
        proc = run([esphome, "config", str(ESPHOME_DIR / config)], timeout=300)
        if proc.returncode != 0:
            fail(f"esphome config {config}:")
            tail = (proc.stdout + proc.stderr).splitlines()[-30:]
            print("\n".join(tail))
            good = False
        else:
            ok(f"esphome config {config}")
    return good


def check_fabtags() -> bool:
    good = True
    files = [p for p in sorted(CAD_DIR.rglob("*.scad"))
             if p.name != "design_params.scad" and "archive" not in p.parts]
    for path in files:
        header = path.read_text()[:1000]
        m = re.search(r"Fabrication:\s*(\w+)", header)
        if not m or m.group(1) not in FAB_TAGS:
            fail(f"{path.relative_to(REPO_ROOT)}: header must declare "
                 f"Fabrication: {'|'.join(FAB_TAGS)}")
            good = False
    if good:
        ok(f"{len(files)} cad files declare a fabrication tag")
    return good


def provided_ids() -> dict[str, str]:
    """Entity ids from the Provides sections of the package banners."""
    ids: dict[str, str] = {}
    for path in sorted((ESPHOME_DIR / "packages").glob("*.yaml")):
        in_provides = False
        for line in path.read_text().splitlines():
            if re.match(r"^#\s*Provides:", line):
                in_provides = True
                continue
            if in_provides:
                m = re.match(r"^#\s{3}(\w+)", line)
                if m:
                    ids[m.group(1)] = path.name
                else:
                    in_provides = False
    return ids


def check_protocol() -> bool:
    table_ids = set()
    doc = REPO_ROOT / "docs" / "PROTOCOL.md"
    for line in doc.read_text().splitlines():
        m = re.match(r"^\|\s*([a-z][a-z0-9_]*)\s*\|", line)
        if m and m.group(1) != "object_id":
            table_ids.add(m.group(1))

    pkg_ids = provided_ids()
    good = True
    missing_in_table = set(pkg_ids) - table_ids
    if missing_in_table:
        for name in sorted(missing_in_table):
            fail(f"{pkg_ids[name]} provides '{name}' but docs/PROTOCOL.md "
                 "does not list it")
        good = False
    missing_in_pkgs = table_ids - set(pkg_ids)
    if missing_in_pkgs:
        fail(f"docs/PROTOCOL.md lists ids no package provides: "
             f"{', '.join(sorted(missing_in_pkgs))}")
        good = False
    if good:
        ok(f"protocol table matches package Provides ({len(table_ids)} ids)")
    return good


def check_cups() -> bool:
    import cup_match

    proc = run([sys.executable, "-m", "unittest", "-q", "test_cup_match"],
               cwd=REPO_ROOT / "tools")
    if proc.returncode != 0:
        fail("tools/test_cup_match.py:")
        print(proc.stderr)
        return False
    ok("cup recognition unit tests pass")

    yaml_text = (ESPHOME_DIR / "packages" / "cup_logic.yaml").read_text()
    m = re.search(r'cup_tolerance_g:\s*"?([\d.]+)"?', yaml_text)
    if not m:
        fail("cup_logic.yaml: no cup_tolerance_g substitution found")
        return False
    if float(m.group(1)) != cup_match.TOLERANCE_G:
        fail(f"cup_logic.yaml cup_tolerance_g {m.group(1)} != "
             f"cup_match.TOLERANCE_G {cup_match.TOLERANCE_G} - the yaml "
             "lambda must mirror tools/cup_match.py")
        return False
    ok(f"cup_tolerance_g mirrors cup_match.TOLERANCE_G "
       f"({cup_match.TOLERANCE_G} g)")
    return True


def check_temps() -> bool:
    """The temperature setpoints span CAD and firmware: one shared value."""
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from design_params import PARAMS

    # (package file, substitution name, design param) sweep set - update
    # docs/PROTOCOL.md "keep in sync" note when this list changes
    sweep = [
        ("boiler_pid.yaml", "brew_temp_c", "brew_temp_c"),
        ("steam_mode.yaml", "brew_temp_c", "brew_temp_c"),
        ("steam_mode.yaml", "steam_temp_c", "steam_temp_c"),
        ("safety.yaml", "max_temp_c", "max_temp_c"),
    ]
    good = True
    for fname, sub, param in sweep:
        text = (ESPHOME_DIR / "packages" / fname).read_text()
        m = re.search(rf'^\s+{sub}:\s*"?([\d.]+)"?', text, re.M)
        if not m:
            fail(f"{fname}: substitution {sub} not found")
            good = False
        elif float(m.group(1)) != float(PARAMS[param]):
            fail(f"{fname} {sub} = {m.group(1)} but design_params.scad "
                 f"{param} = {PARAMS[param]} - change both together")
            good = False
    if good:
        ok(f"{len(sweep)} temperature substitutions match design_params.scad")
    return good


def check_sim() -> bool:
    """Cross-artifact contract: web UI <-> sim-sensors.yaml <-> Containerfile."""
    import importlib.util

    good = True
    spec = importlib.util.spec_from_file_location(
        "fika_sim_webui", SIM_DIR / "webui.py")
    webui = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(webui)
    ui_keys = set(webui.INJECTIONS)

    sensors_yaml = (ESPHOME_DIR / "packages" / "sim-sensors.yaml").read_text()
    fw_keys = set(re.findall(
        r"topic:\s*\$\{mqtt_root\}/\$\{node_name\}/sim/(\S+)", sensors_yaml))
    if ui_keys != fw_keys:
        fail(f"sim injection keys drifted: webui={sorted(ui_keys)} "
             f"firmware={sorted(fw_keys)}")
        good = False
    else:
        ok(f"web UI injection keys match sim-sensors.yaml ({len(ui_keys)})")

    bad_presets = {
        name for name, preset in webui.PRESETS.items()
        if set(preset) - ui_keys
    }
    if bad_presets:
        fail(f"web UI presets use unknown keys: {sorted(bad_presets)}")
        good = False
    else:
        ok(f"web UI presets reference valid keys ({len(webui.PRESETS)})")

    containerfile = (SIM_DIR / "Containerfile").read_text()
    for line in containerfile.splitlines():
        if line.startswith("COPY ") and "--from=" not in line:
            for src in line.split()[1:-1]:
                if not (REPO_ROOT / src.rstrip("/")).exists():
                    fail(f"Containerfile COPYs missing path: {src}")
                    good = False
    if good:
        ok("Containerfile COPY sources exist")
    return good


def check_python() -> bool:
    good = True
    files = (sorted((REPO_ROOT / "scripts").glob("*.py"))
             + sorted((REPO_ROOT / "tools").glob("*.py"))
             + sorted(SIM_DIR.glob("*.py")))
    for path in files:
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as err:
            fail(f"{path.relative_to(REPO_ROOT)}: {err}")
            good = False
    if good:
        ok(f"{len(files)} python files byte-compile (scripts/ tools/ sim/)")
    return good


CHECKS = {
    "yaml": check_yaml,
    "esphome": check_esphome,
    "fabtags": check_fabtags,
    "protocol": check_protocol,
    "cups": check_cups,
    "temps": check_temps,
    "sim": check_sim,
    "python": check_python,
}


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if "--list" in sys.argv:
        print("\n".join(CHECKS))
        return 0
    selected = args or list(CHECKS)
    unknown = set(selected) - set(CHECKS)
    if unknown:
        fail(f"unknown checks: {', '.join(sorted(unknown))} (see --list)")
        return 2

    results: dict[str, bool] = {}
    for name in selected:
        heading(name)
        results[name] = CHECKS[name]()

    heading("summary")
    for name, passed in results.items():
        (ok if passed else fail)(name)
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
