from json import dumps, loads
from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
from screeninfo import get_monitors
from direct.gui.DirectGui import *
import mouse
import sys
import os
from panda3d.core import (
    loadPrcFileData,
    TextNode,
    AntialiasAttrib,
    TransparencyAttrib,
    WindowProperties,
)
import direct.stdpy.threading as threading
import win32con
import win32gui
import win32api
from win32controller import win32_WIN_Interface, win32_SYS_Interface

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
monitor_height = monitor.height - 49  # Leave some space for the taskbar
aspect_ratio = monitor_width / monitor_height

loadPrcFileData("", "win-size " + str(monitor_width) + " " + str(monitor_height))
loadPrcFileData("", "window-title Slipstream Client")
loadPrcFileData("", "undecorated true")
loadPrcFileData("", "show-frame-rate-meter true")
loadPrcFileData("", "frame-rate-meter-update-interval 0.1")
loadPrcFileData("", f"win-origin {monitor.x} {monitor.y}")
loadPrcFileData("", "background-color 0 0 0 0")
loadPrcFileData("", "active-display-region true")
loadPrcFileData("", "framebuffer-alpha true")


def generate_monitor_list():
    return [
        {
            "width": monitor.width,
            "height": monitor.height,
            "x": monitor.x,
            "y": monitor.y,
            "is_primary": monitor.is_primary,
            "name": monitor.name,
        }
        for monitor in get_monitors()
    ]


class clientProgram(ShowBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setBackgroundColor(0, 0, 0)
        self.render.set_antialias(AntialiasAttrib.MAuto)

        # Transparency
        self.render2d.setTransparency(TransparencyAttrib.MAlpha)
        self.graphicsEngine.renderFrame()
        # Get Panda3D window handle
        hwnd = self.win.getWindowHandle().getIntHandle()
        self.win_interface = win32_WIN_Interface(hwnd)
        # Set layered style
        styles = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(
            hwnd, win32con.GWL_EXSTYLE, styles | win32con.WS_EX_LAYERED
        )
        # Set per-pixel alpha (0 = fully transparent, 255 = opaque)
        win32gui.SetLayeredWindowAttributes(
            hwnd, win32api.RGB(0, 0, 0), 0, win32con.LWA_COLORKEY
        )
        # Make window always on top
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOPMOST,
            0,
            0,
            0,
            0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
        )

        # End transparency

        self.disableMouse()
        self.accept("q", self.quit)
        self.serverListPanel = DirectFrame(
            parent=self.render2d,
            frameColor=(0.1, 0.1, 0.1, 1),
            frameSize=(-0.175, 0.175, -0.5, 0.5),
            pos=(0, 0, 0),
            relief=DGG.FLAT,
        )
        self.serverListHeading = OnscreenText(
            parent=self.aspect2d,
            text="Available Servers",
            pos=(0, 0.45),
            scale=0.05,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
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
        send_message("CLIENT_INFO||+MONITOR_CONFIG||+" + dumps(generate_monitor_list()))
        self.alert = OnscreenText(
            parent=self.aspect2d,
            text="Initializing client, please continue on the server side...",
            pos=(0, 0),
            scale=0.1,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
        )

    def quit(self):
        print("Exiting client program...")
        self.userExit()

    def server_loop(self, task):
        for message in iter_messages():
            if message.startswith("CLIENT_CONFIG"):
                self.runConfig(message.split("||+")[1])
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

    def runConfig(self, config):
        monitor_count = len(get_monitors())
        if monitor_count == 0:
            return
        if "left" in config:
            curMonitor = self.win_interface.getWindowMonitor()
            newMonitor = (curMonitor - 1) % monitor_count
            self.win_interface.setWindowMonitor(newMonitor)
        elif "right" in config:
            curMonitor = self.win_interface.getWindowMonitor()
            newMonitor = (curMonitor + 1) % monitor_count
            self.win_interface.setWindowMonitor(newMonitor)
        if "left" in config or "right" in config:
            global monitor, monitor_width, monitor_height, aspect_ratio
            monitor = get_monitors()[self.win_interface.getWindowMonitor()]
            monitor_width = monitor.width
            monitor_height = monitor.height
            aspect_ratio = monitor_width / monitor_height
            self.win.requestProperties(
                WindowProperties(
                    size=(monitor.width, monitor.height - 49),
                    origin=(monitor.x, monitor.y),
                )
            )


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
                pos=(0, 0, (-app.serverButtonsOffset) + 0.35),
            )
        )
        app.serverButtonsOffset += 0.2

    app.run()
