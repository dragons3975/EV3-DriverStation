from __future__ import annotations

import time
from datetime import datetime
from enum import Enum

# from networktables import NetworkTables
from PySide6.QtCore import Property, QObject, Signal, Slot


class Telemetry(QObject):
    def __init__(self):
        super().__init__()
        self._ev3_voltage = 0
        self._aux_voltage = 0
        self._ev3_current = 0
        self._cpu_load = 0

        self._telemetry_data = {}
        self._freeze_telemetry = False
        self._telemetry_status = TelemetryStatus.UNAVAILABLE
        self._last_telemetry_t = None
        self._telemetry_avg_dt = 0

        # self._network_tables = None
        # self._nt_refresh_rate = network_tables_refresh_rate
        # self._nt_status_timer = QTimer()
        # self._nt_status_timer.setInterval(self._nt_refresh_rate)
        # self._nt_status_timer.timeout.connect(self._refresh_telemetry_status)
    
    @Slot()
    def clear_and_disconnect(self):
        self.set_ev3_voltage(0)
        self.set_ev3_current(0)
        self.set_cpu_load(0)
        self.set_telemetry_data(None)

        self._telemetry_avg_dt = None
        self._last_telemetry_t = 0

        # self.disconnect_network_tables()


    def refresh_robot_status(self, status: dict[str, str]):
        """
        Refresh the robot status from the string provided by the DS.sh script output.
        """
        for code, content in status.items():
            if code == 'V':
                self.set_ev3_voltage(float(content)/1000)
            elif code == 'A':
                self.set_aux_voltage(float(content)/1000)
            elif code == 'C':
                self.set_ev3_current(float(content))
            elif code == 'L':
                self.set_cpu_load(float(content))

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
    # --- EV3 voltage --- #
    ev3Voltage_changed = Signal(float)
    @Property(float, notify=ev3Voltage_changed)
    def ev3Voltage(self) -> float:
        return self._ev3_voltage

    def set_ev3_voltage(self, voltage: float):
        if voltage != self._ev3_voltage:
            self._ev3_voltage = voltage
            self.ev3Voltage_changed.emit(self._ev3_voltage)

    # --- Aux voltage --- #
    auxVoltage_changed = Signal(float)
    @Property(float, notify=auxVoltage_changed)
    def auxVoltage(self) -> float:
        return self._aux_voltage

    def set_aux_voltage(self, voltage: float):
        if voltage != self._aux_voltage:
            self._aux_voltage = voltage
            self.auxVoltage_changed.emit(self._aux_voltage)

    # --- EV3 current --- #
    ev3Current_changed = Signal(float)
    @Property(float, notify=ev3Current_changed)
    def ev3Current(self) -> float:
        return self._ev3_current

    def set_ev3_current(self, current: float):
        if current != self._ev3_current:
            self._ev3_current = current
            self.ev3Current_changed.emit(self._ev3_current)

    # --- CPU usage --- #
    cpu_changed = Signal(float)
    @Property(float, notify=cpu_changed)
    def cpu(self) -> float:
        return self._cpu_load

    def set_cpu_load(self, cpu: float):
        if cpu != self._cpu_load:
            self._cpu_load = cpu
            self.cpu_changed.emit(self._cpu_load)

    # --- Telemetry status --- #
    telemetryStatus_changed = Signal(str)
    @Property(str, notify=telemetryStatus_changed)
    def telemetryStatus(self) -> TelemetryStatus:
        return self._telemetry_status

    def set_telemetry_status(self, status: TelemetryStatus):
        if status != self._telemetry_status:
            self._telemetry_status = status
            self.telemetryStatus_changed.emit(status)

    # --- Freeze telemetry --- #
    freezeTelemetry_changed = Signal(bool)
    @Property(bool, notify=freezeTelemetry_changed)
    def freezeTelemetry(self) -> bool:
        return self._freeze_telemetry

    @freezeTelemetry.setter
    def freezeTelemetry(self, freeze: bool):
        if freeze != self._freeze_telemetry:
            self._freeze_telemetry = freeze
            self.freezeTelemetry_changed.emit(freeze)

            self._telemetry_avg_dt = 0
            self._last_telemetry_t = None
            self.telemetryAvgDt_changed.emit(0)
            

    # --- Telemetry average dt --- #
    telemetryAvgDt_changed = Signal(float)
    @Property(float, notify=telemetryAvgDt_changed)
    def udpAvgDt(self) -> float:
        return self._telemetry_avg_dt

    def tick_telemetry_avg_dt(self) -> None:
        last_udp_t = self._last_telemetry_t
        t = time.time()
        self._last_telemetry_t = t

        if last_udp_t is None:
            return

        last_dt = (t-last_udp_t) * 1000
        if self._telemetry_avg_dt==0 or abs(last_dt-self._telemetry_avg_dt) > 1000:
            self._telemetry_avg_dt = last_dt
        else:
            self._telemetry_avg_dt = self._telemetry_avg_dt * 0.8 + last_dt * 0.2
        self.telemetryAvgDt_changed.emit(self._telemetry_avg_dt)
    
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