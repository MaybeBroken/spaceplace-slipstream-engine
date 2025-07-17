import setuptools

setuptools.setup(
    name="spaceplace-slipstream-engine",
    version="0.1",
    author="David Sponseller",
    author_email="davidsponseller123@gmail.com",
    description="Slipstream Engine for The Space Place at Renaissance Academy",
    long_description="This is the Slipstream Engine, a spaceflight engine for The Space Place at Renaissance Academy.",
    long_description_content_type="text/plain",
    url="https://github.com/MaybeBroken/spaceplace-slipstream-engine",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
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
                "client.*"
                "server.*",
                "win32.*.*",
                "urllib",
                "asyncio",
                "asyncio.*",
            ],
            "package_data_dirs": {
                "win32": [("pywin32_system32/*", "", {}), ("win32/*.pyd", "", {})],
                "asyncio": [("asyncio/*", "", {}), ("asyncio/base_events/*", "", {})],
            },
            "prefer_discrete_gpu": True,
            "platforms": ["win_amd64"],
        },
    },
)
