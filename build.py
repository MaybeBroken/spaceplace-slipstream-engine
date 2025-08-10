import setuptools
import os

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
                    "asyncio/**",
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
                    "asyncio",
                    "asyncio.*",
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
    include_patterns = [
        "client",
        "server",
    ]
    requirements_file = "requirements.txt"
    args = [
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name",
        "SlipstreamEngine",
        "main.py",
        "--log-level",
        "INFO",
    ]
    for pattern in include_patterns:
        args.extend(["--add-data", f"{pattern};{pattern}"])

    os.system("pyinstaller " + " ".join(args))
