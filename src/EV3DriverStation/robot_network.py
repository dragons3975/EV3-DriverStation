import socket
import sys

from PySide6.QtCore import Property, QObject, QSettings, QTimer, Signal, Slot

from .controllers_manager import ControllersManager
from .robot import Robot, RobotMode


class RobotNetwork(QObject):
    availableIPs_changed = Signal()
    robotIP_changed = Signal(str)

    def __init__(self, robot: Robot, controllers: ControllersManager, refresh_rate_ms:int=30, ip: str | None = None):
        super().__init__()
        self.robot = robot
        self.controllers = controllers
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.udp_refresh_timer = QTimer(self)
        self.udp_refresh_timer.timeout.connect(self.send_udp)
        self.refresh_rate_ms = refresh_rate_ms

        self._available_ips: list = QSettings('EV3DriverStation').value('availableIPs', [])
        if 'localhost' not in self._available_ips:
            self.addIP('localhost')
        self._robot_ip = QSettings('EV3DriverStation').value('robotIP', '')
        if ip is not None:
            self.robotIP = ip

    @Property(list, notify=availableIPs_changed)
    def availableIPs(self) -> list[str]:
        return self._available_ips

    @Slot(str)
    def addIP(self, ip: str):
        if ip in self._available_ips:
            return

        self._available_ips.append(ip)
        self.availableIPs_changed.emit()
        QSettings('EV3DriverStation').setValue('availableIPs', self._available_ips)

    @Slot(str)
    def removeIP(self, ip: str):
        if ip == self._robot_ip:
            self.robotIP = ''
        self._available_ips.remove(ip)
        self.availableIPs_changed.emit()
        QSettings('EV3DriverStation').setValue('availableIPs', self._available_ips)

    @Property(str, notify=robotIP_changed)
    def robotIP(self):
        return self._robot_ip

    @robotIP.setter
    def robotIP(self, ip: str):
        self._robot_ip = ip
        self.robotIP_changed.emit(self._robot_ip)
        QSettings('EV3DriverStation').setValue('robotIP', self._robot_ip)

    @Slot()
    def send_udp(self):
        if self._robot_ip == '':
            return

        mode = 0 if not self.robot.enabled else {
            RobotMode.AUTO: 1,
            RobotMode.TELEOP: 2,
            RobotMode.TEST: 3
        }[self.robot.mode]

        message = mode.to_bytes(1, sys.byteorder)

        states = self.controllers.get_pilot_controllers_states()
        for state in states:
            message += state.as_bytes()
        try:
            self.udp_socket.sendto(message, (self._robot_ip, 5005))
        except socket.gaierror:
            print('Invalid IP: ' + self._robot_ip)
            self.removeIP(self._robot_ip)

    @property
    def refresh_rate_ms(self) -> int:
        return self._refresh_rate_ms

    @refresh_rate_ms.setter
    def refresh_rate_ms(self, value: int):
        self._refresh_rate_ms = int(round(value))
        self.udp_refresh_timer.setInterval(self._refresh_rate_ms)

    @Slot()
    def start_udp_refresh(self):
        self.udp_refresh_timer.start(self.refresh_rate_ms)

    @Slot()
    def stop_udp_refresh(self):
        self.udp_refresh_timer.stop()