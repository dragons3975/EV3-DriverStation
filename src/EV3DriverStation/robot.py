from __future__ import annotations

from enum import Enum

from PySide6.QtCore import Property, QObject, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QKeyEvent


class Robot(QObject):
    ip_changed = Signal(str)
    mode_changed = Signal(str)
    enabled_changed = Signal(bool)
    time_changed = Signal(int)
    auto_disable_changed = Signal(bool)

    def __init__(self, keyboard_controller):
        super().__init__()
        self._mode: RobotMode = RobotMode.TELEOP
        self._enabled: bool = False
        self._auto_disable: bool = False
        self._keyboard_controller = keyboard_controller
        self.capture_keyboard = False

        self.timer = QTimer()
        self.timer.timeout.connect(self.increment_timer)
        self._time = 0

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

    @Property(bool, notify=enabled_changed)
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, e: bool):
        if self._enabled == e:
            return

        self._enabled = e
        self.enabled_changed.emit(self._enabled)

        # Start/stop timer
        if e:
            self.start_timer()
        else:
            self.stop_timer()
            if self.mode == RobotMode.AUTO:
                self.reset_timer()

    @Property(bool, notify=auto_disable_changed)
    def auto_disable(self) -> bool:
        return self._auto_disable

    @auto_disable.setter
    def auto_disable(self, value: bool):
        self._auto_disable = value
        self.auto_disable_changed.emit(self._auto_disable)

    @Property(int, notify=time_changed)
    def time(self) -> int:
        return self._time

    def increment_timer(self):
        self._time += 1
        self.time_changed.emit(self._time)

        # Auto disable robot after 60 seconds in auto and 120 seconds in teleop
        if self.auto_disable:
            if self.mode == RobotMode.AUTO and self.time >= 60:
                self.enabled = False
            elif self.mode == RobotMode.TELEOP and self.time >= 120:
                self.enabled = False

    @Slot()
    def reset_timer(self):
        self._time = 0
        self.time_changed.emit(self._time)

    @Slot()
    def start_timer(self):
        self.timer.start(1000)

    @Slot()
    def stop_timer(self):
        self.timer.stop()

    @Slot(QObject)
    def install_event_filter(self, obj: QObject):
        obj.installEventFilter(self)

    def eventFilter(self, source: QObject, event):
        if not self.capture_keyboard:
            return False

        if event.type() in (QKeyEvent.KeyPress, QKeyEvent.KeyRelease):
            if event.key() == Qt.Key_Space:
                self.enabled = False
            elif event.key() == Qt.Key_Return:
                self.enabled = True
            else:
                return self._keyboard_controller.key_event(event)
            return True

        return False


class RobotMode(str, Enum):
    AUTO = 'Autonomous'
    TELEOP = 'Teleoperated'
    TEST = 'Test'

