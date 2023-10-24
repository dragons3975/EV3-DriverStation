from __future__ import annotations

import ctypes
import socket
import struct
import sys
import threading
import time
import traceback
from enum import Enum
from os import path
from typing import NamedTuple

from fabric import Config as SSHConfig
from fabric import Connection as SSHConnection
from icmplib import ping
from invoke.exceptions import CommandTimedOut
from paramiko.ssh_exception import AuthenticationException, NoValidConnectionsError
from PySide6.QtCore import Property, QObject, QSettings, QTimer, Signal, Slot

from .controllers import ControllersManager, ControllerState
from .robot import ProgramStatus, Robot, RobotMode, RobotStatus
from .telemetry import Telemetry

UDP_ROBOT_PORT = 5005

WINDOWS_LINE_ENDING = b'\r\n'
UNIX_LINE_ENDING = b'\n'
LOCK_PATH = "robot.lock"
SCRIPT_CWD = "/run/user/1000/"

PING_TIMEOUT = 5 # s before robot is considered disconnected
UDP_RESPONSE_TIMEOUT = 6 # s before program is considered crashed

class RobotNetwork(QObject):
    def __init__(self, robot: Robot, controllers: ControllersManager, telemetry: Telemetry, 
                 address: str | None = None, pull_telemetry_rate: int = 500):
        super().__init__()
        self.robot = robot
        self.controllers = controllers
        self.telemetry = telemetry

        # Properties
        self._robot_address = ''
        self._connection_status = ConnectionStatus.DISCONNECTED
        self._signal_strength = 0
        self._ping = 0
        self._available_addresses = [_ for _ in QSettings('EV3DriverStation').value('availableAddresses', []) 
                                     if _ != '']
        if len(self._available_addresses) == 0:
            self.addAddress('localhost')

        # SSH Communication
        self._ssh_thread: threading.Thread = None
        self._ssh: SSHConnection = None
        self._pull_telemetry_rate = pull_telemetry_rate
        self._request_program_date = threading.Event()
        
        self.connectionFailed.connect(self.disconnectRobot)
        self.connectionLost.connect(self.disconnectRobot)
        self.robot.programStarting.connect(self._request_program_date.set)

        # Udp Communication
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._mute_udp_refresh = False

        self._last_udp_t = None
        self._udp_avg_dt = 0

        self._min_udp_refresh_timer = QTimer(self)
        self._min_udp_refresh_timer.setSingleShot(True)
        self._max_udp_refresh_timer = QTimer(self)
        self._max_udp_refresh_timer.setSingleShot(True)
        self._min_udp_refresh_timer.timeout.connect(self.udp_refresh)
        self._max_udp_refresh_timer.timeout.connect(self.udp_refresh)
        self._last_udp_state: DriverStationState = None    

        self._udp_response_watchdog = QTimer(self)
        self._udp_response_watchdog.setSingleShot(True)
        self._udp_response_watchdog.timeout.connect(self._udp_response_watchdog_timedout)
        self._udp_response_watchdog.setInterval(UDP_RESPONSE_TIMEOUT*1000)
        self.clearUdpResponseWatchdog.connect(self._udp_response_watchdog.stop)
        self._ask_full_telemetry = threading.Event()

        self._udp_refresh_rates = RefreshRates()
        self._udp_refresh_mode = None
        self._update_udp_refresh_mode()
        self.robot.robotStatus_changed.connect(self._update_udp_refresh_mode)
        self.robot.mode_changed.connect(self._update_udp_refresh_mode)

        # Initialize connection
        if address is None:
            address = QSettings('EV3DriverStation').value('robotAddress', '')
        self.connectRobot(address)

    #=================#
    #== UDP Message ==#
    #=================#
    def send_udp(self, udp_state: DriverStationState = None):
        host = self.robot_host
        if host == '':
            return

        if self.robot.programStatus != ProgramStatus.IDLE:
            if udp_state is None:
                udp_state = self.fetch_ds_state(refresh=False)
            
            mode = 0 if not udp_state.enabled else {
                RobotMode.AUTO: 1,
                RobotMode.TELEOP: 2,
                RobotMode.TEST: 3
            }[udp_state.mode]

            if self._ask_full_telemetry.is_set():
                self._ask_full_telemetry.clear()
                mode |= 0x80

            message = mode.to_bytes(1, sys.byteorder)

            for state in udp_state.contollers:
                axis_msg = struct.pack("b"*6, *[int(a*125) for a in state.axis])
                message += axis_msg + struct.pack("i", state.buttons_as_int())

        else:
            # If no program is running, send a hello message asking for the full telemetry
            message = b'\x88'

        try:
            self.udp_socket.sendto(message, (host, UDP_ROBOT_PORT))
        except socket.gaierror:
            print("Impossible to send UDP message: invalid robot address.")
            traceback.print_exc()
            return False
        else:
            if not self._udp_response_watchdog.isActive():
                self._udp_response_watchdog.start()
            return True

    def send_neutral_udp(self):
        udp_state = DriverStationState(enabled=self.robot.enabled, mode=self.robot.mode)
        self.send_udp(udp_state)

    def parse_udp_response(self, response):
        mode = response[0]
        starting = (mode & 0x04) != 0

        mode = mode & 0x03
        if mode == 0:
            enabled = False
            mode = self.robot.mode
        else:
            enabled = True
            mode = RobotMode.from_index(mode)

        if starting:
            self.robot.set_program_status(ProgramStatus.STARTING)
        else:
            if self.robot.programStatus == ProgramStatus.IDLE:
                self.robot.mode = mode
                self.robot.enabled = enabled
            self.robot.set_program_status(ProgramStatus.RUNNING)

        skipped_frame = int(response[1])
        self.telemetry.put_skipped_frame(skipped_frame)

        frame_exec_time = int(response[2])
        if frame_exec_time > 0:
            self.telemetry.put_frame_exec_time(frame_exec_time)
        
        telemetry_data = response[3:]
        if telemetry_data:
            if not self.telemetry.parse_udp_response(telemetry_data):
                self._ask_full_telemetry.set()

    clearUdpResponseWatchdog = Signal()
    def _udp_response_watchdog_timedout(self):
        self.robot.set_program_status(ProgramStatus.IDLE)
        self.telemetry.clear_program_data()


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
                self.handleConnectionSuccess()
                self._set_signalStrength(5, 0)
            else:
                self.ssh_start()

    @Slot()
    def handleConnectionSuccess(self):
        self._set_connection_status(ConnectionStatus.CONNECTED)
        self.connectionSucceed.emit('localhost')
        threading.Thread(target=self.listen_udp_run).start()


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
        self.robot.set_program_status(ProgramStatus.IDLE)
        self.telemetry.clear()
        self._udp_avg_dt = 0
        self._last_udp_t = None
        self.udpAvgDt_changed.emit(0)
        self.disconnected.emit()

    def close(self):
        self.disconnectRobot(save_disconnect=False)
        self.udp_socket.close()

    @Slot()
    def udp_refresh(self) -> None:
        udp_state = self.fetch_ds_state()
        min_refresh = self.sender() is self._min_udp_refresh_timer
        if min_refresh and udp_state.is_same(self._last_udp_state):
            return

        self._max_udp_refresh_timer.stop()
        self._min_udp_refresh_timer.stop()

        if not self.muteUdpRefresh:
            self.tick_udp_avg_dt()
            succeed = self.send_udp(udp_state)
            self._last_udp_state = udp_state
        else:
            succeed = True

        if not succeed: 
            self.connectionLost.emit(self.robot_host, 'Impossible to send UDP message. See console for more details.')
            self.disconnectRobot()
        
        self._set_udp_refresh_timers_intervals(minRate=self.minUdpRefreshRate, maxRate=self.maxUdpRefreshRate)


    def fetch_ds_state(self, refresh=True) -> DriverStationState:
        pilot1, pilot2 = self.controllers.get_pilot_controllers_states(refresh=refresh)
        return DriverStationState(controller1=pilot1, controller2=pilot2, 
                        enabled=self.robot.enabled, mode=self.robot.mode)

    def listen_udp_run(self):
        self.udp_socket.settimeout(0.1)
        while self._connection_status == ConnectionStatus.CONNECTED:
            try:
                data, addr = self.udp_socket.recvfrom(2048)
            except socket.timeout:
                pass
            except OSError:
                continue
            except Exception:
                print("An error occured when receiving UDP message.")
                traceback.print_exc()
            else:
                if addr[0] == self.robot_host or (addr[0] == '127.0.0.1' and self.robot_host=='localhost'):
                    self.clearUdpResponseWatchdog.emit()
                    self.parse_udp_response(data)

    #=======================#
    #== SSH Communication ==#
    #=======================#
    def ssh_start(self) -> None:
        self._ssh_thread = threading.Thread(target=self.ssh_loop, args=(self._robot_address,))
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

    def ssh_loop(self, address: str):
        ssh = self.ssh_connect(address)

        try:
            if ssh is None:
                return
            self._ssh = ssh

            self.handleConnectionSuccess()

            self.handleConnectionSuccess()

            lostConnexionReason = self.refresh_ssh_status()

            while not lostConnexionReason:
                if not self.refresh_signal_strength():
                    lostConnexionReason = "Robot didn't respond to ping in time."
                    break
                
                time.sleep(2)

                # Refresh ping and signal strength
                if not self.refresh_signal_strength():
                    lostConnexionReason = "Robot didn't respond to ping in time."
                    break

                time.sleep(1)
                
                # Refresh robot status
                lostConnexionReason = self.refresh_ssh_status()
                if lostConnexionReason:
                   break
                
                time.sleep(1)

            self.connectionLost.emit(self._ssh.host, lostConnexionReason)

        except SystemError:
            pass
        except Exception as e:
            self.connectionLost.emit(self._ssh.host, 
            'An error occured when communicating with the robot. Check the console for more details.')
            print("An error occured when communicating with the robot.", e)
            traceback.print_exc()
        finally:
            if self._ssh is not None:
                try:
                    self._ssh.run('rm -f' + LOCK_PATH, hide=True, warn=True, timeout=5)
                except Exception:
                    pass
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

        # === Ping robot ===
        self._set_connection_status(ConnectionStatus.PING)
        strength, avg_ping = self.get_signal_strength(host)
        if strength <= 0:
            self.connectionFailed.emit(ConnectionFailedReason.UNREACHABLE, 
                                       f"Address <i>{host}</i> doesn't respond to ping. "
                                       "Check robot address and network quality.")
            return None
        else:
            self._set_signalStrength(strength, avg_ping)
        
        # === Initiate SSH Connection ===
        self._set_connection_status(ConnectionStatus.AUTH)
        try:
            config = SSHConfig(overrides={'sudo': {'password': password}})
            ssh = SSHConnection(f"{username}@{host}:{port}", connect_timeout=30,
                                connect_kwargs=dict(password= password),
                                config=config)
            ssh.open()
        except TimeoutError:
            self.connectionFailed.emit(ConnectionFailedReason.UNREACHABLE, 
                                       f"Connection to <i>{host}</i> timed-out. (Robot might be to busy to respond...)")
            return None
        except NoValidConnectionsError:
            self.connectionFailed.emit(ConnectionFailedReason.UNREACHABLE, 
                                       f'<i>{host}:{port}</i> is not a EV3 robot. (Or ssh is disabled.)')
            return None
        except AuthenticationException:
            self.connectionFailed.emit(ConnectionFailedReason.AUTH, f'Invalid authentication with credentials:'
                                                                    f'"{username}:{password}".')
            return None
        except Exception:
            msg = f'Error when connecting to the robot at <i>{username}:{password}@{host}:{port}</i>.'
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
                lock_stat = ssh_run(f'stat {SCRIPT_CWD+LOCK_PATH} -c %Y')
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
                    lock_host = ssh_run("cat "+SCRIPT_CWD+LOCK_PATH).stdout.strip()
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
            ssh_run(f'echo "{socket.gethostname()}" > '+SCRIPT_CWD+LOCK_PATH)

            # === Push DS.py script to the robot ===
            self._set_connection_status(ConnectionStatus.SETUP)
            if not self.push_ds_script(ssh):
                ssh.close()
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

        return ssh

    def refresh_ssh_status(self) -> bool:
        if not self._ssh.is_connected:
            return "SSH connection with the robot has been lost."

        try:
            status = self._ssh.run(SCRIPT_CWD+'DS.sh', hide=True, warn=True, timeout=5)
            if self._request_program_date.is_set():
                self._request_program_date.clear()
                program_date = self._ssh.run('cat version.txt 2>/dev/null', hide=True, warn=True, timeout=5)
                if program_date.stdout:
                    self.robot.set_program_date(program_date.stdout.strip())

        except CommandTimedOut:
            print("Timeout when running the SSH script.")
            return False
        if status.stderr:
            print("Error when running the SSH script:")
            print(status.stderr)
            return "SSH script returned an error."

        telemetry_status = {}
        for line in status.stdout.splitlines():
            line = line.strip()
            if not line:
                continue

            line_code, line_content = line[0], line[1:]
            if line_code == 'S':
                match line_content:
                    case '0': 
                        self.robot.set_program_status(ProgramStatus.IDLE)
                    case '1': 
                        self.robot.set_program_status(ProgramStatus.STARTING)
                    case '2': 
                        self.robot.set_program_status(ProgramStatus.RUNNING)
            telemetry_status[line_code] = line_content

        self.telemetry.refresh_robot_status(telemetry_status)

        return False

    def check_java_running(self) -> bool:
        if self._ssh is None:
            return False
        status = self._ssh.run('pgrep java', hide=True, warn=True, timeout=5)
        return status.stdout != ''

    def refresh_signal_strength(self) -> bool:
        strength, avg_ping = self.get_signal_strength(self._ssh.host)
        self._set_signalStrength(strength, avg_ping)
        return strength > 0

    def get_signal_strength(self, host: str) -> bool:
        ping_result = ping(host, count=3, interval=.1, timeout=PING_TIMEOUT)

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

    def push_ds_script(self, ssh):
        local_path = path.join(path.abspath(path.dirname(__file__)), 'DS.sh')
        # Ensure linux end of line
        with open(local_path, 'rb') as f:
            content = f.read()
        content = content.replace(WINDOWS_LINE_ENDING, UNIX_LINE_ENDING)
        with open(local_path, 'wb') as f:
            f.write(content)

        ssh.put(local_path, SCRIPT_CWD + 'DS.sh')
        ssh.run("chmod +x " + SCRIPT_CWD + 'DS.sh', hide=True, warn=True, timeout=5)

        # script_status = ssh.sudo('python '+ SCRIPT_CWD+'DS.sh', hide=True, warn=True, timeout=120)
        # if script_status.stderr:
        #     error = '|\t'+script_status.stderr.strip().replace('\n', '\n|\t')
        #     if 'RuntimeError: Impossible to install dependencies:' in script_status.stderr:
        #         print("Failed to install dependencies on the robot.")
        #         print(error)
        #         self.connectionFailed.emit(ConnectionFailedReason.SETUP, 
        #                                    "Robot must access internet to install the telemetry script dependencies.")
        #         return False
        #     else:
        #         print("Error when initiating the SSH script:")
        #         print(error)
        #         self.connectionFailed.emit(ConnectionFailedReason.SETUP, 
        #                                    "Failed to initiate telemetry script on the robot. "
        #                                    "Check the console for more details.")
        #         return False
        return True

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

    # --- Refresh Rate --- #
    maxUdpRefreshRate_changed = Signal(int)
    @Property(int, notify=maxUdpRefreshRate_changed)
    def maxUdpRefreshRate(self) -> int:
        return getattr(self._udp_refresh_rates, self._udp_refresh_mode).max

    @maxUdpRefreshRate.setter
    def maxUdpRefreshRate(self, value: int):
        t = int(round(value))
        if t == self.maxUdpRefreshRate:
            return

        self._udp_refresh_rates = self._udp_refresh_rates.set(self._udp_refresh_mode, max=t)
        self.maxUdpRefreshRate_changed.emit(t)
        self._set_udp_refresh_timers_intervals(maxRate=t)

        if self.minUdpRefreshRate > t:
            self.minUdpRefreshRate = t

    minUdpRefreshRate_changed = Signal(int)
    @Property(int, notify=minUdpRefreshRate_changed)
    def minUdpRefreshRate(self) -> int:
        return getattr(self._udp_refresh_rates, self._udp_refresh_mode).min

    @minUdpRefreshRate.setter
    def minUdpRefreshRate(self, value: int):
        t = int(round(value))
        if t == self.minUdpRefreshRate:
            return

        self._udp_refresh_rates = self._udp_refresh_rates.set(self._udp_refresh_mode, min=t)
        self.minUdpRefreshRate_changed.emit(t)
        self._set_udp_refresh_timers_intervals(minRate=t)

    @Slot()
    def _update_udp_refresh_mode(self):
        if self.robot.robotStatus == RobotStatus.ENABLED:
            mode = {
                RobotMode.AUTO: 'auto',
                RobotMode.TELEOP: 'teleop',
                RobotMode.TEST: 'teleop'
            }[self.robot.mode]
        elif self.robot.robotStatus == RobotStatus.DISABLED:
            mode = 'disabled'
        else:
            mode = 'idle'
        
        if mode != self._udp_refresh_mode:
            self._udp_refresh_mode = mode
            minRate, maxRate = self.minUdpRefreshRate, self.maxUdpRefreshRate
            self.maxUdpRefreshRate_changed.emit(maxRate)
            self.minUdpRefreshRate_changed.emit(minRate)
            self._set_udp_refresh_timers_intervals(maxRate, minRate)

    def _set_udp_refresh_timers_intervals(self, maxRate=None, minRate=None):
        if self._last_udp_t is not None:
            dt = (time.time() - self._last_udp_t) * 1000
        else:
            dt = 0

        if maxRate is not None:
            if maxRate > 0:
                self._max_udp_refresh_timer.start(max(maxRate-dt, 0))
            else:
                self._max_udp_refresh_timer.stop()
        if minRate is not None:
            if maxRate is None:
                maxRate = self.maxUdpRefreshRate
            if minRate>0 and minRate < maxRate:
                self._min_udp_refresh_timer.start(max(minRate-dt, 0))
            else:
                self._min_udp_refresh_timer.stop()

    # --- Pull Telemetry Rate --- #
    pullTelemetryRate_changed = Signal(int)
    @Property(int, notify=pullTelemetryRate_changed)
    def pullTelemetryRate(self) -> int:
        return self._pull_telemetry_rate

    @pullTelemetryRate.setter
    def pullTelemetryRate(self, value: int):
        t = int(round(value))
        if t == self._pull_telemetry_rate:
            return

        self._pull_telemetry_rate = t
        self.pullTelemetryRate_changed.emit(t)

    # --- Mute UDP Refresh --- #
    muteUdpRefresh_changed = Signal(bool)
    @Property(bool, notify=muteUdpRefresh_changed)
    def muteUdpRefresh(self) -> bool:
        return self._connection_status != ConnectionStatus.CONNECTED\
            or self._mute_udp_refresh

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

    def tick_udp_avg_dt(self) -> None:
        last_udp_t = self._last_udp_t
        t = time.time()
        self._last_udp_t = t

        if last_udp_t is None:
            return

        last_dt = (t-last_udp_t) * 1000
        if self._udp_avg_dt == 0 or abs(last_dt-self._udp_avg_dt) > 1000:
            self._udp_avg_dt = last_dt
        else:
            self._udp_avg_dt = self._udp_avg_dt * 0.9 + last_dt * 0.1
        self.udpAvgDt_changed.emit(self._udp_avg_dt)


class ConnectionStatus(str, Enum):
    CONNECTED = 'Connected'
    PING = 'Pinging'
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


class DriverStationState(NamedTuple):
    controller1: ControllerState = ControllerState()
    controller2: ControllerState = ControllerState()
    enabled: bool = False
    mode: RobotMode = RobotMode.TELEOP

    @property
    def contollers(self) -> tuple[ControllerState, ControllerState]:
        return self.controller1, self.controller2

    def is_same(self, other: DriverStationState, axis_tolerance: float = 0.05) -> bool:
        if other is None:
            return False
        return self.controller1.is_same(other.controller1) \
           and self.controller2.is_same(other.controller2) \
           and ((not self.enabled and not other.enabled) or self.mode == other.mode)


class Rates(NamedTuple):
    max: int = 30
    min: int = 0


class RefreshRates(NamedTuple):
    idle: Rates = Rates(1000, 1000)
    disabled: Rates = Rates(200, 200)
    auto: Rates = Rates(40)
    teleop: Rates = Rates(50,30)

    def save(self):
        d = self.to_dict()
        del d['idle']
        QSettings('EV3DriverStation').setValue('refreshRates', self.to_dict())

    @classmethod
    def load(cls):
        saved = QSettings('EV3DriverStation').value('refreshRates', None)
        if saved is not None:
            del saved['idle']
            return cls.from_dict(saved)
        return cls()

    def to_dict(self):
        return {
            'idle': (self.idle.max, self.idle.min),
            'disabled': (self.disabled.max, self.disabled.min),
            'auto': (self.auto.max, self.auto.min),
            'teleop': (self.teleop.max, self.teleop.min)
        }

    @classmethod
    def from_dict(cls, d: dict):
        d = {k: Rates(*v) for k, v in d.items()}
        return cls(**d)

    def set(self, mode, max=None, min=None, save=True):
        d = dict()
        if max is not None:
            d['max'] = max
        if min is not None:
            d['min'] = min
        if d:
            d = self._replace(**{mode: getattr(self, mode)._replace(**d)})
            d.save()
            return d
        else:
            return self
