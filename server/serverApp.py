from json import dumps, loads
from re import S
from time import sleep
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import *
from panda3d.core import *
from screeninfo import get_monitors
import mouse
import sys
import os
from panda3d.core import loadPrcFileData, TextNode
import direct.stdpy.threading as threading
from socketServer import (
    send_message,
    iter_messages,
    launch_server,
)
from thorium_api import Connection, asyncio
import base64

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
        self.client_info = {"MONITOR_INDEX": 0}
        self.accept("q", self.quit)
        self.taskMgr.add(self.client_loop, "client_loop")
        self.thorium_connection = Connection()
        self.base_object = {
            "position": [0, 0, 0],
            "rotation": [0, 0, 0],
            "hitbox_scale": [1, 1, 1],
            "hitbox_offset": [0, 0, 0],
            "hitbox_type": "box" or None,
            "hitbox_geom": None or list(tuple()),
            "size": [1, 1, 1],
            "id": "name",
            "color": [1, 0, 0],
            "colorScale": [1, 1, 1, 1],
            "texture": "name.png" or None,
            "texData": None or list(tuple()),
            "onHit": None or "function_name",
            "visible": True,
            "colidable": True,
        }
        self.base_config_data = {
            "MONITOR_INDEX": 0,
            "OBJECTS": {
                "SHIP": self.base_object,
                "OBSTACLES": [self.base_object],
                "TARGETS": [self.base_object],
            },
        }
        self.savedClientData = self.base_config_data.copy()

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
            elif message == "CLIENT_READY":
                self.setPreSimulation()
            elif message.startswith("UPDATE_DATA"):
                data = message.split("||+")[1]
                self.updateData(loads(data))
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

    def loadSavedConfig(self, name):
        if not os.path.exists(f"config/{name}.dat"):
            with open(f"config/{name}.dat", "wb") as f:
                encoded = base64.b64encode(
                    dumps(self.base_config_data, indent=4).encode()
                )
                f.write(encoded)
        with open(f"config/{name}.dat", "rb") as f:
            config_data = f.read()
        ret = loads(base64.b64decode(config_data))
        self.client_config(None, "set_monitor_" + str(ret["MONITOR_INDEX"]))
        self.client_config(None, "set_ship_" + dumps(ret["OBJECTS"]["SHIP"]))
        self.savedClientData = ret
        return ret

    def saveSimulationData(self):
        def saveConfig(name):
            if not name:
                return
            config_data = self.savedClientData or {
                "MONITOR_INDEX": (
                    self.client_info["MONITOR_INDEX"]
                    if "MONITOR_INDEX" in self.client_info
                    else 0
                ),
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
            with open(f"config/{name}.dat", "wb") as f:
                encoded = base64.b64encode(dumps(config_data, indent=4).encode())
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
        self.clientScreenText = OnscreenText(
            text="Press the buttons or use the arrow keys to control which screen the client is on.",
            wordwrap=20,
            pos=(0, 0.8),
            scale=0.07,
            fg=(1, 1, 1, 1),
            bg=(0, 0, 0, 1),
            align=TextNode.ACenter,
            mayChange=True,
        )
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
        self.startButton = DirectButton(
            text="Start Flight",
            scale=0.1,
            pos=(0, 0, -0.8),
            command=lambda: [
                send_message("BUILD_WORLD", target_client=wsock),
                self.startButton.setText("Loading..."),
                self.loadConfigDropdown.destroy(),
            ][0],
        )
        self.loadConfigDropdown = DirectOptionMenu(
            text="Load Config",
            scale=0.1,
            pos=(-1.1, 0, 0.9),
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
        self.accept("arrow_left", self.client_config, extraArgs=[wsock, "left"])
        self.accept("arrow_right", self.client_config, extraArgs=[wsock, "right"])
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
                pos=(index, 0, 0.5),
                scale=0.000125,
            )
            self.cliMonitorObjects.append(node)

    def setPreSimulation(self):
        self.clientScreenText.destroy()
        self.leftButton.destroy()
        self.rightButton.destroy()
        self.startButton.destroy()
        self.accept("arrow_left", lambda: None)
        self.accept("arrow_right", lambda: None)
        for monitor in self.cliMonitorObjects:
            monitor.destroy()

        self.beginSimulationButton = DirectButton(
            text="Begin Simulation",
            scale=0.1,
            pos=(0, 0, -0.8),
            command=lambda: [
                send_message("START_SIMULATION"),
                self.taskMgr.add(self.update, "update_thruster_rotation"),
                self.simulationStart(),
            ][0],
        )

    def simulationStart(self):
        self.beginSimulationButton.destroy()
        self.saveButton = DirectButton(
            text="Save",
            scale=0.1,
            pos=(-0.9, 0, 0.9),
            command=self.saveSimulationData,
        )
        self.thorium_connection.set_thruster_rotation(0, 270, 0)

    def update(self, task):
        distance_changed = self.thorium_connection.get_thruster_loc_rot()
        send_message("UPDATE_THORIUM_SHIP_POSITION||+" + dumps(distance_changed))
        return task.cont


if __name__ == "__main__":
    app = serverProgram()
    launch_server("localhost", 7050)
    app.run()
