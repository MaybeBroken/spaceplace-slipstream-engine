from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
from screeninfo import get_monitors
import sys
import os
from panda3d.core import loadPrcFileData

monitors = get_monitors()
if monitors:
    screen_x = monitors[0].width
    screen_y = monitors[0].height
else:
    screen_x = 800
    screen_y = 600

loadPrcFileData("", f"win-size {screen_x} {screen_y}")
loadPrcFileData("", "window-title Slipstream Client")
loadPrcFileData("", "undecorated true")


class clientProgram(ShowBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setBackgroundColor(0, 0, 0)
        self.disableMouse()
        self.accept("q", self.quit)

    def quit(self):
        print("Exiting client program...")
        self.userExit()


if __name__ == "__main__":
    app = clientProgram()
    app.run()
