from json import dumps, loads
from time import sleep, time
from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
from screeninfo import get_monitors
from direct.gui.DirectGui import *
import mouse
import os
from panda3d.core import (
    loadPrcFileData,
    TextNode,
    AntialiasAttrib,
    TransparencyAttrib,
    WindowProperties,
    LineSegs,
    Shader,
    Vec4,
    Vec3,
    ColorBlendAttrib,
)
from direct.filter.CommonFilters import CommonFilters
import direct.stdpy.threading as threading
import win32con
import win32.win32gui as win32gui
import win32.win32api as win32api
from .win32controller import win32_WIN_Interface, win32_SYS_Interface
from .worldgen import WorldGen, WorldManager
from direct.stdpy.threading import Thread
import random
from .physics import physicsMgr
from scipy.stats import norm
import math


def clamp(value, min_value, max_value):
    if value <= min_value:
        return min_value
    elif value >= max_value:
        return max_value
    else:
        return value


# Precompute the bell curve CDF at high resolution using pure Python for fast mapping
_x = [i / 9999 for i in range(10000)]
_pdf = [norm.pdf(x, loc=0.5, scale=0.15) for x in _x]
pdf_sum = sum(_pdf)
_pdf = [p / pdf_sum for p in _pdf]
_cdf = []
acc = 0.0
for p in _pdf:
    acc += p
    _cdf.append(acc)


def map_weights_to_range(obj_percent_list):
    total_weight = sum(weight for _, weight in obj_percent_list)
    normalized_weights = [weight / total_weight for _, weight in obj_percent_list]

    # Compute CDF boundaries for each object
    cdf_bounds = [0]
    acc = 0.0
    for w in normalized_weights:
        acc += w
        cdf_bounds.append(acc)

    # Find indices in _cdf for all boundaries at once
    def searchsorted(arr, val):
        # Binary search for insertion index
        lo, hi = 0, len(arr)
        while lo < hi:
            mid = (lo + hi) // 2
            if arr[mid] < val:
                lo = mid + 1
            else:
                hi = mid
        return lo

    idxs = [min(searchsorted(_cdf, b), len(_x) - 1) for b in cdf_bounds]
    x_vals = [_x[i] for i in idxs]

    results = []
    for i, (obj, _) in enumerate(obj_percent_list):
        results.append([obj, float(x_vals[i]), float(x_vals[i + 1])])
    return results


# local imports
from .socketClient import (
    start_client,
    send_message,
    iter_messages,
    search_servers,
    register_disconnect_callback,
)

WORKING_DIR = os.path.dirname(os.path.abspath(__file__))


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
        self.physicsMgr = physicsMgr()
        self.physicsMgr.enable(drag=0.0003, gravity=(0, 0, 0))
        register_disconnect_callback(lambda: os.kill(os.getpid(), 9))
        filterMgr = CommonFilters(self.win, self.cam)
        filterMgr.setMSAA(2)

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
        self.worldGen = WorldGen(
            threshold=-1,
            chunk_size=6,
            voxel_scale=32,
            noise_scale=1,
            seed=0,
        )
        self.obstaclesToPlace = []
        self.targetsToPlace = []

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
            elif message.startswith("NEW_OBJECT"):
                self.create_new_object(loads(message.split("||+")[1]))
            else:
                print(f"CLIENT: Received unknown message: {message}")
        return task.cont

    def build_world(self):
        self.alert.setText("CLIENT: Building world...")
        self.graphicsEngine.renderFrame()
        self.camLens.setNearFar(0.01, 20000)
        self.worldGrid = self.generateGrid(100, 20)
        self.boxModel = self.loader.loadModel("models/box")
        self.circleModel = self.loader.loadModel(
            os.path.join(WORKING_DIR, "models", "Circle", "circle.bam")
            .replace("\\", "/")
            .replace("c:", "/c")
        )
        self.distanceShader = Shader.load(
            Shader.SL_GLSL,
            os.path.join(WORKING_DIR, "shaders", "fade.vert")
            .replace("\\", "/")
            .replace("c:", "/c"),
            os.path.join(WORKING_DIR, "shaders", "fade.frag")
            .replace("\\", "/")
            .replace("c:", "/c"),
        )
        self.circleModel.setShader(self.distanceShader)
        self.circleModel.setShaderInput("fadeDistance", 1)
        self.circleModel.setShaderInput("fadeColor", Vec4(1, 1, 1, 1))
        self.circleModel.setShaderInput("fadeCenter", Vec3(0, 0, 0))
        self.voyager_model = self.loader.loadModel(
            os.path.join(WORKING_DIR, "models", "Voyager", "voyager.bam")
            .replace("\\", "/")
            .replace("c:", "/c")
        )
        self.voyager_model.setScale(0.1)
        self.rootNode = self.render.attachNewNode("rootNode")
        self.voyager_model.reparentTo(self.rootNode)
        self.physicsMgr.registerObject(
            object=self.rootNode,
            name="ship",
            velocity=[0, 0, 0],
            velocityLimit=[0.5, 0.5, 0.5],
        )
        self.engineRingNode = self.loader.loadModel(
            os.path.join(WORKING_DIR, "models", "Ring", "ring.bam")
            .replace("\\", "/")
            .replace("c:", "/c")
        )
        self.engineRingNode.reparentTo(self.voyager_model)
        self.engineRingNode.setScale(8)
        self.engineRingNode.setTransparency(TransparencyAttrib.MAlpha)
        self.voyager_model.flattenLight()
        self.voyager_model.flattenStrong()
        self.render.prepareScene(self.win.getGsg())
        self.camera_joint.reparentTo(self.rootNode)
        self.blackHoleModel = self.circleModel.__copy__()
        self.blackHoleModel.setScale(60)
        self.blackHoleModel.setShaderInput("fadeDistance", 55)
        self.blackHoleModel.setShaderInput("fadeColor", Vec4(0, 0, 0, 1))
        self.blackHoleModel.setShaderInput("fadeCenter", Vec3(0, 0, 0))
        self.blackHoleModel.setName("black_hole")
        self.blackHoleModel.setColor(0, 0, 0, 1)
        self.wormholeModel = self.circleModel.__copy__()
        self.wormholeModel.setScale(25)
        self.wormholeModel.setShaderInput("fadeDistance", 21)
        self.wormholeModel.setShaderInput("fadeColor", Vec4(1, 0.05, 0.3, 1))
        self.wormholeModel.setShaderInput("fadeCenter", Vec3(0, 0, 0))
        self.wormholeModel.setName("wormhole")
        self.wormholeModel.setColor(1, 0.05, 0.3, 1)
        self.nebulaModel = self.circleModel.__copy__()
        self.nebulaModel.setScale(15)
        self.nebulaModel.setShaderInput("fadeDistance", 11)
        self.nebulaModel.setShaderInput("fadeColor", Vec4(0.5, 0.5, 1, 1))
        self.nebulaModel.setShaderInput("fadeCenter", Vec3(0, 0, 0))
        self.nebulaModel.setName("nebula")
        self.nebulaModel.setColor(0.5, 0.5, 1, 1)
        self.solarSystemModel = self.circleModel.__copy__()
        self.solarSystemModel.setScale(7)
        self.solarSystemModel.setShaderInput("fadeDistance", 5)
        self.solarSystemModel.setShaderInput("fadeColor", Vec4(1, 1, 1, 1))
        self.solarSystemModel.setShaderInput("fadeCenter", Vec3(0, 0, 0))
        self.solarSystemModel.setName("solar_system")
        self.solarSystemModel.setColor(1, 1, 1, 1)
        self.roguePlanetModel = self.circleModel.__copy__()
        self.roguePlanetModel.setScale(1.5)
        self.roguePlanetModel.setShaderInput("fadeDistance", 1)
        self.roguePlanetModel.setShaderInput("fadeColor", Vec4(0.6, 1, 0.8, 1))
        self.roguePlanetModel.setShaderInput("fadeCenter", Vec3(0, 0, 0))
        self.roguePlanetModel.setName("rogue_planet")
        self.roguePlanetModel.setColor(0.6, 1, 0.8, 1)
        self.render.setTransparency(TransparencyAttrib.MAlpha)
        self.object_ranges = [
            (start, end, model)
            for model, start, end in map_weights_to_range(
                [
                    [None, 50],
                    [self.solarSystemModel, 45 * 0.5],
                    [self.roguePlanetModel, 35 * 0.5],
                    [self.nebulaModel, 15 * 0.5],
                    [self.wormholeModel, 4 * 0.5],
                    [self.blackHoleModel, 1 * 0.5],
                ]
            )
            if model is not None
        ]
        self.WorldManager = WorldManager(
            WorldGen=self.worldGen,
            renderObject=self.rootNode,
            renderDistance=3,
        )
        self.renderedChunks = set()
        self.render.hide()

        # List containing objects and their percentage chance of spawning
        def renderTerrainThread():
            while True:
                self.renderTerrain()
                sleep(1 / 20)

        Thread(target=renderTerrainThread).start()
        self.alert.destroy()
        send_message("CLIENT_READY")
        for obstacle in self.obstaclesToPlace:
            if obstacle["name"] == "black_hole":
                instance = self.blackHoleModel.copyTo(self.render)
            elif obstacle["name"] == "wormhole":
                instance = self.wormholeModel.copyTo(self.render)
            elif obstacle["name"] == "nebula":
                instance = self.nebulaModel.copyTo(self.render)
            elif obstacle["name"] == "solar_system":
                instance = self.solarSystemModel.copyTo(self.render)
            elif obstacle["name"] == "rogue_planet":
                instance = self.roguePlanetModel.copyTo(self.render)
            instance.setPos(
                obstacle["position"][0],
                obstacle["position"][1],
                obstacle["position"][2],
            )
            instance.setHpr(
                obstacle["rotation"][0],
                obstacle["rotation"][1],
                obstacle["rotation"][2],
            )
            instance.setScale(
                obstacle["size"][0],
                obstacle["size"][1],
                obstacle["size"][2],
            )
            instance.setColorScale(
                obstacle["colorScale"][0],
                obstacle["colorScale"][1],
                obstacle["colorScale"][2],
                obstacle["colorScale"][3],
            )
            instance.setShaderInput("fadeCenter", Vec3(*obstacle["position"]))
            instance.setShaderInput("fadeDistance", obstacle["hitbox_scale"][0])
            instance.setShaderInput("fadeColor", Vec4(*obstacle["color"]))
            instance.setName(obstacle["name"])
            instance.setTransparency(TransparencyAttrib.MAlpha)
            send_message("NEW_OBJECT||+" + dumps(obstacle))
        send_message(
            "NEW_OBJECT||+"
            + dumps(
                {
                    "position": list(self.voyager_model.getPos()),
                    "rotation": [0, 0, 0],
                    "hitbox_scale": [1, 1, 1],
                    "hitbox_offset": [0, 0, 0],
                    "hitbox_type": "sphere",
                    "hitbox_geom": None,
                    "size": list(self.voyager_model.getScale()),
                    "id": "ship",
                    "name": "ship",
                    "color": [1, 1, 1, 1],
                    "colorScale": [1, 1, 1, 1],
                    "texture": None,
                    "texData": None,
                    "onHit": None,
                    "visible": True,
                    "colidable": True,
                }
            )
        )

    def start_simulation(self):
        print("CLIENT: Starting simulation...")
        self.render.show()
        self.taskMgr.doMethodLater(
            0.1, self.updateServerPositionData, "updateServerPositionData"
        )
        self.taskMgr.add(self.update, "updatePhysics")
        print("CLIENT: Rendering in progress")

    def update(self, task):
        self.physicsMgr.updateWorldPositions()
        rotVal = self.engineRingNode.getH()
        strength = self.engineRingNode.getColorScale()[3]
        # Get x and y components from rotVal (assuming rotVal is in degrees)
        rot_rad = math.radians(rotVal)
        x_component = math.cos(rot_rad)
        y_component = math.sin(rot_rad)
        velocity = self.physicsMgr.getObjectVelocity(self.rootNode, "ship")
        velocity_magnitude = math.sqrt(sum(v**2 for v in velocity))
        if strength > 0:
            if velocity_magnitude <= 0.001:
                self.physicsMgr.setObjectVelocity(
                    self.rootNode,
                    "ship",
                    [x_component * strength * 0.01, y_component * strength * 0.01, 0],
                )
            else:
                self.physicsMgr.addVectorForce(
                    self.rootNode,
                    "ship",
                    [
                        x_component * strength * 0.001,
                        y_component * strength * 0.001,
                        0,  # No vertical force
                    ],
                )
        return task.cont

    def create_new_object(self, data):
        position = Vec3(*data["position"])
        rotation = Vec3(*data["rotation"])
        hitbox_scale = Vec3(*data["hitbox_scale"])
        hitbox_offset = Vec3(*data["hitbox_offset"])

        if data["name"] == "black_hole":
            instance = self.blackHoleModel.copyTo(self.render)
        elif data["name"] == "wormhole":
            instance = self.wormholeModel.copyTo(self.render)
        elif data["name"] == "nebula":
            instance = self.nebulaModel.copyTo(self.render)
        elif data["name"] == "solar_system":
            instance = self.solarSystemModel.copyTo(self.render)
        elif data["name"] == "rogue_planet":
            instance = self.roguePlanetModel.copyTo(self.render)
        else:
            print(f"Unknown object name: {data['name']}")
            return

        instance.setPos(position)
        instance.setHpr(rotation)
        instance.setShaderInput("fadeCenter", position)
        instance.setShaderInput("fadeDistance", instance.getScale(self.render)[0])
        instance.setTransparency(TransparencyAttrib.MAlpha)
        data["size"] = list(instance.getScale(self.render))
        data["position"] = list(position)
        data["rotation"] = list(rotation)
        data["color"] = list(instance.getColor())
        data["colorScale"] = list(instance.getColorScale())
        send_message(
            "NEW_OBJECT||+" + dumps(data),
        )

    def renderTerrain(self):
        self.WorldManager.update()
        newChunks = self.WorldManager.newChunks - self.WorldManager.lastNewChunks

        for chunk in newChunks:
            xCoord, yCoord = chunk
            chunkData = self.worldGen.GENERATED_CHUNKS[chunk]

            xs = [row[0] for row in chunkData]
            ys = [row[1] for row in chunkData]
            points = [row[2] for row in chunkData]

            # Calculate world positions using voxel scale
            chunk_origin_x = xCoord * self.worldGen.CHUNK_SIZE * self.worldGen.VOX_SC
            chunk_origin_y = yCoord * self.worldGen.CHUNK_SIZE * self.worldGen.VOX_SC
            coords3D = [
                (
                    chunk_origin_x + xs[i] * self.worldGen.VOX_SC,
                    chunk_origin_y + ys[i] * self.worldGen.VOX_SC,
                    0,
                )
                for i in range(len(xs))
            ]
            pointIndices = [(p + 1) / 2 for p in points]

            # Only render points not already rendered
            not_rendered_mask = [coord not in self.renderedChunks for coord in coords3D]
            coords3D_filtered = [
                c for c, mask in zip(coords3D, not_rendered_mask) if mask
            ]
            pointIndices_filtered = [
                p for p, mask in zip(pointIndices, not_rendered_mask) if mask
            ]

            for i, coord3D in enumerate(coords3D_filtered):
                pointIndex = pointIndices_filtered[i]
                for start, end, model in self.object_ranges:
                    if start <= pointIndex < end:
                        instance = model.copyTo(self.render)
                        offset = (
                            10
                            + (
                                self.worldGen.get_noise_point(
                                    coord3D[0] * 100,
                                    coord3D[1] * 100,
                                    self.worldGen.seed,
                                )
                                + 2
                            )
                            * 50
                        )
                        instancePos = Vec3(
                            coord3D[0] + offset,
                            coord3D[1] + coord3D[1] % offset / 20,
                            random.uniform(-0.5, 0.5),
                        )
                        instance.setPos(instancePos)
                        instance.setShaderInput("fadeCenter", instancePos)
                        instance.setTransparency(TransparencyAttrib.MAlpha)

                        send_message(
                            "NEW_OBJECT||+"
                            + dumps(
                                {
                                    "position": list(instancePos),
                                    "rotation": [0, 0, 0],
                                    "hitbox_scale": [1, 1, 1],
                                    "hitbox_offset": [0, 0, 0],
                                    "hitbox_type": "sphere",
                                    "hitbox_geom": None,
                                    "size": list(model.getScale()),
                                    "id": "obstacle",
                                    "name": str(model.getName()),
                                    "color": list(model.getColor()),
                                    "colorScale": [1, 1, 1, 1],
                                    "texture": None,
                                    "texData": None,
                                    "onHit": None,
                                    "visible": True,
                                    "colidable": True,
                                }
                            )
                        )
                        break
                self.renderedChunks.add(coord3D)
            sleep(1 / 10)

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
        if config.startswith("set_seed_"):
            try:
                self.seed = int(config.split("set_seed_")[-1])
                self.worldGen.set_seed(self.seed)
                random.seed(self.seed)
                send_message("CLIENT_INFO||+SEED||+" + str(self.seed))
            except Exception as e:
                print(f"Error setting seed: {e}")
        if config.startswith("set_obstacles_"):
            try:
                obstacles = loads(config.split("set_obstacles_")[-1])
                self.obstaclesToPlace = obstacles
                print(f"CLIENT: Set obstacles to place: {self.obstaclesToPlace}")
            except Exception as e:
                print(f"Error setting obstacles: {e}")
        if config.startswith("set_targets_"):
            try:
                targets = loads(config.split("set_targets_")[-1])
                self.targetsToPlace = targets
                print(f"CLIENT: Set targets to place: {self.targetsToPlace}")
            except Exception as e:
                print(f"Error setting targets: {e}")

    def updateServerPositionData(self, task):
        send_message(
            "UPDATE_DATA||+"
            + dumps(
                {
                    "ship": {
                        "pos": [
                            self.rootNode.getX(),
                            self.rootNode.getY(),
                            self.rootNode.getZ(),
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
        yVal = -data[0]["z"] * 0.3 + self.camera.getY()
        if -10 >= yVal >= -100:
            self.camera.setPos(0, yVal, 0)
        # Clamp pitch to [-45, 45], wrap yaw to [0, 360)
        # If you want pitch to be only [0, 45] and [315, 360], remap accordingly:
        pitch = data[1]["pitch"] % 360

        # Calculate heading (h) from x and y
        x = data[0]["x"]
        y = data[0]["y"]
        heading = -math.degrees(math.atan2(x, y))
        self.engineRingNode.setH(heading + 180)
        self.engineRingNode.setColorScale(1, 1, 1, abs(x) + abs(y))
        # Clamp pitch to [0, 45] and [315, 360]
        if 0 <= pitch <= 35:
            mapped_pitch = pitch
        elif 270 <= pitch < 360:
            mapped_pitch = pitch
        elif pitch < 270 and pitch > 35:
            mapped_pitch = 270
        else:
            mapped_pitch = 35
        self.voyager_model.setHpr(
            (data[1]["yaw"] % 360),
            0,
            0,
        )
        self.camera_joint.setHpr(
            (data[1]["yaw"] % 360),
            mapped_pitch,
            0,
        )


def run_client():
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
    # loadPrcFileData("", f"want-pstats true")
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
