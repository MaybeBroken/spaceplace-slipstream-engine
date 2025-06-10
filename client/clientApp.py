from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
from screeninfo import get_monitors
from direct.gui.DirectGui import *
import mouse
import sys
import os
from panda3d.core import loadPrcFileData, TextNode, AntialiasAttrib
import direct.stdpy.threading as threading

# local imports
from socketClient import (
    start_client,
    send_message,
    iter_messages,
    search_clients,
)

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def get_current_monitor():
    x, y = mouse.get_position()
    for idx, m in enumerate(get_monitors()):
        if m.x <= x < m.x + m.width and m.y <= y < m.y + m.height:
            return idx
    return 0


monitor = get_monitors()[get_current_monitor()]
monitor_width = monitor.width
monitor_height = monitor.height
aspect_ratio = monitor_width / monitor_height

loadPrcFileData("", "win-size " + str(monitor_width) + " " + str(monitor_height))
loadPrcFileData("", "window-title Slipstream Client")
loadPrcFileData("", "undecorated true")
loadPrcFileData("", "show-frame-rate-meter true")
loadPrcFileData("", "frame-rate-meter-update-interval 0.1")
loadPrcFileData("", f"win-origin {monitor.x} {monitor.y}")


class clientProgram(ShowBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setBackgroundColor(0, 0, 0)
        self.render.set_antialias(AntialiasAttrib.MAuto)
        self.disableMouse()
        self.accept("q", self.quit)
        self.serverListHeading = OnscreenText(
            parent=self.aspect2d,
            text="Available Servers",
            pos=(-0.5 * aspect_ratio, 0.65),
            scale=0.1,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
        )
        self.serverListPanel = DirectFrame(
            parent=self.render2d,
            frameColor=(0.1, 0.1, 0.1, 1),
            frameSize=(-0.25, 0.25, -0.5, 0.5),
            pos=(-0.5, 0, 0),
            relief=DGG.FLAT,
        )
        self.serverButtonsOffset = 0
        self.serverButtons = []

    def launch(self, serverName):
        threading.Thread(target=start_client, args=(serverName,), daemon=True).start()
        self.serverListHeading.destroy()
        self.serverListPanel.destroy()
        [button.destroy() for button in self.serverButtons]
        self.taskMgr.add(self.server_loop, "server_loop")
        send_message(
            "CLIENT_INIT",
        )
        self.alert = OnscreenText(
            parent=self.aspect2d,
            text="Loading...",
            pos=(0, 0),
            scale=0.2,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
        )

    def quit(self):
        print("Exiting client program...")
        self.userExit()

    def server_loop(self, task):
        for message in iter_messages():
            if message == "BUILD_WORLD":
                self.build_world()
            elif message == "QUIT":
                self.quit()
            else:
                print(f"Received unknown message: {message}")
        return task.cont

    def build_world(self):
        # Placeholder for world-building logic
        print("Building world... (not implemented)")
        self.alert.setText("Building world...")


if __name__ == "__main__":
    app = clientProgram()
    clients = search_clients(7050)
    for cli in clients:
        print(f"Found client: {cli}")
        app.serverButtons.append(
            DirectButton(
                parent=app.aspect2d,
                text=cli,
                scale=0.1,
                text_scale=0.5,
                command=app.launch,
                extraArgs=[cli],
                pos=(-0.5 * aspect_ratio, 0, (-app.serverButtonsOffset) + 0.4),
            )
        )
        app.serverButtonsOffset += 0.2

    app.run()
