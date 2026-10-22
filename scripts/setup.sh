#!/usr/bin/env bash
# One-shot setup: submodules → choreoir (from ./choreo) → this package. Python 3.11+.
set -euo pipefail
cd "$(dirname "$0")/.."
git submodule update --init --recursive
PIP="python3 -m pip install"
# pip on Debian/Ubuntu system Python needs --break-system-packages; harmless elsewhere.
$PIP -q --break-system-packages -e './choreo[dev]' 2>/dev/null || $PIP -q -e './choreo[dev]'
$PIP -q --break-system-packages -e '.[dev]'       2>/dev/null || $PIP -q -e '.[dev]'
agentic-compiler pins
