import setuptools
import os
import sys
from pathlib import Path

if len(os.sys.argv) > 1:
    MODE = "setuptools"
else:
    MODE = "pyinstaller"


if MODE == "setuptools":
    setuptools.setup(
        options={
            "build_apps": {
                "gui_apps": {
                    "Slipstream Engine": "main.py",
                },
                "log_filename": "$USER_APPDATA/SlipstreamEngine/output.log",
                "log_append": False,
                "log_filename_strftime": True,
                "include_patterns": [
                    "client/**",
                    "server/**",
                ],
                "exclude_patterns": [
                    "**/*.py",
                    "**/__pycache__/**",
                    "**/*.blend*",
                ],
                "plugins": [
                    "pandagl",
                    "p3openal_audio",
                    "p3tinydisplay",
                    "pandadx9",
                    "pandadx8",
                ],
                "include_modules": [
                    "client.*",
                    "server.*",
                    "win32.*.*",
                    "urllib",
                ],
                "package_data_dirs": {
                    "win32": [("pywin32_system32/*", "", {}), ("win32/*.pyd", "", {})],
                },
                "prefer_discrete_gpu": True,
                "platforms": ["win_amd64"],
            },
        },
    )
elif MODE == "pyinstaller":
    command_args = [
        "pyinstaller",
        "--onefile",
        # "--windowed",
        "--name",
        "SlipstreamEngine",
        "--collect-data",
        "panda3d",
        "--add-data",
        "client;client",
        "--add-data",
        "server;server",
        "--add-data",
        "client/models:./models",
        "--add-data",
        "client/shaders:./shaders",
        "--contents-directory",
        ".",
        "main.py",
    ]
    command = " ".join(command_args)

    os.system(command)
