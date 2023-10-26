__all__ = ['GuiApp']
import os
import sys

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

from .controllers import ControllersManager
from .network import RobotNetwork
from .robot import Robot
from .telemetry import Telemetry


class GuiApp(QGuiApplication):
    def __init__(self):
        super().__init__(sys.argv)

        self.setWindowIcon(QIcon(self.ui_path('icon.png')))
        
        self.app_status = AppStatus()
        self.app_status.panelChanged.connect(self.aknowledge_panel_changed)
        self.controllersManager = ControllersManager()
        self.robot = Robot(self.controllersManager.keyboard_controller)
        self.telemetry = Telemetry()
        self.robot_network = RobotNetwork(self.robot, self.controllersManager, self.telemetry)

        os.environ["QT_QUICK_CONTROLS_STYLE"] = "Material"
        os.environ["QT_QUICK_CONTROLS_MATERIAL_VARIANT"] = "Dense"
        os.environ["QT_QUICK_CONTROLS_MATERIAL_THEME"] = "Dark"
        os.environ["QT_QUICK_CONTROLS_MATERIAL_ACCENT"] = "LightBlue"
        os.environ["QT_QUICK_CONTROLS_MATERIAL_PRIMARY"] = "Indigo"

        self.engine = QQmlApplicationEngine()
        self.ctx = self.engine.rootContext()
        QQuickStyle.setStyle('Material')
        self.engine.exit.connect(self.quit)

    def exec(self):
        self.controllersManager.init_pygame()
        self.ctx.setContextProperty('app', self.app_status)
        self.ctx.setContextProperty('robot', self.robot)
        self.ctx.setContextProperty('telemetry', self.telemetry)
        self.ctx.setContextProperty('controllers', self.controllersManager)
        self.ctx.setContextProperty('network', self.robot_network)

        self.aknowledge_panel_changed(self.app_status.panel)

        self.engine.load(self.ui_path('main.qml'))

        r = super().exec_()
        # Delete the engine to avoid type errors when closing the program
        del self.engine

        self.robot_network.mute_udp_refresh = True
        self.robot.enabled = False
        self.robot_network.send_neutral_udp()
        self.robot_network.close()
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