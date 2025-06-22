from datetime import date
from json import dumps, loads
from random import randint
from re import S
from time import sleep
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import *
from panda3d.core import *
from screeninfo import get_monitors
import mouse
import sys
import os
from panda3d.core import (
    loadPrcFileData,
    TextNode,
    LineSegs,
    TransparencyAttrib,
    Vec3,
    Vec4,
)
import direct.stdpy.threading as threading
from socketServer import (
    send_message,
    iter_messages,
    launch_server,
    register_disconnect_callback,
)
from thorium_api import Connection, asyncio
import base64
from PIL import Image
from direct.interval.IntervalGlobal import *

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
loadPrcFileData("", "load-display pandagl")
loadPrcFileData("", "aux-display p3tinydisplay")
loadPrcFileData("", "aux-display pandadx9")
loadPrcFileData("", "aux-display pandadx8")
loadPrcFileData("", f"win-fixed-size true")
# loadPrcFileData("", f"want-pstats true")

import requests

if not os.path.exists("textures"):
    os.makedirs("textures")
if not os.path.exists("textures/apod.txt"):
    with open("textures/apod.txt", "w") as f:
        f.write("NULL")
with open("textures/apod.txt", "r") as f:
    last_date = f.read().strip()
if last_date != date.today().isoformat() or not os.path.exists("textures/apod.jpg"):

    API_KEY = "DEMO_KEY"
    URL = f"https://api.nasa.gov/planetary/apod?api_key={API_KEY}"

    APOD_response = requests.get(URL)
    APOD_data: dict = APOD_response.json()

    def fetch_file(url: str, local_path: str) -> None:

        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with requests.get(url, stream=True) as response:
                response.raise_for_status()  # Raise an error for bad responses
                with open(local_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
        except requests.RequestException as e:
            print(f"Error downloading file {url}: {e}")
        except Exception as e:
            print(f"Error saving file {url} at {local_path}: {e}")

    if APOD_data.get("media_type") == "image":
        image_url = APOD_data.get("hdurl") or APOD_data.get("url")
        fetch_file(image_url, "textures/apod.jpg")
        with open("textures/apod.txt", "w") as f:
            f.write(date.today().isoformat())
        with open("textures/apod_info.txt", "w") as f:
            f.write(APOD_data.get("title", ""))
            f.write("||+")
            f.write(APOD_data.get("explanation", ""))


class serverProgram(ShowBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setBackgroundColor(0, 0, 0)
        self.disableMouse()
        self.client_info = {"MONITOR_INDEX": 0}
        self.accept("q", self.quit)
        self.taskMgr.add(self.client_loop, "client_loop")
        self.thorium_connection = Connection()
        self.base_object = {
            "position": [0, 0, 0],
            "rotation": [0, 0, 0],
            "hitbox_scale": [1, 1, 1],
            "hitbox_offset": [0, 0, 0],
            "hitbox_type": None,
            "hitbox_geom": None,
            "size": [1, 1, 1],
            "id": "obstacle",
            "name": "name",
            "color": [1, 1, 1, 1],
            "colorScale": [1, 1, 1, 1],
            "texture": None,
            "texData": None,
            "onHit": None,
            "visible": True,
            "colidable": True,
        }
        self.base_config_data = {
            "MONITOR_INDEX": 0,
            "SEED": randint(0, 1000000),
            "OBJECTS": {
                "SHIP": self.base_object,
                "OBSTACLES": [],
                "TARGETS": [],
            },
        }
        self.savedClientData = self.base_config_data.copy()
        if os.path.exists("textures/apod.jpg"):
            image = Image.open("textures/apod.jpg")
            self.apod_image = OnscreenImage(
                image="textures/apod.jpg",
                pos=(0, -0.5, -0.1),
                scale=(
                    1.5,
                    1,
                    1.5 * image.height / image.width,
                ),
            )
            self.apod_image.setTransparency(TransparencyAttrib.MAlpha)
        self.init_text = OnscreenText(
            text="Waiting for client to connect...",
            pos=(0, 0.45),
            scale=0.15,
            fg=(1, 1, 1, 1),
            bg=(0, 0, 0, 0.4),
            align=TextNode.ACenter,
        )
        self.init_text.setTransparency(TransparencyAttrib.MAlpha)
        self.instruction_text = OnscreenText(
            text="Please complete setup in thorium first, if not already done: go to the client config and assign the Slipstream Engine to the active flight and the Slipstream Core page",
            pos=(0, 0.25),
            scale=0.05,
            wordwrap=25,
            fg=(1, 1, 1, 0.7),
            bg=(0, 0, 0, 0.4),
            align=TextNode.ACenter,
        )
        self.instruction_text.setTransparency(TransparencyAttrib.MAlpha)
        if os.path.exists("textures/apod_info.txt"):
            with open("textures/apod_info.txt", "r") as f:
                apod_info = f.read().split("||+")
            self.apod_title = OnscreenText(
                text=apod_info[0],
                pos=(1, -0.8),
                scale=0.05,
                fg=(1, 1, 1, 1),
                bg=(0, 0, 0, 0.4),
                align=TextNode.ARight,
            )
            self.apod_title.setTransparency(TransparencyAttrib.MAlpha)
        if os.path.exists("textures/apod.txt"):
            with open("textures/apod.txt", "r") as f:
                last_date = f.read().strip()
            self.apod_date = OnscreenText(
                text=f"{last_date}",
                pos=(-1, 0.9),
                scale=0.06,
                fg=(1, 1, 1, 1),
                bg=(0, 0, 0, 0.4),
                align=TextNode.ALeft,
            )
            self.apod_date.setTransparency(TransparencyAttrib.MAlpha)
        self.mapNodes = []
        self.currentMapNodeCount = 0

    def client_loop(self, task):
        for entry in iter_messages():
            wsock, message = entry if isinstance(entry, tuple) else (None, entry)
            if message == "CLIENT_INIT":
                self.runClientConfig(wsock)
            elif message.startswith("CLIENT_INFO"):
                info_id = message.split("||+")[1]
                client_info = message.split("||+")[2]
                self.client_info[info_id] = loads(client_info)
                if info_id == "MONITOR_INDEX":
                    self.savedClientData["MONITOR_INDEX"] = self.client_info[
                        "MONITOR_INDEX"
                    ]
                elif info_id == "SEED":
                    self.savedClientData["SEED"] = self.client_info["SEED"]
                    self.seedEntry.set(str(self.savedClientData["SEED"]))
                    LerpColorScaleInterval(
                        self.seedEntry,
                        0.5,
                        Vec4(1, 1, 1, 1),
                        Vec4(0, 1, 0, 1),
                    ).start()
            elif message == "CLIENT_READY":
                self.setPreSimulation()
            elif message.startswith("UPDATE_DATA"):
                data = message.split("||+")[1]
                self.updateData(loads(data))
            elif message.startswith("NEW_OBJECT"):
                data = message.split("||+")[1]
                self.newObject(loads(data))
            else:
                print(f"SERVER: Received unknown message: {message}")
        return task.cont

    def quit(self):
        print("SERVER: Exiting server program...")
        self.userExit()

    def client_config(self, wsock, data):
        send_message("CLIENT_CONFIG||+" + data, target_client=wsock)

    def updateData(self, data):
        self.savedClientData["OBJECTS"]["SHIP"]["position"] = data["ship"]["pos"]
        self.savedClientData["OBJECTS"]["SHIP"]["rotation"] = data["ship"]["rot"]

    def toggleColorTask(self, task):
        if hasattr(self, "shipMappingNode"):
            ship_data = self.savedClientData["OBJECTS"]["SHIP"]
            if ship_data["color"] == [1, 0, 0, 1]:
                ship_data["color"] = [0, 1, 0, 1]
            else:
                ship_data["color"] = [1, 0, 0, 1]
            newNode = self.shipMappingNode.copyTo(self.shipMappingNode.getParent())
            newNode.setColor(*ship_data["color"])
            newNode.setBin("fixed", 0)
            self.shipMappingNode.removeNode()
            self.shipMappingNode = newNode
        return task.again

    def newObject(self, data):
        if data["id"] == "ship":
            self.savedClientData["OBJECTS"]["SHIP"] = data
        scale = 0.01
        node = DirectFrame(
            parent=self.aspect2d,
            frameSize=(-1, 1, -1, 1),
            frameColor=tuple(data["color"]),
            pos=(
                data["position"][0] * scale,
                0,
                data["position"][1] * scale,
            ),
            scale=data["size"][0] * scale,
        )
        if self.currentMapNodeCount >= 20 or len(self.mapNodes) == 0:
            self.currentMapNodeCount = 0
            parent = self.mapObjectNode.attachNewNode("mapChildNode")
            self.mapNodes.append(parent)
            if len(self.mapNodes) > 1:
                self.mapNodes[-2].flattenLight()
        else:
            parent = self.mapNodes[-1]
        node.reparentTo(parent)
        if data["id"] == "ship":
            self.shipMappingNode = node
            self.doMethodLater(
                1,
                self.toggleColorTask,
                "toggle_color_task",
            )
        self.currentMapNodeCount += 1
        if "customSetType" in data:
            self.savedClientData["OBJECTS"]["OBSTACLES"].append(data)

    def loadSavedConfig(self, name):
        if not os.path.exists(f"config/{name}.dat"):
            with open(f"config/{name}.dat", "wb") as f:
                encoded = base64.b64encode(
                    dumps(self.base_config_data, indent=4).encode()
                )
                f.write(encoded)
        with open(f"config/{name}.dat", "rb") as f:
            config_data = f.read()
        ret = loads(base64.b32hexdecode(config_data))
        self.client_config(None, "set_monitor_" + str(ret["MONITOR_INDEX"]))
        self.client_config(None, "set_ship_" + dumps(ret["OBJECTS"]["SHIP"]))
        self.client_config(None, "set_seed_" + str(ret["SEED"]))
        self.client_config(None, "set_obstacles_" + dumps(ret["OBJECTS"]["OBSTACLES"]))
        self.client_config(None, "set_targets_" + dumps(ret["OBJECTS"]["TARGETS"]))
        self.savedClientData = ret
        return ret

    def saveSimulationData(self):
        def saveConfig(name):
            if not name:
                return
            config_data = (
                {
                    "MONITOR_INDEX": (
                        self.client_info["MONITOR_INDEX"]
                        if "MONITOR_INDEX" in self.client_info
                        else 0
                    ),
                    "SEED": None,
                    "OBJECTS": {
                        "SHIP": {
                            "position": [0, 0, 0],
                            "rotation": [0, 0, 0],
                            "hitbox_scale": [1, 1, 1],
                            "hitbox_offset": [0, 0, 0],
                            "hitbox_type": "box",
                            "hitbox_geom": None,
                            "size": [1, 1, 1],
                            "id": "ship",
                            "color": [1, 0, 0],
                            "colorScale": [1, 1, 1, 1],
                            "texture": None,
                            "texData": None,
                            "onHit": None,
                            "visible": True,
                            "colidable": True,
                        },
                        "OBSTACLES": [],
                        "TARGETS": [],
                    },
                }
                if not hasattr(self, "savedClientData")
                else self.savedClientData.copy()
            )
            with open(f"config/{name}.dat", "wb") as f:
                encoded = base64.b32hexencode(dumps(config_data, indent=4).encode())
                f.write(encoded)
            print(f"Config saved as {name}.dat")
            nameRequest.destroy()

        nameRequest = DirectEntry(
            text="",
            scale=0.1,
            pos=(-0.8, 0, 0.9),
            initialText="Name",
            numLines=1,
            command=saveConfig,
        )

    def runClientConfig(self, wsock):
        if not os.path.exists("config"):
            os.makedirs("config")
        if "MONITOR_CONFIG" not in self.client_info:
            self.taskMgr.doMethodLater(
                0.1,
                lambda task: self.runClientConfig(wsock) or task.done,
                "wait_for_monitor_config",
            )
            return
        self.init_text.destroy()
        self.instruction_text.destroy()
        if hasattr(self, "apod_title"):
            self.apod_title.destroy()
        if hasattr(self, "apod_date"):
            self.apod_date.destroy()
        self.clientScreenText = OnscreenText(
            text="Press the buttons or use the arrow keys to control which screen the client is on.",
            wordwrap=20,
            pos=(0, 0.8),
            scale=0.07,
            fg=(1, 1, 1, 1),
            bg=(0, 0, 0, 0.4),
            align=TextNode.ACenter,
            mayChange=True,
        )
        self.clientScreenText.setTransparency(TransparencyAttrib.MAlpha)
        self.leftButton = DirectButton(
            text="<",
            scale=0.1,
            pos=(-0.75, 0, 0.8),
            command=self.client_config,
            extraArgs=[wsock, "left"],
        )
        self.rightButton = DirectButton(
            text=">",
            scale=0.1,
            pos=(0.75, 0, 0.8),
            command=self.client_config,
            extraArgs=[wsock, "right"],
        )
        self.sizeBoundsFrame = DirectFrame(
            parent=self.aspect2d,
            frameSize=(-1, 1, -0.75, 0.75),
            frameColor=(0, 0, 0, 0.8),
            scale=0.9,
            pos=(0, 0, -0.15),
        )
        self.sizeBoundsFrame.setTransparency(TransparencyAttrib.MAlpha)
        self.startButton = DirectButton(
            text="Start Flight",
            scale=0.1,
            pos=(0, 0, -0.92),
            command=lambda: [
                send_message("BUILD_WORLD", target_client=wsock),
                self.startButton.setText("Loading..."),
                self.loadConfigDropdown.destroy(),
            ][0],
        )
        self.loadConfigDropdown = DirectOptionMenu(
            text="Load Config",
            scale=0.08,
            pos=(-1.25, 0, 0.91),
            items=["Load a saved config"]
            + [
                f.split(os.path.sep)[-1].removesuffix(".dat")
                for f in os.listdir("config")
                if f.endswith(".dat")
            ],
            command=lambda x: (
                self.loadSavedConfig(x) if x != "Load a saved config" else None
            ),
        )
        self.seedEntry = DirectEntry(
            initialText=str(self.savedClientData["SEED"]),
            scale=0.1,
            pos=(0.6, 0, 0.9),
            command=lambda s: self.client_config(wsock, "set_seed_" + s),
        )
        self.accept("arrow_left", self.client_config, extraArgs=[wsock, "left"])
        self.accept("arrow_right", self.client_config, extraArgs=[wsock, "right"])
        self.client_config(
            wsock,
            ("set_seed_" + self.savedClientData["SEED"].__str__()),
        )
        index = -1
        self.cliMonitorObjects = []
        for screenObj in self.client_info["MONITOR_CONFIG"]:
            index += 0.4
            node = DirectFrame(
                parent=self.aspect2d,
                frameSize=(
                    -screenObj["width"] / 2,
                    screenObj["width"] / 2,
                    -screenObj["height"] / 2,
                    screenObj["height"] / 2,
                ),
                frameColor=(0.3, 0.3, 0.3, 1),
                pos=(index, 0, 0.6),
                scale=0.000125,
            )
            self.cliMonitorObjects.append(node)

    def generateGrid(self, grid_size=100, spacing=10):
        self.gridNode = self.render.attachNewNode("gridNode")

        # Draw grid lines
        for x in range(-grid_size, grid_size + 1):
            line = LineSegs()
            line.setThickness(1.0)
            line.setColor(0.3, 0.3, 0.3, 1)  # Gray color
            # Horizontal line
            line.moveTo(x * spacing, -grid_size * spacing, 0)
            line.drawTo(x * spacing, grid_size * spacing, 0)
            node = line.create()
            self.gridNode.attachNewNode(node)

        for y in range(-grid_size, grid_size + 1):
            line = LineSegs()
            line.setThickness(1.0)
            line.setColor(0.3, 0.3, 0.3, 1)  # Gray color
            # Vertical line
            line.moveTo(-grid_size * spacing, y * spacing, 0)
            line.drawTo(grid_size * spacing, y * spacing, 0)
            node = line.create()
            self.gridNode.attachNewNode(node)

        self.gridNode.setTransparency(TransparencyAttrib.MAlpha)
        return self.gridNode

    def setPreSimulation(self):
        self.clientScreenText.destroy()
        self.leftButton.destroy()
        self.rightButton.destroy()
        self.startButton.destroy()
        self.sizeBoundsFrame.destroy()
        self.seedEntry.destroy()
        self.apod_image.destroy() if hasattr(self, "apod_image") else None
        self.accept("arrow_left", lambda: None)
        self.accept("arrow_right", lambda: None)
        for monitor in self.cliMonitorObjects:
            monitor.destroy()
        self.saveButton = DirectButton(
            text="Save",
            scale=0.1,
            pos=(-0.93, 0, 0.9),
            command=self.saveSimulationData,
        )
        self.mapHideButton = DirectButton(
            text="Hide Map",
            scale=0.1,
            pos=(0.93, 0, 0.9),
            command=self.hideMap,
        )
        self.map = DirectFrame(
            parent=self.aspect2d,
            frameSize=(-1, 1, -1, 1),
            frameColor=(0, 0, 0, 0),
            scale=1,
            pos=(0, 0, 0),
        )
        self.map.setTransparency(TransparencyAttrib.MAlpha)
        self.map.setBin("background", 0)
        self.map.setDepthWrite(False)
        self.map.setDepthTest(False)
        self.mapObjectNode = self.map.attachNewNode("mapObjectNode")
        self.generateGrid(100, 20 * 0.01)
        self.gridNode.reparentTo(self.mapObjectNode)
        self.gridNode.setP(90)
        self.accept(
            "wheel_up",
            self.zoomIn,
        )
        self.accept(
            "wheel_down",
            self.zoomOut,
        )
        self.accept("mouse1", self.startDrag)
        self.accept("mouse1-up", self.stopDrag)
        self.accept("mouse3", self.initPlaceMenu)
        self.dragging = False
        self.taskMgr.add(self.drag_task, "drag_task")

        self.beginSimulationButton = DirectButton(
            text="Begin Simulation",
            scale=0.1,
            pos=(0, 0, -0.93),
            command=self.simulationStart,
        )

    def startDrag(self):
        self.dragging = True
        if hasattr(self, "placeMenu") and self.placeMenu is not None:
            self.closePlaceMenu()
        self.last_mouse_pos = (
            self.mouseWatcherNode.getMouse().getX(),
            self.mouseWatcherNode.getMouse().getY(),
        )
        self.mapObjectNodeStartPos = self.mapObjectNode.getPos()

    def stopDrag(self):
        self.dragging = False
        self.last_mouse_pos = None
        self.mapObjectNodeStartPos = None

    def drag_task(self, task):
        if self.dragging:
            current_mouse_pos = (
                self.mouseWatcherNode.getMouse().getX(),
                self.mouseWatcherNode.getMouse().getY(),
            )
            delta = (
                (current_mouse_pos[0] - self.last_mouse_pos[0])
                / self.map.getScale()[0],
                (current_mouse_pos[1] - self.last_mouse_pos[1])
                / self.map.getScale()[1],
            )
            self.mapObjectNode.setPos(
                self.mapObjectNodeStartPos
                + Vec3(delta[0] * self.getAspectRatio(), 0, delta[1])
            )
        return task.cont

    def initPlaceMenu(self):
        if hasattr(self, "placeMenu") and self.placeMenu is not None:
            self.closePlaceMenu()
        pos = (
            self.mouseWatcherNode.getMouse().getX() * self.getAspectRatio(),
            0,
            self.mouseWatcherNode.getMouse().getY(),
        )
        self.placeMenu = DirectFrame(
            parent=self.aspect2d,
            frameSize=(0, 0.5, -0.75, 0),
            frameColor=(0.2, 0.2, 0.2, 0.8),
            pos=(pos[0], pos[1], pos[2]),
        )
        self.placeMenu.setTransparency(TransparencyAttrib.MAlpha)
        self.placeMenuButtons = []
        for obj_type in [
            "black_hole",
            "wormhole",
            "nebula",
            "solar_system",
            "rogue_planet",
            "target",
        ]:
            button = DirectButton(
                parent=self.placeMenu,
                text=obj_type,
                scale=0.09,
                pos=(0.25, 0, -0.11 * len(self.placeMenuButtons) - 0.1),
                command=self.createObject,
                extraArgs=[obj_type, pos],
            )
            self.placeMenuButtons.append(button)

    def createObject(self, obj_type, pos):
        obj_data = self.base_object.copy()
        obj_data["name"] = obj_type
        # Convert screen (mouse) coordinates to map coordinates, accounting for translation and scale
        map_scale = self.map.getScale()
        map_x = (pos[0] - (self.mapObjectNode.getX() * map_scale[0])) / map_scale[0]
        map_y = (pos[2] - (self.mapObjectNode.getZ() * map_scale[2])) / map_scale[2]
        obj_data["position"] = [
            map_x * 100,
            map_y * 100,
            0,
        ]
        obj_data["customSetType"] = True
        send_message(
            "NEW_OBJECT||+" + dumps(obj_data),
            target_client=None,
        )
        self.closePlaceMenu()

    def closePlaceMenu(self):
        if hasattr(self, "placeMenu") and self.placeMenu is not None:
            self.placeMenu.destroy()
            self.placeMenu = None
        for button in self.placeMenuButtons:
            button.destroy()
        self.placeMenuButtons = []

    def zoomIn(self):
        current_scale = self.map.getScale()
        new_scale = current_scale * 1.1
        self.map.setScale(new_scale)

    def zoomOut(self):
        current_scale = self.map.getScale()
        new_scale = current_scale * 0.9
        self.map.setScale(new_scale)

    def hideMap(self):
        if hasattr(self, "map"):
            self.map.hide()
        if hasattr(self, "mapHideButton"):
            self.mapHideButton.setText("Show Map")
            self.mapHideButton["command"] = self.showMap
        self.accept("wheel_up", lambda: None)
        self.accept("wheel_down", lambda: None)
        self.accept("mouse1", lambda: None)
        self.accept("mouse1-up", lambda: None)
        self.accept("mouse3", lambda: None)

    def showMap(self):
        if hasattr(self, "map"):
            self.map.show()
        if hasattr(self, "mapHideButton"):
            self.mapHideButton.setText("Hide Map")
            self.mapHideButton["command"] = self.hideMap
        self.accept("wheel_up", self.zoomIn)
        self.accept("wheel_down", self.zoomOut)
        self.accept("mouse1", self.startDrag)
        self.accept("mouse1-up", self.stopDrag)
        self.accept("mouse3", self.initPlaceMenu)

    def destroyMap(self):
        for node in self.mapNodes:
            node.removeNode()
        if hasattr(self, "gridNode"):
            self.gridNode.removeNode()
            self.gridNode = None
        if hasattr(self, "mapObjectNode"):
            self.mapObjectNode.removeNode()
            self.mapObjectNode = None
        if hasattr(self, "map"):
            self.map.destroy()
            self.map = None
        self.mapNodes.clear()
        self.currentMapNodeCount = 0
        self.taskMgr.remove("drag_task")
        self.accept("wheel_up", lambda: None)
        self.accept("wheel_down", lambda: None)
        self.accept("mouse1", lambda: None)
        self.accept("mouse1-up", lambda: None)
        self.accept("mouse3", lambda: None)

    def simulationStart(self):
        send_message("START_SIMULATION"),
        self.beginSimulationButton.destroy()
        self.taskMgr.add(self.update, "update_thruster_rotation")

        self.thorium_connection.set_thruster_rotation(0, 270, 0)

    def update(self, task):
        distance_changed = self.thorium_connection.get_thruster_loc_rot()
        send_message("UPDATE_THORIUM_SHIP_POSITION||+" + dumps(distance_changed))
        return task.cont


if __name__ == "__main__":
    app = serverProgram()
    launch_server("localhost", 7050)
    app.run()
