# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

project_root = Path.cwd()
hmi_src = project_root / "src" / "HMI"


a = Analysis(
    [str(hmi_src / "HMI_python.py")],
    pathex=[str(hmi_src)],
    binaries=[("/home/cetevi/miniconda3/lib/libexpat.so.1", ".")
              ],
    datas=[(str(hmi_src / "Plots" ), "Plots"), (str(hmi_src / "hmi" / "utils" / "QRCodes"), "QRCodes")],
    hiddenimports=["snap7", "serial"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="HMI_python",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
