from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
from screeninfo import get_monitors
import mouse
import sys
import os
from panda3d.core import loadPrcFileData
import direct.stdpy.threading as threading

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def get_current_monitor():
    x, y = mouse.get_position()
    for idx, m in enumerate(get_monitors()):
        if m.x <= x < m.x + m.width and m.y <= y < m.y + m.height:
            return idx
    return 0  # Default to primary if not found


monitor = get_monitors()[get_current_monitor()]
monitor_width = monitor.width
monitor_height = monitor.height
aspect_ratio = monitor_width / monitor_height

loadPrcFileData("", "win-size " + str(monitor_width) + " " + str(monitor_height))
loadPrcFileData("", "window-title Slipstream Server")
loadPrcFileData("", "undecorated true")


class serverProgram(ShowBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setBackgroundColor(0, 0, 0)
        self.disableMouse()
        self.accept("q", self.quit)

    def quit(self):
        print("Exiting server program...")
        self.userExit()


if __name__ == "__main__":
    app = serverProgram()

    app.run()
