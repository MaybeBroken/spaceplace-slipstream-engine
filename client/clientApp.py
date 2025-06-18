from json import dumps, loads
from time import sleep, time
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
    LineSegs,
    Point3,
)
from direct.filter.CommonFilters import CommonFilters
import direct.stdpy.threading as threading
import win32con
import win32gui
import win32api
from win32controller import win32_WIN_Interface, win32_SYS_Interface
from worldgen import WorldGen, WorldManager
from direct.stdpy.threading import Thread
import random

import numpy as np
from scipy.stats import norm


# Precompute the bell curve CDF at high resolution, but use vectorized numpy for fast mapping
_x = np.linspace(0, 1, 10000)
_pdf = norm.pdf(_x, loc=0.5, scale=0.15)
_pdf /= _pdf.sum()
_cdf = np.cumsum(_pdf)


def map_weights_to_range(obj_percent_list):
    total_weight = sum(weight for _, weight in obj_percent_list)
    normalized_weights = np.array(
        [weight / total_weight for _, weight in obj_percent_list]
    )

    # Compute CDF boundaries for each object
    cdf_bounds = np.concatenate(([0], np.cumsum(normalized_weights)))
    # Find indices in _cdf for all boundaries at once
    idxs = np.searchsorted(_cdf, cdf_bounds)
    idxs = np.clip(idxs, 0, len(_x) - 1)
    # Map to x values
    x_vals = _x[idxs]

    results = []
    for i, (obj, _) in enumerate(obj_percent_list):
        results.append([obj, float(x_vals[i]), float(x_vals[i + 1])])
    return results


# local imports
from socketClient import (
    start_client,
    send_message,
    iter_messages,
    search_servers,
    register_disconnect_callback,
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
# loadPrcFileData("", "show-frame-rate-meter true")
# loadPrcFileData("", "frame-rate-meter-update-interval 0.1")
loadPrcFileData("", f"win-origin {monitor.x} {monitor.y}")
loadPrcFileData("", "background-color 0 0 0 0")
loadPrcFileData("", "active-display-region true")
loadPrcFileData("", "framebuffer-alpha true")
loadPrcFileData("", "load-display pandagl")
loadPrcFileData("", "aux-display p3tinydisplay")
loadPrcFileData("", "aux-display pandadx9")
loadPrcFileData("", "aux-display pandadx8")


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
        self.backfaceCullingOn()
        self.render.set_antialias(AntialiasAttrib.MAuto)
        register_disconnect_callback(lambda: os.kill(os.getpid(), 9))
        filterMgr = CommonFilters(self.win, self.cam)
        filterMgr.setMSAA(8)

        self.camera_joint = self.render.attachNewNode("camera_joint")
        self.camera.reparentTo(self.camera_joint)
        self.camera.setPos(0, -15, 0)
        self.camera.lookAt(0, 0, 0)

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
        threading.Thread(target=start_client, args=(serverName,)).start()
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
            elif message == "BUILD_WORLD":
                self.build_world()
            elif message == "START_SIMULATION":
                self.start_simulation()
            elif message.startswith("UPDATE_THORIUM_SHIP_POSITION"):
                self.update_thruster_position(message.split("||+")[1])
            elif message == "QUIT":
                self.quit()
            else:
                print(f"CLIENT: Received unknown message: {message}")
        return task.cont

    def build_world(self):
        # Placeholder for world-building logic
        self.alert.setText("CLIENT: Building world...")
        self.graphicsEngine.renderFrame()
        self.worldGrid = self.generateGrid(300, 5)
        self.boxModel = self.loader.loadModel("models/box")
        self.voyager_model = self.loader.loadModel("models/Voyager/voyager.bam")
        self.voyager_model.setScale(0.15)
        self.voyager_model.reparentTo(self.render)
        self.render.prepareScene(self.win.getGsg())
        self.voyager_model.flattenLight()
        self.voyager_model.flattenStrong()
        self.camera_joint.reparentTo(self.voyager_model)
        self.worldGen = WorldGen(
            -1, self.camera, chunk_size=8, voxel_scale=25, noise_scale=1
        )

        self.objects = [
            [None, 80],
            ["models/box", 10],
            ["models/rock", 5],
            ["models/asteroid", 3],
            ["models/ship", 1],
            ["models/space_station", 1],
        ]
        self.objects = map_weights_to_range(self.objects)
        self.WorldManager = WorldManager(self.worldGen, self.camera, renderDistance=6)
        self.renderedChunks = set()
        self.render.hide()
        # List containing objects and their percentage chance of spawning
        self.taskMgr.add(self.renderTerrain, "renderTerrain")
        self.alert.destroy()
        send_message("CLIENT_READY")

    def start_simulation(self):
        self.render.show()
        self.taskMgr.doMethodLater(
            0.25, self.updateServerPositionData, "updateServerPositionData"
        )

    def renderTerrain(self, task):
        self.WorldManager.update()
        newChunks = self.WorldManager.newChunks - self.WorldManager.lastNewChunks

        for chunk in newChunks:
            xCoord, yCoord = chunk
            chunkData = self.worldGen.GENERATED_CHUNKS[chunk]
            for x, y, point in chunkData:
                coord3D = Point3(
                    xCoord * self.worldGen.CHUNK_SIZE + x,
                    yCoord * self.worldGen.CHUNK_SIZE + y,
                    0,
                )
                if coord3D in self.renderedChunks:
                    pass
                pointIndex = (point + 1) / 2
                if pointIndex >= 0.8:
                    model = self.boxModel.copyTo(self.render)
                    model.setPos(coord3D.getX(), coord3D.getY(), 0)
                    self.renderedChunks.add(coord3D)
                self.graphicsEngine.renderFrame()

        self.WorldManager.lastNewChunks = self.WorldManager.newChunks.copy()

    def generateGrid(self, grid_size=100, spacing=10):
        self.gridNode = self.render.attachNewNode("gridNode")

        # Draw grid lines
        for x in range(-grid_size, grid_size + 1):
            line = LineSegs()
            line.setThickness(1.0)
            line.setColor(1, 1, 1, 1)  # White color
            # Horizontal line
            line.moveTo(x * spacing, -grid_size * spacing, 0)
            line.drawTo(x * spacing, grid_size * spacing, 0)
            node = line.create()
            self.gridNode.attachNewNode(node)

        for y in range(-grid_size, grid_size + 1):
            line = LineSegs()
            line.setThickness(1.0)
            line.setColor(1, 1, 1, 1)  # White color
            # Vertical line
            line.moveTo(-grid_size * spacing, y * spacing, 0)
            line.drawTo(grid_size * spacing, y * spacing, 0)
            node = line.create()
            self.gridNode.attachNewNode(node)

        self.gridNode.setTransparency(TransparencyAttrib.MAlpha)
        return self.gridNode

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
        if config.startswith("set_monitor_"):
            newMonitor = int(config.split("_")[-1])
            if newMonitor < monitor_count:
                self.win_interface.setWindowMonitor(newMonitor)
        if "left" in config or "right" in config or config.startswith("set_monitor_"):
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
            send_message(
                "CLIENT_INFO||+MONITOR_INDEX||+"
                + str(self.win_interface.getWindowMonitor())
            )
        if config.startswith("set_ship_"):
            ship_data = loads(config.split("set_ship_")[-1])
            self.camera_joint.setPos(
                ship_data["position"][0],
                ship_data["position"][1],
                ship_data["position"][2],
            )
            self.camera_joint.setHpr(
                ship_data["rotation"][0],
                ship_data["rotation"][1],
                ship_data["rotation"][2],
            )

    def updateServerPositionData(self, task):
        send_message(
            "UPDATE_DATA||+"
            + dumps(
                {
                    "ship": {
                        "pos": [
                            self.camera_joint.getX(),
                            self.camera_joint.getY(),
                            self.camera_joint.getZ(),
                        ],
                        "rot": [
                            self.camera_joint.getH(),
                            self.camera_joint.getP(),
                            self.camera_joint.getR(),
                        ],
                    }
                }
            )
        )
        return task.again

    def update_thruster_position(self, data):
        data = loads(data)
        # self.camera_joint.setPos(
        #     data[0]["x"] / 10 + self.camera_joint.getX(),
        #     data[0]["y"] / 10 + self.camera_joint.getY(),
        #     1,
        # )
        # Clamp pitch to [-45, 45], wrap yaw to [0, 360)
        # If you want pitch to be only [0, 45] and [315, 360], remap accordingly:
        pitch = data[1]["pitch"] % 360
        # Clamp pitch to [0, 45] and [315, 360]
        if 0 <= pitch <= 35:
            mapped_pitch = pitch
        elif 270 <= pitch < 360:
            mapped_pitch = pitch
        elif pitch < 270 and pitch > 35:
            mapped_pitch = 270
        else:
            mapped_pitch = 35
        self.camera_joint.setHpr(
            (data[1]["yaw"] % 360),
            mapped_pitch,
            0,
        )


if __name__ == "__main__":
    app = clientProgram()
    servers = search_servers(7050)
    for srv in servers:
        print(f"CLIENT: Found server: {srv}")
        app.serverButtons.append(
            DirectButton(
                parent=app.aspect2d,
                text=srv,
                text_scale=0.5,
                text_fg=(1, 1, 1, 1),
                color=(0.3, 0.3, 0.3, 1),
                relief=DGG.FLAT,
                scale=0.1,
                command=app.launch,
                extraArgs=[srv],
                pos=(0, 0, (-app.serverButtonsOffset) + 0.35),
            )
        )
        app.serverButtonsOffset += 0.2

    app.run()
