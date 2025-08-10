# Ensures Panda3D finds graphics pipe DLLs when running a onefile PyInstaller build
import os
import sys

try:
    import panda3d.core as p3

    base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    # Make Panda3D search both the root and a plugins/ subdir of the extraction dir
    p3.loadPrcFileData("", f"plugin-path {base}")
    p3.loadPrcFileData("", f"plugin-path {os.path.join(base, 'plugins')}")
except Exception:
    pass