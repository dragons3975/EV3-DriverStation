from time import sleep, time

from EV3DriverStation.controllers import ControllersManager, ControllerState
from EV3DriverStation.network import RobotNetwork
from EV3DriverStation.robot import Robot, RobotMode


class RobotAPI:
    def __init__(self, ip: str):
        self.controllers = ControllersManager()
        self.robot = Robot(self.controllers.keyboard_controller)    
        self.network = RobotNetwork(self.robot, self.controllers, refresh_rate_ms=30, ip=ip)
        self.robot.mode = RobotMode.TELEOP
        self.robot.enabled = True
        self.send_neutral()

    def send_during(self, seconds: float, repeat_ms: int = None):
        if repeat_ms is None:
            self.network.send_udp()
            sleep(seconds)
        else:
            t = time()
            while time() - t < seconds:
                self.network.send_udp()
                sleep(repeat_ms / 1000)
        self.send_neutral()

    def avance(self, temps: float, puissance:float=1):
        self.controllers._pilot1State = ControllerState(leftY=-puissance)
        self.controllers._pilot2State = ControllerState()
        self.send_during(temps)

    def recule(self, temps: float, puissance:float=1):
        self.controllers._pilot1State = ControllerState(leftY=puissance)
        self.controllers._pilot2State = ControllerState()
        self.send_during(temps)

    def tourne_gauche(self, temps: float=1, puissance:float =.7):
        self.controllers._pilot1State = ControllerState(rightX=-puissance)
        self.controllers._pilot2State = ControllerState()
        self.send_during(temps)

    def tourne_droite(self, temps: float=1, puissance:float =.7):
        self.controllers._pilot1State = ControllerState(rightX=puissance)
        self.controllers._pilot2State = ControllerState()
        self.send_during(temps)

    def send_neutral(self):
        self.controllers._pilot1State = ControllerState()
        self.controllers._pilot2State = ControllerState()
        self.network.send_udp()
