#!/usr/bin/env python3
"""fika validation gate - run every software check the repo must keep green.

Usage:
    python3 tools/validate.py                 # everything
    python3 tools/validate.py yaml esphome    # a subset
    python3 tools/validate.py --list          # show available checks

Checks (framework and generic checks: esphome_skills; fika-local checks
couple firmware to CAD and stay in this file):
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
    sim        project injection keys match sim-sensors.yaml topics; the
               sim container staging sources exist
    python     scripts/*.py + tools/*.py byte-compile

Intended entry points: scripts/verify_design.sh, `.claude/skills/verify`,
CI, and pre-commit. Run inside the devshell (`nix develop`) so all
binaries are present. The CAD side (params guard, renders, manifold,
layout, budgets, drift) lives in scripts/verify_design.sh.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from project import PROJECT  # noqa: E402

from esphome_skills import checks, validate  # noqa: E402
from esphome_skills.lib import fail, ok, run  # noqa: E402

REPO_ROOT = PROJECT.repo_root
CAD_DIR = REPO_ROOT / "cad"
ESPHOME_DIR = PROJECT.esphome_dir

FAB_TAGS = ("cnc", "print", "cots", "lib", "assembly")


def check_fabtags(project) -> bool:
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


def check_protocol(project) -> bool:
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


def check_cups(project) -> bool:
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


def check_temps(project) -> bool:
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


CHECKS = {
    "yaml": checks.check_yaml,
    "esphome": checks.check_esphome,
    "fabtags": check_fabtags,
    "protocol": check_protocol,
    "cups": check_cups,
    "temps": check_temps,
    "sim": checks.check_sim,
    "python": checks.check_python,
}

if __name__ == "__main__":
    sys.exit(validate.main(PROJECT, CHECKS))
