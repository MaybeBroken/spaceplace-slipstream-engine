# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('client', 'client'), ('server', 'server'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\etc', 'etc')]
binaries = [('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\libpandagl.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\libpandadx9.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\libp3tinydisplay.dll', '.')]
hiddenimports = ['panda3d', 'panda3d.core']
tmp_ret = collect_all('panda3d')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['test.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['pyi_rth_panda3d_pluginpath.py'],
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
    name='test',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
