from setuptools import setup

setup(
    name="SlipstreamEngine",
    options={
        "build_apps": {
            "gui_apps": {
                "op_media_player": "runner.py",
            },
            "log_filename": "$USER_APPDATA/SlipstreamEngine/output.log",
            "log_append": False,
            "include_patterns": [
                "Main.py",
                "updater.py",
                "remove_index.json",
                "src/**",
                "client/**",
                "server/**",
            ],
            "plugins": [
                "pandagl",
                "p3openal_audio",
            ],
            "prefer_discrete_gpu": True,
            "platforms": [
                "win_amd64",
            ],
        }
    },
)
