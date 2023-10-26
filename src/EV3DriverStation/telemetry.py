from __future__ import annotations

import re
import struct
import threading
import traceback
from enum import Enum

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

        self._telemetry_data = []
        self._telemetry_transmitted = False
        self.newTelemetryData.connect(self.parse_new_telemetry_data)

        
    @Slot()
    def clear(self):
        self.set_ev3_voltage(0)
        self.set_ev3_current(0)
        self.set_cpu_load(0)
        self.clear_program_data()

    def clear_program_data(self):
        self.set_telemetry_data([])
        self.set_telemetry_transmitted(False)
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
                telemetry_data_str = telemetry_data[1:].decode('ascii')
            else:
                telemetry_data_str = ''
            self.newTelemetryData.emit(telemetry_data_str) # Use signal to avoid threading issues
        else:
            try:
                telemetry_data = bytearray(telemetry_data)
                while len(telemetry_data) > 0 and telemetry_data[0] < 255:
                    varID = telemetry_data.pop(0)
                    telemetry_data = self._telemetry_data[varID].from_bytes(telemetry_data)
            except Exception:
                print("Error while parsing UDP telemetry data")
                traceback.print_exc()
                return False
        self.telemetryData_changed.emit()
        return True

    def generate_udp_telemetry_update(self) -> bytes:
        """
        Generate the UDP telemetry update packet to send to the robot.
        """
        packet = bytearray()
        for i, var in enumerate(self._telemetry_data):
            if var.editable and var.check_changed():
                packet.append(i)
                packet.extend(var.to_bytes())
        return bytes(packet)


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
    @Property("QVariantList", notify=telemetryData_changed)
    def telemetryData(self) -> list:
        return self._telemetry_data

    def set_telemetry_data(self, data: list[TelemetryVariable]):
        self._telemetry_data = data
        self.telemetryData_changed.emit()
        self.set_telemetry_transmitted(True)

    newTelemetryData = Signal(str)
    @Slot(str)
    def parse_new_telemetry_data(self, telemetry_data: str):
        if len(telemetry_data) > 0:
            data = yaml.safe_load(telemetry_data)
            if data is not None:
                telemetry_data = []
                for name, value in data.items():
                    editable = name.startswith('?')
                    if editable:
                        name = name[1:]
                    telemetry_data.append(TelemetryVariable(name, editable, value))
                self.set_telemetry_data(telemetry_data)

        else:
            self.set_telemetry_data([])

    # --- Telemetry unknown --- #
    telemetryTransmitted_changed = Signal(bool)
    @Property(bool, notify=telemetryTransmitted_changed)
    def telemetryTransmitted(self) -> bool:
        return self._telemetry_transmitted

    def set_telemetry_transmitted(self, unknown: bool):
        if unknown != self._telemetry_transmitted:
            self._telemetry_transmitted = unknown
            self.telemetryTransmitted_changed.emit(self._telemetry_transmitted)


class TelemetryVariable(QObject):
    def __init__(self, name: str, editable: bool, value: bool|int|float|str):
        super().__init__()
        self._name = name
        self._editable = editable
        self._value = value
        self._type = TelemetryVarType.from_value(value)
        self._changedFlag = threading.Event()

    def __repr__(self):
        return f"TelemetryVariable({self.name}, {self._type}, {self.value})"

    def check_changed(self):
        if self._changedFlag.is_set():
            self._changedFlag.clear()
            return True
        return False
    
    def from_bytes(self, data: bytearray):
        if self._type == TelemetryVarType.BOOL:
            value = data.pop(0) != 0
        elif self._type == TelemetryVarType.INT:
            value = struct.unpack('h', data[:2])[0]
            del data[:2]
        elif self._type == TelemetryVarType.FLOAT:
            value = struct.unpack('f', data[:4])[0]
            del data[:4]
        elif self._type == TelemetryVarType.STRING:
            size = int(data.pop(0))
            value = data[:size].decode('ascii')
            del data[:size]
        else:
            return
        if value != self.value:
            self._value = value
            self.valueChanged.emit()
        else:
            self.valueTransmitted.emit()
        return data

    def to_bytes(self) -> bytes:
        if self._type == TelemetryVarType.BOOL:
            return struct.pack('?', self.value)
        elif self._type == TelemetryVarType.INT:
            return struct.pack('h', self.value)
        elif self._type == TelemetryVarType.FLOAT:
            return struct.pack('f', self.value)
        elif self._type == TelemetryVarType.STRING:
            return struct.pack('B', len(self.value)) + self.value.encode('ascii')

    #====================#
    #== QML PROPERTIES ==#
    #====================#

    # --- Name --- #
    @Property(str, constant=True)
    def name(self) -> str:
        return self._name

    # --- Editable --- #
    @Property(bool, constant=True)
    def editable(self) -> bool:
        return self._editable

    # --- Type --- #
    @Property(str, constant=True)
    def valueType(self) -> str:
        return self._type

    # --- Value --- #
    valueChanged = Signal()
    valueTransmitted = Signal()
    @Property("QVariant", notify=valueChanged) 
    def value(self) -> bool|int|float|str:
        return self._value

    @Property(str, notify=valueChanged)
    def formattedValue(self) -> str:
        return TelemetryVarType.format_value(self.value, self.valueType)

    @Slot("QVariant", result=bool)
    def setValue(self, value: bool|int|float|str) -> bool:
        if not self.editable:
            return False
        try:
            value = TelemetryVarType.cast_to(value, self._type)
        except ValueError:
            return False

        validValue = True
        if self._type == TelemetryVarType.STRING:
            if re.match(r'^[\x00-\x7F]*$', value) is None:
                validValue = False
                value = re.sub(r'[^\x00-\x7F]', '', value)
            if len(value) > 255:
                validValue = False
                value = value[:255]
        elif self._type == TelemetryVarType.INT:
            if abs(value) > 32767:
                validValue = False
                value = 32767 if value > 0 else -32767
        elif self._type == TelemetryVarType.FLOAT:
            convertedValue = float(struct.unpack('f', struct.pack('f', value))[0])
            validValue = (TelemetryVarType.format_value(convertedValue, TelemetryVarType.FLOAT) 
                         == TelemetryVarType.format_value(value, TelemetryVarType.FLOAT))
            value = convertedValue
            
        if value == self.value:
            return validValue
            
        self._value = value
        self.valueChanged.emit()
        self._changedFlag.set()
        return validValue
        

class TelemetryVarType(str, Enum):
    BOOL = 'bool'
    INT = 'int'
    FLOAT = 'float'
    STRING = 'string'

    @classmethod
    def from_value(cls, v):
        if isinstance(v, bool):
            return cls.BOOL
        elif isinstance(v, int):
            return cls.INT
        elif isinstance(v, float):
            return cls.FLOAT
        elif isinstance(v, str):
            return cls.STRING
        else:
            raise ValueError(f"Invalid type {type(v)} for telemetry variable")

    @classmethod
    def cast_to(cls, v, t: TelemetryVarType):
        if t == cls.BOOL:
            if isinstance(v, bool):
                return v
            elif isinstance(v, str):
                return v.lower() in ("true", "1")
            else:
                return bool(v)
        elif t == cls.INT:
            return int(v)
        elif t == cls.FLOAT:
            return float(v)
        elif t == cls.STRING:
            return str(v)
        else:
            raise ValueError(f"Invalid type {t} for telemetry variable")

    @classmethod
    def format_value(cls, v, t: TelemetryVarType) -> str:
        if t == TelemetryVarType.BOOL:
            return 'true' if v else 'false'
        elif t == TelemetryVarType.INT:
            return str(v)
        elif t == TelemetryVarType.FLOAT:
            if v == float('inf'):
                return "∞"
            elif v == float('-inf'):
                return "-∞"
            elif abs(v) < 1e-15:
                return "0.000"
            else:
                return f'{v:.3f}' if 1e-3 < abs(v) < 1e3 else f'{v:.3e}'
        elif t == TelemetryVarType.STRING:
            return v
        return ""
