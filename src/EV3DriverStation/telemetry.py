from __future__ import annotations

from datetime import datetime
from enum import Enum

# from networktables import NetworkTables
from PySide6.QtCore import Property, QObject, Signal, Slot


class Telemetry(QObject):
    def __init__(self, network_tables_refresh_rate=450):
        super().__init__()
        self._program_last_update = ''
        self._voltage = 0
        self._cpu = 0
        self._telemetry_data = {}
        self._telemetry_status = TelemetryStatus.UNAVAILABLE

        # self._network_tables = None
        # self._nt_refresh_rate = network_tables_refresh_rate
        # self._nt_status_timer = QTimer()
        # self._nt_status_timer.setInterval(self._nt_refresh_rate)
        # self._nt_status_timer.timeout.connect(self._refresh_telemetry_status)
    
    @Slot()
    def clear_and_disconnect(self):
        self._program_last_update = ''
        self._voltage = 0
        self._cpu = 0
        self._telemetry_data = {}
        self._telemetry_status = TelemetryStatus.UNAVAILABLE

        self.programLastUpdate_changed.emit(self._program_last_update)
        self.voltage_changed.emit(self._voltage)
        self.cpu_changed.emit(self._cpu)
        self.telemetryData_changed.emit()
        self.telemetryStatus_changed.emit(self._telemetry_status)

        # self.disconnect_network_tables()


    def refresh_robot_status(self, status: str):
        """
        Refresh the robot status from the string provided by the DS.sh script output.
        """
        self.set_program_date(None)
        for line in status.splitlines():
            line = line.strip()
            if not line:
                continue
            line_code, line_content = line[0], line[1:]

            if line_code == 'A':
                try:
                    date = datetime.strptime(line_content, "%Y%m%d%H%M%S")
                except ValueError:
                    date = None
                self.set_program_date(date)
            elif line_code == 'V':
                self.set_robot_voltage(float(line_content)/1000)
            elif line_code == 'C':
                self.set_cpu_usage(float(line_content))

    #====================#
    #== Network Tables ==#
    #====================#
    # @Slot(str)
    # def connect_network_tables(self, ip: str):
    #    if self._network_tables is not None:
    #        self.disconnect_network_tables()
    #    self._network_tables = NetworkTables.initialize(server=ip)
    #    self._network_tables.setUpdateRate(self._nt_refresh_rate)
    #    self._network_tables.addEntryListener(self._network_tables_listener, 
    #                                          immediateNotify=True,
    #                                          paramIsNew=False)
    #    self._nt_status_timer.start()

    #@Slot()
    #def disconnect_network_tables(self):
    #    self._network_tables.shutdown()
    #    self._network_tables = None
    #    self._nt_status_timer.stop()

    # def _nt_listener(self, table, key, value, flag):
    #    NotifyFlags = self._network_tables.NotifyFlags
    #    match flag:
    #        case NotifyFlags.UPDATE | NotifyFlags.NEW | NotifyFlags.IMMEDIATE | NotifyFlags.LOCAL:
    #            self.add_telemetry_data(key, value)
    #        case NotifyFlags.DELETE:
    #            self.remove_telemetry_data(key)

    # def _refresh_telemetry_status(self):
    #    if self._network_tables is None:
    #        return self.set_telemetry_status(TelemetryStatus.UNAVAILABLE)
    #    NetworkModes = self._network_tables.NetworkMode
    #    match self._network_tables.getNetworkMode():
    #        case NetworkModes.NONE:
    #            self.set_telemetry_status(TelemetryStatus.UNAVAILABLE)
    #        case NetworkModes.FAILURE:
    #            self.set_telemetry_status(TelemetryStatus.UNAVAILABLE)
    #        case NetworkModes.STARTING:
    #            self.set_telemetry_status(TelemetryStatus.CONNECTING)
    #        case NetworkModes.CLIENT:
    #            self.set_telemetry_status(TelemetryStatus.CONNECTED)
        

    #====================#
    #== QML PROPERTIES ==#
    #====================#
    # --- Program date --- #
    programLastUpdate_changed = Signal(str)
    @Property(str, notify=programLastUpdate_changed)
    def programLastUpdate(self) -> str:
        return self._program_last_update

    def set_program_date(self, date: float | None):
        if date is None:
            date = ""
        else:
            age_s = (datetime.now() - date).total_seconds()
            
            if age_s < 0:
                date = "Invalid date"
            elif age_s < 60:
                date = f"{round(age_s/10)*10:.0f} seconds ago"
            elif age_s < 3600:
                date = f"{age_s // 60:.0f} min ago"
            elif age_s < 86400:
                date = date.strftime("Today %H:%M")
            else:
                date = date.strftime("%d/%m/%y %H:%M")

        if date != self._program_last_update:
            self._program_last_update = date 
            self.programLastUpdate_changed.emit(self._program_last_update)

    # --- Robot voltage --- #
    voltage_changed = Signal(float)
    @Property(float, notify=voltage_changed)
    def voltage(self) -> float:
        return self._voltage

    def set_robot_voltage(self, voltage: float):
        if voltage != self._voltage:
            self._voltage = voltage
            self.voltage_changed.emit(self._voltage)

    # --- CPU usage --- #
    cpu_changed = Signal(float)
    @Property(float, notify=cpu_changed)
    def cpu(self) -> float:
        return self._cpu

    def set_cpu_usage(self, cpu: float):
        if cpu != self._cpu:
            self._cpu = cpu
            self.cpu_changed.emit(self._cpu)

    # --- Telemetry status --- #
    telemetryStatus_changed = Signal(str)
    @Property(str, notify=telemetryStatus_changed)
    def telemetryStatus(self) -> TelemetryStatus:
        return self._telemetry_status

    def set_telemetry_status(self, status: TelemetryStatus):
        if status != self._telemetry_status:
            self._telemetry_status = status
            self.telemetryStatus_changed.emit(status)

    # --- Telemetry data --- #
    telemetryData_changed = Signal()
    @Property(list, notify=telemetryData_changed)
    def telemetryData(self) -> list:
        return [{'key': k, 'value': v} for k, v in self._telemetry_data.items()]

    def set_telemetry_data(self, data: dict):
        if data is None:
            data = {}
            self.set_telemetry_status(TelemetryStatus.UNAVAILABLE)
        else:
            self.set_telemetry_status(TelemetryStatus.CONNECTED)
        if data != self._telemetry_data:
            self._telemetry_data = data
            self.telemetryData_changed.emit()

    def add_telemetry_data(self, key, value):
        if key not in self._telemetry_data or self._telemetry_data[key] != value:
            self._telemetry_data[key] = value
            self.telemetryData_changed.emit()
    
    def remove_telemetry_data(self, key):
        if key in self._telemetry_data:
            del self._telemetry_data[key]
            self.telemetryData_changed.emit()

class TelemetryStatus(str, Enum):
    UNAVAILABLE = "Unavailable"
    CONNECTING = "Connecting"
    CONNECTED = "Connected"