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

loadPrcFileData("", "win-size 350 150")
loadPrcFileData("", "window-title Slipstream Launcher")
loadPrcFileData("", "win-fixed-size true")
loadPrcFileData("", "load-display pandagl")
loadPrcFileData("", "aux-display p3tinydisplay")
loadPrcFileData("", "aux-display pandadx9")
loadPrcFileData("", "aux-display pandadx8")

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
        Process(target=serverApp.run_server, args=()).start()

    def launch_client(self):
        print("Launching client program...")
        Process(target=clientApp.run_client, args=()).start()

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


if __name__ == "__main__":
    main()
