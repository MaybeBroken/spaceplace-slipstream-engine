from multiprocessing import Process
from time import sleep
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import *
from panda3d.core import *
from panda3d.core import loadPrcFileData
import client.clientApp as clientApp
import server.serverApp as serverApp
import os
import sys
import traceback
import subprocess
import asyncio.base_events
import asyncio.tasks
import asyncio.streams
import asyncio.events
import asyncio.subprocess


loadPrcFileData("", "win-size 350 150")
loadPrcFileData("", "window-title Slipstream Launcher")
loadPrcFileData("", "win-fixed-size true")
loadPrcFileData("", "load-display pandagl")
loadPrcFileData("", "aux-display p3tinydisplay")
loadPrcFileData("", "aux-display pandadx9")
loadPrcFileData("", "aux-display pandadx8")

if not "__file__" in globals():
    __file__ = os.path.abspath(sys.argv[0])

WORKING_DIR = os.path.dirname(os.path.abspath(__file__))

os.chdir(WORKING_DIR)


class mainWindow(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.setBackgroundColor(0, 0, 0)
        self.disableMouse()
        self.accept("q", self.quit)
        self.launch_server_button = DirectButton(
            text="Launch Server",
            pos=(0, 0, 0.35),
            scale=0.6,
            geom=None,
            relief=DGG.FLAT,
            command=self.launch_server,
        )
        self.launch_client_button = DirectButton(
            text="Launch Client",
            pos=(0, 0, -0.35),
            scale=0.6,
            geom=None,
            relief=DGG.FLAT,
            command=self.launch_client,
        )

    def launch_server(self):
        print("Launching server program...")
        subprocess.Popen([sys.executable, os.path.abspath(__file__), "--server"])

    def launch_client(self):
        print("Launching client program...")
        subprocess.Popen([sys.executable, os.path.abspath(__file__), "--client"])

    def quit(self):
        print("Exiting main program...")
        self.userExit()


def main():
    print("Slipstream Engine starting...")  # Console output for debugging
    try:
        app = mainWindow()
        app.run()
    except Exception as e:
        print("An error occurred. See log file for details.")
        sleep(2)
        sys.exit(e.__traceback__)


def run_server():
    serverApp.run_server()


def run_client():
    clientApp.run_client()


def parse_args():
    import argparse

    parser = argparse.ArgumentParser(description="Slipstream Engine Launcher")
    parser.add_argument("--server", action="store_true", help="Launch server only")
    parser.add_argument("--client", action="store_true", help="Launch client only")
    # Use parse_known_args to ignore unknown arguments (e.g., from multiprocessing)
    args, unknown = parser.parse_known_args()
    return args


if __name__ == "__main__":
    args = parse_args()
    if args.server:
        run_server()
    elif args.client:
        run_client()
    else:
        main()
