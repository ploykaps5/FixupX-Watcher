# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = [
    'pynput.keyboard._xorg',
    'pystray._xorg',          # бэкенд для X11
    'pystray._appindicator',  # бэкенд для GNOME/KDE AppIndicator
    'PIL._tkinter_finder',
]
for pkg in ('pystray', 'PIL', 'psutil'):
    d, b, h = collect_all(pkg)
    datas += d; binaries += b; hiddenimports += h

a = Analysis(
    ['fixupx_watcher.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name='fixupx-watcher',
    debug=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)