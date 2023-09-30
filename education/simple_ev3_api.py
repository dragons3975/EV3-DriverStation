import traceback
from time import sleep, time

from EV3DriverStation import ControllersManager, ControllerState, Robot, RobotMode, RobotNetwork, Telemetry


class RobotAPI:
    def __init__(self, ip: str, refresh_udp=50):
        self.controllers = ControllersManager()
        self.robot = Robot(self.controllers.keyboard_controller)   
        self.telemetry = Telemetry() 
        print("Connecting to robot")
        self.network = RobotNetwork(self.robot, self.controllers, self.telemetry, address=ip, 
                                    pull_telemetry_rate=refresh_udp*2)
        while self.network.connectionStatus != "Connected":
            sleep(.1)
            if self.network.connectionStatus == "Disconected":
                raise RuntimeError("Impossible to connect on robot")
        print("Robot connected")
        self.robot.mode = RobotMode.TELEOP
        self.robot.enabled = True

        self.refresh_udp = refresh_udp

        self.send_neutral()

    def __del__(self):
        self.disconnect()

    def disconnect(self):
        self.send_neutral()
        self.network.disconnectRobot()

    def send_during(self, dt: float, repeat_ms: int = None):
        try:
            if repeat_ms is None:
                self.network.send_udp()
                sleep(dt)
            else:
                t0 = time()
                while t0 + dt > time():
                    self.network.send_udp()
                    sleep(min(repeat_ms / 1000, (t0 + dt)-time()))
        except:
            traceback.print_exc()
        self.send_neutral()

    def avance(self, temps: float, puissance:float=1):
        self.controllers._pilot1State = ControllerState(leftY=-puissance)
        self.controllers._pilot2State = ControllerState()
        self.send_during(temps, self.refresh_udp)

    def recule(self, temps: float, puissance:float=1):
        self.controllers._pilot1State = ControllerState(leftY=puissance)
        self.controllers._pilot2State = ControllerState()
        self.send_during(temps, self.refresh_udp)

    def tourne_gauche(self, temps: float=1, puissance:float =.7):
        self.controllers._pilot1State = ControllerState(rightX=-puissance)
        self.controllers._pilot2State = ControllerState()
        self.send_during(temps, self.refresh_udp)

    def tourne_droite(self, temps: float=1, puissance:float =.7):
        self.controllers._pilot1State = ControllerState(rightX=puissance)
        self.controllers._pilot2State = ControllerState()
        self.send_during(temps, self.refresh_udp)

    def send_neutral(self):
        self.controllers._pilot1State = ControllerState()
        self.controllers._pilot2State = ControllerState()
        self.network.send_udp()

    @property
    def positionMoteur1(self):
        return self.telemetry._telemetryData['moteurL']

    @property
    def positionMoteur2(self):
        return self.telemetry._telemetryData['moteurR']

    @property
    def capteurCouleur(self):
        return self.telemetry._telemetryData['color']

    @property
    def capteurTactile(self):
        return self.telemetry._telemetryData['touch'] == 1
