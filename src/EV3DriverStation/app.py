__all__ = ['GuiApp']
import os
import sys

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

from .controllers_manager import ControllersManager
from .robot import Robot
from .robot_network import RobotNetwork


class GuiApp(QGuiApplication):
    def __init__(self):
        super().__init__(sys.argv)

        self.setWindowIcon(QIcon(self.ui_path('icon.png')))

        self.engine = QQmlApplicationEngine()
        self.ctx = self.engine.rootContext()
        
        self.app_status = AppStatus()
        self.app_status.panelChanged.connect(self.aknowledge_panel_changed)
        self.controllersManager = ControllersManager()
        self.robot = Robot(self.controllersManager.keyboard_controller)
        self.robot_network = RobotNetwork(self.robot, self.controllersManager)

        QQuickStyle.setStyle('Material')
        self.engine.quit.connect(self.quit)
        

    def exec(self):
        self.controllersManager.init_pygame()
        self.robot_network.start_udp_refresh()
        self.ctx.setContextProperty('app', self.app_status)
        self.ctx.setContextProperty('controllers', self.controllersManager)
        self.ctx.setContextProperty('robot', self.robot)
        self.ctx.setContextProperty('network', self.robot_network)
        self.aknowledge_panel_changed(self.app_status.panel)

        self.engine.load(self.ui_path('main.qml'))

        r = super().exec_()

        self.robot_network.stop_udp_refresh()
        self.robot.enabled = False
        self.robot_network.send_udp()
        self.controllersManager.quit_pygame()
        return r

    def send_controllers_state(self):
        states = [c.state for c in self.controllersManager.controllers]
        self.robot.send_udp(states)

    @Slot(str)
    def aknowledge_panel_changed(self, panel):
        self.robot.capture_keyboard = panel in ("Robot", "Controllers")

    @staticmethod
    def ui_path(path):
        return os.path.abspath(os.path.dirname(__file__)) + '/ui/' + path


class AppStatus(QObject):
    panelChanged = Signal(str)
    def __init__(self):
        super().__init__()
        self._panel = "Robot"

    @Property(str, notify=panelChanged)
    def panel(self):
        return self._panel

    @panel.setter
    def panel(self, value):
        self._panel = value
        self.panelChanged.emit(self._panel)