from threading import Thread as Thread
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import *
from panda3d.core import *
from panda3d.core import loadPrcFileData
import os
import direct.stdpy.threading as threading

loadPrcFileData("", "win-size 350 150")
loadPrcFileData("", "window-title Slipstream Launcher")


class mainWindow(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.setBackgroundColor(0, 0, 0)
        self.disableMouse()
        self.accept("q", self.quit)
        self.launch_client_button = DirectButton(
            text="Launch Client",
            pos=(0, 0, 0.35),
            scale=0.6,
            geom=None,
            relief=DGG.FLAT,
            command=self.launch_client,
        )
        self.launch_server_button = DirectButton(
            text="Launch Server",
            pos=(0, 0, -0.35),
            scale=0.6,
            geom=None,
            relief=DGG.FLAT,
            command=self.launch_server,
        )

    def launch_server(self):
        print("Launching server program...")
        threading.Thread(target=os.system, args=("python server/serverApp.py",)).start()

    def launch_client(self):
        print("Launching client program...")
        threading.Thread(target=os.system, args=("python client/clientApp.py",)).start()

    def quit(self):
        print("Exiting main program...")
        self.userExit()


if __name__ == "__main__":
    app = mainWindow()
    app.run()
