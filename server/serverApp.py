from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
from screeninfo import get_monitors
import mouse
import sys
import os
from panda3d.core import loadPrcFileData
import direct.stdpy.threading as threading
from socketServer import (
    send_message,
    iter_messages,
    launch_server,
)

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

loadPrcFileData("", "win-size 800 600")
loadPrcFileData("", "window-title Slipstream Server")


class serverProgram(ShowBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setBackgroundColor(0, 0, 0)
        self.disableMouse()
        self.accept("q", self.quit)
        self.taskMgr.add(self.client_loop, "client_loop")

    def client_loop(self, task):
        for message in iter_messages():
            if message == "CLIENT_INIT":
                send_message("BUILD_WORLD")
            else:
                print(f"Received unknown message: {message}")
        return task.cont

    def quit(self):
        print("Exiting server program...")
        self.userExit()


if __name__ == "__main__":
    app = serverProgram()
    launch_server("localhost", 7050)
    app.run()
