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
    include_patterns = [
        "client",
        "server",
    ]
    dll_paths = []
    requirements_file = "requirements.txt"

    args = [
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name",
        "test",
        "test.py",
        "--log-level",
        "INFO",
        "--hidden-import",
        "panda3d",
        "--hidden-import",
        "panda3d.core",
        "--collect-all",
        "panda3d",
        "--runtime-hook",
        "pyi_rth_panda3d_pluginpath.py",
    ]

    for pattern in include_patterns:
        args.extend(["--add-data", f"{pattern};{pattern}"])

    try:
        import panda3d  # noqa: F401
        from pathlib import Path as _Path

        p3d_dir = _Path(panda3d.__file__).parent
        added = set()
        binaries = [
            (
                "C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\libpandagl.dll",
                ".",
            ),
            (
                "C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\libpandadx9.dll",
                ".",
            ),
            (
                "C:\\Users\\david\\AppData\\Roaming\\Python\\Python313\\site-packages\\panda3d\\libp3tinydisplay.dll",
                ".",
            ),
        ]

        def add_binary(src_path, dest="."):
            sp = str(src_path)
            if sp not in added:
                args.extend(["--add-binary", f"{sp};{dest}"])
                added.add(sp)

        for bin_path, dest in binaries:
            if os.path.isfile(bin_path):
                add_binary(bin_path, dest)

        for base in [
            "libpandagl",
            "libpandadx11",
            "libpandadx9",
            "libpandadx8",
            "libp3tinydisplay",
            "libp3headlessgl",
            "libpandagles2",
        ]:
            for dll in p3d_dir.glob(f"{base}*.dll"):
                add_binary(dll, ".")

        etc_dir = p3d_dir / "etc"
        if etc_dir.is_dir():
            args.extend(["--add-data", f"{etc_dir};etc"])
    except Exception:
        pass

    def q(a):
        a = str(a)
        return f'"{a}"' if " " in a else a

    os.system("pyinstaller " + " ".join(q(a) for a in args))
