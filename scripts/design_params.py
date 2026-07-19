#!/usr/bin/env python3
"""Python-side access to cad/design_params.scad - the single source of truth.

OpenSCAD consumes the file directly (every part includes it); Python tools
import this module, which parses the same file, so CAD, layout checks and
budgets can never drift apart. Values: numbers, booleans, and flat vectors.

Override precedence (highest first):
  1. environment variable, FIKA_ + UPPERCASE of the name (FIKA_BOILER_OD=110)
  2. the value in cad/design_params.scad

OpenSCAD gets the same overrides via -D flags: scad_overrides() returns the
-D arguments for every env-overridden name, and scripts/regen_all.py plus
scripts/verify_design.sh forward them, so one env var flips the whole
pipeline at once.

Usage:
    from design_params import PARAMS, scad_overrides
    od = PARAMS["boiler_od"]
"""

import os
import re
from pathlib import Path

_SCAD = Path(__file__).resolve().parent.parent / "cad" / "design_params.scad"

ENV_PREFIX = "FIKA_"


def _parse(text):
    s = text.strip()
    if s.lower() in ("true", "false"):
        return s.lower() == "true"
    if s.startswith("[") and s.endswith("]"):
        return [_parse(part) for part in s[1:-1].split(",")]
    return float(s) if "." in s else int(s)


def load():
    params = {}
    for m in re.finditer(r"(?m)^\s*(\w+)\s*=\s*([^;]+?)\s*;", _SCAD.read_text()):
        try:
            params[m.group(1)] = _parse(m.group(2))
        except ValueError:
            raise ValueError(
                f"design_params.scad: unsupported value {m.group(2)!r} for "
                f"{m.group(1)!r} - keep the file to numbers/booleans/vectors")
    for name in params:
        env = os.environ.get(ENV_PREFIX + name.upper())
        if env is not None:
            params[name] = _parse(env)
    return params


def overridden():
    """Names whose value comes from the environment, with parsed values."""
    return {
        name: value for name, value in PARAMS.items()
        if os.environ.get(ENV_PREFIX + name.upper()) is not None
    }


def scad_overrides():
    """-D arguments forwarding env overrides to OpenSCAD (-D beats include)."""
    args = []
    for name, value in overridden().items():
        if isinstance(value, bool):
            rendered = "true" if value else "false"
        else:
            rendered = str(value)
        args += ["-D", f"{name}={rendered}"]
    return args


PARAMS = load()

if __name__ == "__main__":
    marks = overridden()
    for k, v in PARAMS.items():
        note = "  (env override)" if k in marks else ""
        print(f"{k} = {v}{note}")
