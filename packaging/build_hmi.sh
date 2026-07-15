#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ARCH="$(uname -m)"
OUTPUT="HMI_python_linux_${ARCH}"

python3 -m pip install -r src/HMI/requirements.txt
python3 -m PyInstaller --clean --noconfirm packaging/HMI_python.spec
cp dist/HMI_python "dist/${OUTPUT}"

echo "Executable created at: $ROOT_DIR/dist/HMI_python"
echo "Architecture-specific copy: $ROOT_DIR/dist/${OUTPUT}"
