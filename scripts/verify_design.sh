#!/usr/bin/env bash
# Design verification - read-only, writes NOTHING into the repo.
# Run before every commit:
#
#     scripts/verify_design.sh
#
# Checks, in order:
#   1. python byte-compile via tools/validate.py python
#   2. params guard (scripts/check_params.py: no shadowed dimensions)
#   3. software gate (tools/validate.py: yamllint, esphome config,
#      fabrication tags, protocol table, cup logic, sim contract)
#   4. full regeneration into a temp dir - any OpenSCAD error or WARNING
#      fails (covers CAD compile health for every part and profile)
#   5. STL watertight + shell count per the manifest (scripts/check_stl.py)
#   6. layout clearances (scripts/check_layout.py)
#   7. budget assertions (tools/energy_budget.py --check, no [!] flags)
#   8. drift: the temp regeneration must byte-match committed outputs/
#      (if it does not, run scripts/regen_all.py and commit the result).
#      Bytes are only comparable between identical OpenSCAD builds, so
#      this step self-skips with a notice when the resolved version
#      differs from outputs/openscad_version.txt; steps 4-7 still fully
#      exercise the local toolchain.
#
# Nix is optional: steps 1-3 need esphome, yamllint and the
# esphome_skills package, from either the devshell (nix develop) or a
# plain pip install -r requirements.txt.
# They run directly if the tools are on PATH, else through `nix
# develop`. Missing toolchain is a FAILURE, not a skip. FIKA_* env
# overrides flow through to every step, so the gate can be probed
# without editing files:
#     FIKA_BOILER_OD=300 scripts/verify_design.sh   # must fail step 6
#
# Never fix a failing step by loosening its threshold.
set -uo pipefail
cd "$(dirname "$0")/.."
ROOT=$PWD
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
FAIL=0

PY="${PYTHON:-python3}"
PYRUN=(env); case "$PY" in /nix/store/*) PYRUN=(env -u LD_LIBRARY_PATH);; esac

step() { echo; echo "== $*"; }
bad()  { echo "   [FAIL] $*"; FAIL=1; }
good() { echo "   [ok] $*"; }

run_sw() {
    # Run a tool that needs the devshell toolchain.
    if command -v esphome >/dev/null 2>&1 && command -v yamllint >/dev/null 2>&1; then
        "${PYRUN[@]}" "$PY" "$@"
    elif command -v nix >/dev/null 2>&1; then
        nix develop "$ROOT" --command python3 "$@"
    else
        echo "   [FAIL] esphome/yamllint not on PATH and no nix - cannot run $1"
        echo "          pip install -r requirements.txt, or install nix"
        return 1
    fi
}

step "[1/8] Python byte-compile"
if run_sw tools/validate.py python > "$TMP/py.txt" 2>&1; then
    good "scripts/ tools/ byte-compile"
else
    bad "byte-compile failed:"; tail -10 "$TMP/py.txt"
fi

step "[2/8] Params guard (check_params.py)"
if "${PYRUN[@]}" "$PY" scripts/check_params.py > "$TMP/params.txt" 2>&1; then
    tail -1 "$TMP/params.txt" | sed 's/^/   /'
else
    bad "shadowed parameters:"; cat "$TMP/params.txt"
fi

step "[3/8] Software gate (tools/validate.py)"
if run_sw tools/validate.py yaml esphome fabtags protocol cups temps sim > "$TMP/validate.txt" 2>&1; then
    good "tools/validate.py green"
else
    bad "tools/validate.py failed:"; tail -30 "$TMP/validate.txt"
fi

step "[4/8] Full regeneration (temp dir, warnings are errors)"
if "${PYRUN[@]}" "$PY" scripts/regen_all.py --out-dir "$TMP/outputs" > "$TMP/regen.txt" 2>&1; then
    good "all parts, profiles, renders and budgets regenerate cleanly"
else
    bad "regeneration failed:"; tail -20 "$TMP/regen.txt"
fi

step "[5/8] STL watertightness and shell counts"
if "${PYRUN[@]}" "$PY" scripts/check_stl.py --all "$TMP/outputs/stl" > "$TMP/stl.txt" 2>&1; then
    sed 's/^/   /' "$TMP/stl.txt"
else
    bad "STL check failed:"; sed 's/^/   /' "$TMP/stl.txt"
fi

step "[6/8] Layout clearances (check_layout.py)"
if "${PYRUN[@]}" "$PY" scripts/check_layout.py > "$TMP/layout.txt" 2>&1; then
    tail -1 "$TMP/layout.txt" | sed 's/^/   /'
else
    bad "layout violations:"; cat "$TMP/layout.txt"
fi

step "[7/8] Budget assertions (energy_budget.py --check)"
if "${PYRUN[@]}" "$PY" tools/energy_budget.py --check > "$TMP/budget.txt" 2>&1; then
    grep -E "current|heat-up" "$TMP/budget.txt" | sed 's/^/   /'
    good "no [!] flags"
else
    bad "budget raises [!] flags:"; grep -F '[!]' "$TMP/budget.txt"
fi

step "[8/8] Derived artifact drift (temp regen vs committed outputs/)"
CUR_VER=$(scripts/render_scad.sh --version-string 2>/dev/null || true)
REC_VER=$(cat outputs/openscad_version.txt 2>/dev/null || true)
if [ -n "$(env | grep '^FIKA_' || true)" ]; then
    echo "   [skip] FIKA_* overrides active - drift vs committed outputs is expected"
elif [ -n "$CUR_VER" ] && [ -n "$REC_VER" ] && [ "$CUR_VER" != "$REC_VER" ]; then
    # a different OpenSCAD build renders different bytes by design; the
    # byte contract holds between matching toolchains only. Every other
    # step above already ran against this toolchain's output.
    echo "   [skip] byte drift needs the toolchain that made outputs/:"
    echo "          committed: $REC_VER"
    echo "          resolved:  $CUR_VER"
    echo "          (match them, or regenerate and commit with yours)"
else
    DRIFT=$("${PYRUN[@]}" "$PY" - "$TMP/outputs" <<'EOF'
import filecmp, sys
from pathlib import Path
fresh = Path(sys.argv[1])
committed = Path("outputs")
drifted = []
fresh_files = sorted(p.relative_to(fresh) for p in fresh.rglob("*") if p.is_file())
committed_files = sorted(p.relative_to(committed) for p in committed.rglob("*") if p.is_file()) if committed.exists() else []
for rel in fresh_files:
    other = committed / rel
    if not other.exists() or not filecmp.cmp(fresh / rel, other, shallow=False):
        drifted.append(str(rel))
for rel in committed_files:
    if not (fresh / rel).exists():
        drifted.append(f"{rel} (stale, no longer generated)")
print("\n".join(drifted))
EOF
)
    if [ -z "$DRIFT" ]; then
        good "outputs/ matches a fresh regeneration"
    else
        bad "outputs/ drifted - run scripts/regen_all.py and commit the result:"
        echo "$DRIFT" | sed 's/^/        /'
    fi
fi

echo
if [ "$FAIL" -eq 0 ]; then
    echo "[ok] design verification PASSED"
else
    echo "[FAIL] design verification FAILED - fix the items above before committing"
    exit 1
fi
