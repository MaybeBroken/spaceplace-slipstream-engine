from panda3d.core import *
from panda3d.core import loadPrcFileData
from direct.showbase.ShowBase import ShowBase

prc_data = """
window-title Test
load-display pandagl
aux-display p3tinydisplay
aux-display pandadx9
aux-display pandadx8
"""
loadPrcFileData("", prc_data)


class mainWindow(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.set_background_color(0, 0, 0, 1)
        import asyncio


root = mainWindow()
root.run()
