# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller packaging specification for 42 Pac-Man."""

from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# Collect all package submodules including dynamically imported mazegenerator
hidden_imports = [
    *collect_submodules("pacman"),
    *collect_submodules("mazegenerator"),
    *collect_submodules("pygame"),
    "mazegenerator.mazegenerator",
]

# Bundle default configuration and clean highscore template
datas = [
    ("config.json", "."),
    ("highscores.json", "."),
]

a = Analysis(
    ["pac-man.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="pacman",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="pacman",
)
