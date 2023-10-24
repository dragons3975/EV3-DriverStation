from __future__ import annotations

from datetime import datetime
from enum import Enum
from time import time

from PySide6.QtCore import Property, QObject, QSettings, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QKeyEvent

MAX_TELEOP_TIME = 120
MAX_AUTO_TIME = 60

class Robot(QObject):
    def __init__(self, keyboard_controller):
        super().__init__()
        self._mode: RobotMode = RobotMode.TELEOP
        self._robot_status: RobotStatus = RobotStatus.IDLE
        self._program_status: ProgramStatus = ProgramStatus.IDLE
        self._auto_disable: bool = QSettings('EV3DriverStation').value("auto_disable_on_timer", False, bool)
        self._time = 0
        self._timer_start_t = None
        self._program_last_update = ''

        self._keyboard_controller = keyboard_controller
        self.capture_keyboard = False

        self.timer = QTimer()
        self.timer.setInterval(30)
        self.timer.timeout.connect(self.increment_timer)

    #====================#
    #== QML PROPERTIES ==#
    #====================#
    # --- Program status --- #
    programStatus_changed = Signal(str)
    @Property(str, notify=programStatus_changed)
    def programStatus(self) -> ProgramStatus:
        return self._program_status

    def set_program_status(self, status: ProgramStatus):
        if self._program_status != status:
            old_status = self._program_status
            self._program_status = status

            if status == ProgramStatus.RUNNING:
                if old_status == ProgramStatus.IDLE:
                    self.on_program_starting()
                self.on_program_started()
            elif status == ProgramStatus.STARTING:
                self.on_program_starting()
            else:
                self.on_program_stopped()
            self.programStatus_changed.emit(self._program_status)

    programStarting = Signal()
    def on_program_starting(self):
        self.programStarting.emit()

    programStarted = Signal()
    def on_program_started(self):
        self.programStarted.emit()
        self.set_robot_status(RobotStatus.DISABLED)

    programStopped = Signal()
    def on_program_stopped(self):
        self.programStopped.emit()
        self.set_robot_status(RobotStatus.IDLE)
        self.set_program_date(None)

    # --- Robot mode --- #
    mode_changed = Signal(str)
    @Property(str, notify=mode_changed)
    def mode(self) -> RobotMode:
        return self._mode

    @mode.setter
    def mode(self, value: RobotMode):
        self.enabled = False
        self._mode = value
        self.mode_changed.emit(self._mode)

        # Reset timer when mode changes
        self.reset_timer()

    # --- Robot Status --- #
    robotStatus_changed = Signal(str)
    @Property(str, notify=robotStatus_changed)
    def robotStatus(self) -> RobotStatus:
        return self._robot_status

    def set_robot_status(self, status: RobotStatus):
        if self._robot_status == status:
            return

        self._robot_status = status
        self.robotStatus_changed.emit(self._robot_status)
        self.enabled_changed.emit(self.enabled)

        # Start/stop timer
        if status == RobotStatus.ENABLED:
            if self.auto_disable and self.mode == RobotMode.TELEOP and self.time >= MAX_TELEOP_TIME:
                self.reset_timer()
            self.start_timer()
        else:
            self.stop_timer()
            if status == RobotStatus.IDLE or self.mode == RobotMode.AUTO:
                self.reset_timer()

    enabled_changed = Signal(bool)
    @Property(bool, notify=enabled_changed)
    def enabled(self) -> bool:
        return self._robot_status == RobotStatus.ENABLED

    @enabled.setter
    def enabled(self, e: bool):
        self.set_robot_status(RobotStatus.ENABLED if e else RobotStatus.DISABLED)

    # --- Auto disable --- #
    auto_disable_changed = Signal(bool)
    @Property(bool, notify=auto_disable_changed)
    def auto_disable(self) -> bool:
        return self._auto_disable

    @auto_disable.setter
    def auto_disable(self, value: bool):
        if value == self._auto_disable:
            return
        self._auto_disable = value
        self.auto_disable_changed.emit(self._auto_disable)
        QSettings('EV3DriverStation').setValue("auto_disable_on_timer", value)

    # --- Timer --- #
    time_changed = Signal(float)
    @Property(float, notify=time_changed)
    def time(self) -> float:
        return self._time + (time() - self._timer_start_t if self._timer_start_t else 0)

    @Slot()
    def reset_timer(self):
        self._time = 0
        if self._timer_start_t is not None:
            self._timer_start_t = time()
        self.time_changed.emit(self._time)

    @Slot()
    def start_timer(self):
        self._timer_start_t = time()
        self.timer.start()

    @Slot()
    def stop_timer(self):
        self.timer.stop()
        if self._timer_start_t is not None:
            self._time += time() - self._timer_start_t
        self._timer_start_t = None

    def increment_timer(self):
        self.time_changed.emit(self._time)

        # Auto disable robot after 60 seconds in auto and 120 seconds in teleop
        if self.auto_disable:
            time = self.time
            if self.mode == RobotMode.AUTO and time >= MAX_AUTO_TIME:
                self.enabled = False
            elif self.mode == RobotMode.TELEOP and time >= MAX_TELEOP_TIME:
                self.enabled = False
                self._time = MAX_TELEOP_TIME

    # --- Program date --- #
    programLastUpdate_changed = Signal(str)
    @Property(str, notify=programLastUpdate_changed)
    def programLastUpdate(self) -> str:
        return self._program_last_update

    def set_program_date(self, date: str):
        if date is None:
            date = ""
        else:
            date = datetime.strptime(date, "%Y%m%d%H%M%S")
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

    #====================#

    @Slot(QObject)
    def install_event_filter(self, obj: QObject):
        obj.installEventFilter(self)

    def eventFilter(self, source: QObject, event):
        if not self.capture_keyboard:
            return False

        if event.type() in (QKeyEvent.KeyPress, QKeyEvent.KeyRelease):
            press = event.type() == QKeyEvent.KeyPress
            if event.isAutoRepeat():
                return True
            if event.key() == Qt.Key_Space:
                if press:
                    self.enabled = False
            elif event.key() == Qt.Key_Return:
                if press:
                    self.enabled = True
            else:
                return self._keyboard_controller.key_event(event)
            return True

        return False


class RobotMode(str, Enum):
    AUTO = 'Autonomous'
    TELEOP = 'Teleoperated'
    TEST = 'Test'

    @staticmethod
    def from_index(index: int) -> RobotMode:
        return {
            1: RobotMode.AUTO,
            2: RobotMode.TELEOP,
            3: RobotMode.TEST
        }[index]


class RobotStatus(str, Enum):
    ENABLED = 'Enabled'
    DISABLED = 'Disabled'
    IDLE = 'Idle'


class ProgramStatus(str, Enum):
    IDLE = 'Idle'
    STARTING = 'Starting'
    RUNNING = 'Running'