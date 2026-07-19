#!/usr/bin/env bash
# Headless OpenSCAD renderer (no GUI, no X server needed).
#
# Fetches OpenSCAD + Mesa (software GL) from nixpkgs and renders via EGL
# surfaceless. Works in sandboxes/CI where nix-shell's bash may crash and
# where LD_LIBRARY_PATH pollution breaks nix binaries (we override it with
# only the GL libs the nix loader should see).
#
# Usage:
#   scripts/render_scad.sh <file.scad> [output.(png|stl|dxf)] [extra openscad args...]
#
# Examples:
#   scripts/render_scad.sh cad/frame.scad                       # -> cad/frame.png
#   scripts/render_scad.sh cad/main_assembly.scad /tmp/a.png --camera=0,0,0,55,0,25,1200
#   scripts/render_scad.sh cad/boiler.scad boiler.stl           # manifold check/export
set -euo pipefail

CHANNEL="channel:nixos-25.05"

build() { nix-build -I "nixpkgs=$CHANNEL" '<nixpkgs>' -A "$1" --no-out-link 2>/dev/null | tail -1; }

OPENSCAD="$(build openscad-unstable)/bin/openscad"
MESA="$(build mesa)"
GLVND="$(build libglvnd)"

IN="$1"
OUT="${2:-${1%.scad}.png}"
shift; [ $# -gt 0 ] && shift

EXTRA_ARGS=()
case "$OUT" in
  *.png) EXTRA_ARGS+=(--imgsize 1600,1200 --viewall --autocenter) ;;
esac

exec env \
  LD_LIBRARY_PATH="$GLVND/lib:$MESA/lib" \
  __EGL_VENDOR_LIBRARY_FILENAMES="$MESA/share/glvnd/egl_vendor.d/50_mesa.json" \
  EGL_PLATFORM=surfaceless \
  LIBGL_ALWAYS_SOFTWARE=1 \
  "$OPENSCAD" --backend Manifold "${EXTRA_ARGS[@]}" -o "$OUT" "$@" "$IN"
