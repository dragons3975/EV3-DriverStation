from __future__ import annotations

import struct

import yaml
from PySide6.QtCore import Property, QObject, Signal, Slot

from .utils import AverageOverTime


class Telemetry(QObject):
    def __init__(self):
        super().__init__()
        self._ev3_voltage = 0
        self._aux_voltage = 0
        self._ev3_current = 0
        self._cpu_load = 0
        self._avg_skipped_frames = AverageOverTime(5)
        self._avg_frame_exec_time = AverageOverTime(5)

        self._telemetry_data = {}

        
    @Slot()
    def clear(self):
        self.set_ev3_voltage(0)
        self.set_ev3_current(0)
        self.set_cpu_load(0)
        self.clear_program_data()

    def clear_program_data(self):
        self.set_telemetry_data({})
        self._avg_skipped_frames.clear()
        self._avg_frame_exec_time.clear()
        self.skippedFrames_changed.emit(0)
        self.frameExecTime_changed.emit(0)


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

    def parse_udp_response(self, telemetry_data):
        """
        Parse the UDP response from the robot and update the telemetry data.
        """
        if telemetry_data[0] == 255:
            if len(telemetry_data) > 1:
                telemetry_data = telemetry_data[1:].decode('ascii')
                data = yaml.safe_load(telemetry_data)
                if data is not None:
                    self.set_telemetry_data(data)
            else:
                self.set_telemetry_data({})
        else:
            try:
                var_names  = list(self._telemetry_data.keys())
                telemetry_data = list(telemetry_data)
                while len(telemetry_data) > 0:
                    varID = telemetry_data.pop(0)
                    varName = var_names[varID]
                    var = self._telemetry_data[varName]
                    if isinstance(var, bool):
                        var = telemetry_data.pop(0) != 0
                    elif isinstance(var, int):
                        var = struct.unpack('h', bytes(telemetry_data[:2]))[0]
                        del telemetry_data[:2]
                    elif isinstance(var, float):
                        var = struct.unpack('f', bytes(telemetry_data[:4]))[0]
                        del telemetry_data[:4]
                    elif isinstance(var, str):
                        size = int(telemetry_data.pop(0))
                        var = bytes(telemetry_data[:size]).decode('ascii')
                        del telemetry_data[:size]
                    self._telemetry_data[varName] = var
            except Exception:
                return False

        self.telemetryData_changed.emit()
        return True


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

    # --- Skipped frames --- #
    skippedFrames_changed = Signal(float)
    @Property(float, notify=skippedFrames_changed)
    def skippedFrames(self) -> float:
        return self._avg_skipped_frames.get(-1)

    def put_skipped_frame(self, skipped: float):
        self._avg_skipped_frames.put(skipped)
        self.skippedFrames_changed.emit(self._avg_skipped_frames.get())

    # --- Frame execution time --- #
    frameExecTime_changed = Signal(float)
    @Property(float, notify=frameExecTime_changed)
    def frameExecTime(self) -> float:
        return self._avg_frame_exec_time.get(-1)

    def put_frame_exec_time(self, exec_time: float):
        self._avg_frame_exec_time.put(exec_time)
        self.frameExecTime_changed.emit(self._avg_frame_exec_time.get())

    # --- Telemetry data --- #
    telemetryData_changed = Signal()
    @Property(list, notify=telemetryData_changed)
    def telemetryData(self) -> list:
        return [{'key': k, 'value': v} for k, v in self._telemetry_data.items()]

    def set_telemetry_data(self, data: dict):
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
