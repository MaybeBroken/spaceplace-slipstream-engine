# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\api-ms-win-crt-multibyte-l1-1-0.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\api-ms-win-crt-utility-l1-1-0.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\avcodec-55.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\avformat-55.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\avutil-52.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\cg.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\cgD3D9.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\cgGL.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\d3dx9_43.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\fmodex64.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\libp3assimp.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\libp3direct.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\libp3dtool.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\libp3dtoolconfig.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\libp3ffmpeg.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\libp3fmod_audio.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\libp3interrogatedb.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\libp3openal_audio.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\libp3ptloader.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\libp3tinydisplay.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\libp3vision.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\libp3vrpn.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\libp3windisplay.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\libpanda.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\libpandaai.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\libpandabullet.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\libpandadx9.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\libpandaegg.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\libpandaexpress.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\libpandafx.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\libpandagl.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\libpandaode.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\libpandaphysics.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\libpandaskel.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\MSVCP140.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\swresample-0.dll', '.'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\swscale-2.dll', '.')],
    datas=[('client', 'client'), ('server', 'server'), ('C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\etc', 'etc')],
    hiddenimports=['panda3d', 'panda3d.core'],
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
    name='SlipstreamEngine',
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
