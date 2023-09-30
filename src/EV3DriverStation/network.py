from __future__ import annotations

import ctypes
import json
import socket
import struct
import sys
import threading
import time
import traceback
from enum import Enum
from os import path
from tempfile import SpooledTemporaryFile

from fabric import Connection as SSHConnection
from icmplib import ping
from invoke.exceptions import CommandTimedOut
from paramiko.ssh_exception import AuthenticationException, NoValidConnectionsError
from PySide6.QtCore import Property, QObject, QSettings, QTimer, Signal, Slot

from .controllers import ControllersManager, ControllerState
from .robot import Robot, RobotMode
from .telemetry import Telemetry


class RobotNetwork(QObject):
    def __init__(self, robot: Robot, controllers: ControllersManager, telemetry: Telemetry, max_refresh_rate:int=30, address: str | None = None):
        super().__init__()
        self.robot = robot
        self.controllers = controllers
        self.telemetry = telemetry

        # Properties
        self._robot_address = ''
        self._connection_status = ConnectionStatus.DISCONNECTED
        self._signal_strength = 0
        self._ping = 0
        self._available_addresses = [_ for _ in QSettings('EV3DriverStation').value('availableAddresses', []) if _ != '']
        if len(self._available_addresses) == 0:
            self.addAddress('localhost')

        # SSH Communication
        self._ssh_thread: threading.Thread = None
        self._ssh: SSHConnection = None
        
        self.connectionFailed.connect(self.disconnectRobot)
        self.connectionLost.connect(self.disconnectRobot)

        # self.connectionSucceed.connect(self.telemetry.connect_network_tables)
        # self.disconnected.connect(self.telemetry.clear_and_disconnect)

        # Udp Communication
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._mute_udp_refresh = False

        self._udp_sent_count = 0
        self._udp_avg_dt = 0
        self._udp_sent_count_timer = QTimer(self)
        self._udp_sent_count_timer.timeout.connect(self.refresh_udp_avg_dt)
        self._udp_sent_count_timer.start(500)

        self._max_udp_refresh_timer = QTimer(self)
        self._max_udp_refresh_timer.setSingleShot(True)
        self._max_udp_refresh_rate = 0

        controllers.statesChanged.connect(self.udp_refresh)
        self._max_udp_refresh_timer.timeout.connect(self.udp_refresh)

        self.maxUdpRefreshRate = max_refresh_rate    # This line starts the max_udp_refresh_timer

        # Initialize connection
        if address is None:
            address = QSettings('EV3DriverStation').value('robotAddress', '')
        self.connectRobot(address)

    #=================#
    #== UDP Message ==#
    #=================#
    def send_udp(self, force_controller_neutral: bool = False):
        host = self.robot_host
        if host == '':
            return
        
        mode = 0 if not self.robot.enabled else {
            RobotMode.AUTO: 1,
            RobotMode.TELEOP: 2,
            RobotMode.TEST: 3
        }[self.robot.mode]

        message = mode.to_bytes(1, sys.byteorder)

        if force_controller_neutral:
            states = [ControllerState()] * 2
        else:
            states = self.controllers.get_pilot_controllers_states()

        for state in states:
            axis_msg = struct.pack("f"*6, *state.axis)
            buttons = 0
            for i, b in enumerate(state.buttons):
                buttons |= b << i
            message += axis_msg + struct.pack("i", buttons)

        try:
            self.udp_socket.sendto(message, (host, 5005))
        except socket.gaierror:
            print("Impossible to send UDP message: invalid robot address.")
            traceback.print_exc()
            return False
        else:
            return True

    #================#
    #== Main Slots ==#
    #================#
    @Slot(str)
    def connectRobot(self, address: str):
        if address == self._robot_address:
            return
        self.disconnectRobot()
        if address != '':
            self._set_robotAddress(address)
            if address == 'localhost':
                self._set_connection_status(ConnectionStatus.CONNECTED)
                self.connectionSucceed.emit('localhost')
                self._set_signalStrength(5, 0)
            else:
                self.ssh_start()

    connectionFailed = Signal(str, str)
    connectionLost = Signal(str, str)
    connectionSucceed = Signal(str)

    disconnected = Signal()

    @Slot()
    def disconnectRobot(self, save_disconnect: bool = True):
        self._set_robotAddress('', save=save_disconnect)
        self.ssh_kill()
        self._set_connection_status(ConnectionStatus.DISCONNECTED)
        self._set_signalStrength(0, 0)
        self.telemetry.clear_and_disconnect()
        self.disconnected.emit()

    def close(self):
        self.disconnectRobot(save_disconnect=False)
        self.udp_socket.close()

    @Slot()
    def udp_refresh(self) -> None:
        self._max_udp_refresh_timer.stop()

        if not self.muteUdpRefresh:
            self._udp_sent_count += 1
            
            succeed = self.send_udp()
        else:
            succeed = True

        if not succeed: 
            self.connectionLost.emit(self._ssh.host, 'Impossible to send UDP message. See console for more details.')
            self.disconnectRobot()
        self._max_udp_refresh_timer.start(self._max_udp_refresh_rate)

    #=======================#
    #== SSH Communication ==#
    #=======================#
    def ssh_start(self) -> None:
        self._ssh_thread = threading.Thread(target=self.ssh_run, args=(self._robot_address,))
        self._ssh_thread.start()

    def ssh_kill(self) -> None:
        if self._ssh_thread is  None:
            return
        
        # Kill thread
        thread_id = 0
        for i, thread in threading._active.items():
            if thread is self._ssh_thread:
                thread_id = i
                break
        else:
            return
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), ctypes.py_object(SystemExit))

        # Wait for thread to stop
        self._ssh_thread.join()
        self._ssh_thread = None
        self._ssh = None

    def ssh_run(self, address: str):
        ssh = self.ssh_connect(address)
        try:
            if ssh is None:
                return
            self._ssh = ssh

            lostConnexionReason = self.refresh_ssh_status()

            while not lostConnexionReason:
                if not self.refresh_signal_strength():
                    lostConnexionReason = "Robot didn't respond to ping in time."
                    break
                
                # Pull telemetry for 2.5 seconds
                time.sleep(.5)
                for _ in range(4):
                    self.pull_telemetry()
                    time.sleep(.5)

                # Refresh ping and signal strength
                if not self.refresh_signal_strength():
                    lostConnexionReason = "Robot didn't respond to ping in time."
                    break

                # Pull telemetry for 1 seconds
                time.sleep(.5)
                self.pull_telemetry()
                time.sleep(.5)

                # Refresh robot status
                lostConnexionReason = self.refresh_ssh_status()
                if lostConnexionReason:
                    break
                
                # Pull telemetry for 1 seconds
                time.sleep(.5)
                self.pull_telemetry()
                time.sleep(.5)

            self.connectionLost.emit(self._ssh.host, lostConnexionReason)

        except SystemError:
            pass
        except Exception:
            self.connectionLost.emit(self._ssh.host, 
            'An error occured when communicating with the robot. Check the console for more details.')
            print("An error occured when communicating with the robot.")
            traceback.print_exc()
        finally:
            if self._ssh is not None:
                self._ssh.run('rm -f robot.lock')
                self._ssh.close()
                self._ssh = None

    def ssh_connect(self, host: str) -> SSHConnection | None:
        MAX_LOCK_AGE = 10

        # === Parse host address ===
        if '@' in host:
            username, host = host.split('@', 1)
            if ':' in username:
                username, password = username.split(':', 1)
            else:
                password = ''
        else:
            username = 'robot'
            password = 'maker'
        if ':' in host:
            host, port = host.split(':', 1)
        else:
            port = '22'
        
        # === Initiate SSH Connection ===
        self._set_connection_status(ConnectionStatus.AUTH)
        try:
            ssh = SSHConnection(f"{username}@{host}:{port}", connect_timeout=30,
                                connect_kwargs=dict(password= password))
            ssh.open()
        except TimeoutError:
            self.connectionFailed.emit(ConnectionFailedReason.UNREACHABLE, 
                                       f'Invalid robot address: <i>{host}</i>. (Or robot is too busy)')
            return None
        except NoValidConnectionsError:
            self.connectionFailed.emit(ConnectionFailedReason.UNREACHABLE, 
                                       f'Invalid robot address: <i>{host}:{port}</i>.')
            return None
        except AuthenticationException:
            self.connectionFailed.emit(ConnectionFailedReason.AUTH, f'Impossible to login to the robot with '
                                                                f'username: "{username}" and password: "{password}".')
            return None
        except Exception:
            msg = f'Error when connecting to the robot at <i>{host}:{port}</i>'
            msg +=f' with username: "{username}" and password: "{password}".'
            print(msg)
            traceback.print_exc()
            self.connectionFailed.emit(ConnectionFailedReason.AUTH, msg+"\nCheck the console for more details.")
            return None

        def ssh_run(cmd):
            return ssh.run(cmd, hide=True, warn=True, timeout=5)


        try:
            # === Check if robot is already connected to another Driver Station ===
            self._set_connection_status(ConnectionStatus.CHECK_AVAILABLE)

            def get_lock_date():
                """
                Read the date of the last modification of the lock file on the robot.
                """
                lock_stat = ssh_run("stat robot.lock -c %Y")
                if lock_stat.exited != 0:
                    return 0
                return float(lock_stat.stdout)

            # Read lock file and system date on the robot
            lock_date = get_lock_date()
            robot_date = float(ssh_run("date +%s").stdout)   

            # If the lock file is not older than MAX_LOCK_AGE...
            if robot_date - lock_date <= MAX_LOCK_AGE:
                self._set_connection_status(ConnectionStatus.WAIT_AVAILABLE)
                time.sleep(MAX_LOCK_AGE)            # ...wait for MAX_LOCK_AGE seconds...
                new_lock_date = get_lock_date()     # ...and check again the lock file date.
                if new_lock_date != lock_date and new_lock_date != 0:
                    # If the lock file has been modified, it means that another Driver Station is using the robot.
                    # then read the hostname of the computer that locked the robot.
                    lock_host = ssh_run("cat robot.lock").stdout.strip()
                    if lock_host == '':
                        lock_host = 'an unknown device'
                    elif lock_host == socket.gethostname():
                        lock_host = 'this computer. Another instance of EV3DriverStation is probably already started.'
                    else:
                        lock_host = f'<i>{lock_host}</i>'
                    # Then, close the SSH connection and emit a signal to inform the user.
                    ssh.close()
                    self.connectionFailed.emit(ConnectionFailedReason.LOCKED, 
                                                    f"The robot is already used by {lock_host}.")
                    return None

            # === Write lock file ===
            ssh_run(f'echo "{socket.gethostname()}" > robot.lock')

            # === Push DS.sh script to the robot ===
            self._set_connection_status(ConnectionStatus.SETUP)
            local_path = path.join(path.abspath(path.dirname(__file__)), 'DS.sh')
            ssh.put(local_path, 'DS.sh')
            status = ssh_run('chmod +x DS.sh')
            if status.stderr:
                ssh.close()
                self.connectionFailed.emit(ConnectionFailedReason.SETUP, 
                                           "Impossible to make DriverStation script executable on the robot.")
                return None
            
        except SystemExit:
            ssh.close()
            return None
        except Exception as e:
            ssh.close()
            print("An error occured when connecting to the robot.")
            traceback.print_exc()          
            self.connectionFailed.emit(ConnectionFailedReason.RUNTIME, str(e))
            return None

        # Robot is ready!
        self._set_connection_status(ConnectionStatus.CONNECTED)
        self.connectionSucceed.emit(ssh.host)
        return ssh

    def refresh_ssh_status(self) -> bool:
        if not self._ssh.is_connected:
            return "SSH connection with the robot has been lost."

        try:
            status = self._ssh.run('./DS.sh', hide=True, warn=True, timeout=3)
        except CommandTimedOut:
            return False
        if status.stderr:
            print("Error when running the SSH script:")
            print(status.stderr)
            return "SSH script returned an error."

        self.telemetry.refresh_robot_status(status.stdout)

        return False

    def refresh_signal_strength(self) -> bool:
        strength, avg_ping = self.get_signal_strength(self._ssh.host)
        self._set_signalStrength(strength, avg_ping)
        return strength > 0

    def get_signal_strength(self, host: str) -> bool:
        ping_result = ping(host, count=3, interval=.1, timeout=1)

        if not ping_result.is_alive:
            strength = 0
        elif ping_result.max_rtt <= 30 and ping_result.packet_loss == 0:
            strength = 5    # No packet loss and max ping < 30ms
        elif ping_result.avg_rtt <= 30 and ping_result.packet_loss == 0:
            strength = 4    # No packet loss and mean ping < 30ms
        elif ping_result.avg_rtt <= 120 and ping_result.packet_loss <= 1:
            strength = 3    # Packet loss <= 1/3 and mean ping < 120ms
        elif ping_result.avg_rtt <= 500:
            strength = 2    # Packet loss <= 2/3 and mean ping < 500ms
        else:
            strength = 1    # Packet loss <= 2/3 and mean ping >= 500ms
        return strength, ping_result.avg_rtt

    #====================#
    #== QML PROPERTIES ==#
    #====================#
    # --- Robot IP --- #
    robotAddress_changed = Signal(str)
    @Property(str, notify=robotAddress_changed)
    def robotAddress(self):
        return self._robot_address

    def _set_robotAddress(self, address: str, save=True):
        self._robot_address = address
        self.robotAddress_changed.emit(address)
        if save:
            QSettings('EV3DriverStation').setValue('robotAddress', self._robot_address)

    @property
    def robot_host(self):
        if self._robot_address == 'localhost':
            return 'localhost'
        elif self._ssh is None:
            return ''
        else:
            return self._ssh.host

    # --- Connection Status --- #
    connectionStatus_changed = Signal(str)
    @Property(str, notify=connectionStatus_changed)
    def connectionStatus(self):
        return self._connection_status

    def _set_connection_status(self, status: str):
        if status != self._connection_status and status in ConnectionStatus:
            mute_udp_refresh = self.muteUdpRefresh
            self._connection_status = status
            self.connectionStatus_changed.emit(status)

            if mute_udp_refresh != self.muteUdpRefresh:
                self.muteUdpRefresh_changed.emit(self.muteUdpRefresh)

    # --- Signal Strength --- #
    signalStrength_changed = Signal(int)
    @Property(int, notify=signalStrength_changed)
    def signalStrength(self):
        return self._signal_strength

    ping_changed = Signal(int)
    @Property(int, notify=ping_changed)
    def ping(self):
        return self._ping

    def _set_signalStrength(self, strength: int, ping: int = None):
        if ping is not None and ping != self._ping:
            self._ping = ping
            self.ping_changed.emit(ping)
        if strength != self._signal_strength:
            self._signal_strength = strength
            self.signalStrength_changed.emit(strength)

    def pull_telemetry(self):
        if self._ssh is None:
            return
        with SpooledTemporaryFile() as f:
            try:
                self._ssh.get('/run/user/1000/telemetry.json', f)
                f.seek(0)
                data = f.read()
                if data:
                    self.telemetry.set_telemetry_data(json.loads(data))
            except IOError:
                pass
            except:
                print("An error occured when pulling telemetry from the robot.")
                traceback.print_exc()

    # --- IPs List --- #
    availableAddresses_changed = Signal()
    @Property(list, notify=availableAddresses_changed)
    def availableAddresses(self) -> list[str]:
        return self._available_addresses

    @Slot(str)
    def addAddress(self, address: str):
        if address in self._available_addresses:
            return

        self._available_addresses.append(address)
        self.availableAddresses_changed.emit()
        QSettings('EV3DriverStation').setValue('availableAddresses', self._available_addresses)

    @Slot(str)
    def removeAddress(self, address: str):
        if address == self._robot_address:
            self.robotAddress = ''
        self._available_addresses.remove(address)
        self.availableAddresses_changed.emit()
        QSettings('EV3DriverStation').setValue('availableAddresses', self._available_addresses)   

    # --- Max UDP Refresh Rate --- #
    maxUdpRefreshRate_changed = Signal(int)
    @Property(int, notify=maxUdpRefreshRate_changed)
    def maxUdpRefreshRate(self) -> int:
        return self._max_udp_refresh_rate

    @maxUdpRefreshRate.setter
    def maxUdpRefreshRate(self, value: int):
        t = int(round(value))
        if t == self._max_udp_refresh_rate:
            return

        self._max_udp_refresh_rate = t
        self._max_udp_refresh_timer.stop()

        if t > 0:
            self._max_udp_refresh_timer.start(t)

        self.maxUdpRefreshRate_changed.emit(t)

    # --- Mute UDP Refresh --- #
    muteUdpRefresh_changed = Signal(bool)
    @Property(bool, notify=muteUdpRefresh_changed)
    def muteUdpRefresh(self) -> bool:
        return self._connection_status != ConnectionStatus.CONNECTED or self._mute_udp_refresh

    @muteUdpRefresh.setter
    def muteUdpRefresh(self, value: bool):
        mute_udp_refresh = self.muteUdpRefresh
        self._mute_udp_refresh = value
        if mute_udp_refresh != self.muteUdpRefresh:
            self.muteUdpRefresh_changed.emit(value)

    # --- UDP Avg dt --- #
    udpAvgDt_changed = Signal(int)
    @Property(int, notify=udpAvgDt_changed)
    def udpAvgDt(self) -> int:
        return self._udp_avg_dt

    @Slot()
    def refresh_udp_avg_dt(self) -> None:
        self._udp_avg_dt = 0 if self._udp_sent_count == 0 else 500 / self._udp_sent_count
        self.udpAvgDt_changed.emit(self._udp_avg_dt)
        self._udp_sent_count = 0


class ConnectionStatus(str, Enum):
    CONNECTED = 'Connected'
    AUTH = 'Authenticating'
    CHECK_AVAILABLE = 'Check Available'
    WAIT_AVAILABLE = 'Wait Available'
    SETUP = 'Setuping'
    DISCONNECTED = 'Disconnected'

    @classmethod
    def __contains__(cls, item):
        return item in cls.__members__.values()


class ConnectionFailedReason(str, Enum):
    UNREACHABLE = 'Unreachable'
    AUTH = 'Authentication'
    LOCKED = 'Locked'
    SETUP = 'Setup'
    RUNTIME = 'Runtime'

    @classmethod
    def __contains__(cls, item):
        return item in cls.__members__.values()