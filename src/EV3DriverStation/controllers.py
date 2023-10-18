from __future__ import annotations

__all__ = ["ControllersManager", "Controller", "ControllerState"]

from typing import NamedTuple

import pygame
from PySide6.QtCore import Property, QObject, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QKeyEvent


class ControllersManager(QObject):
    def __init__(self, list_refresh_rate=1000):
        super().__init__()
        self.keyboard_controller = Keyboard()
        self.controllers = []
        self._pilot1ControllerId = None
        self._pilot2ControllerId = None
        self._pilot1State = ControllerState()
        self._pilot1StateDict = None
        self._pilot2State = ControllerState()
        self._pilot2StateDict = None

        self.list_refresh_timer = QTimer(self)
        self.list_refresh_timer.timeout.connect(self.refresh_controllers_list)
        self.state_refresh_timer = QTimer(self)
        self.state_refresh_timer.setInterval(10)
        self.state_refresh_timer.timeout.connect(self.refresh_pilot_controllers_state)

        self._list_refresh_rate = list_refresh_rate
        self._states = None
        self._states_dirty = False

    def init_pygame(self):
        pygame.init()
        pygame.joystick.init()
        self.list_refresh_timer.start(self._list_refresh_rate)
        self.state_refresh_timer.start()

    def quit_pygame(self):
        pygame.quit()

    #===================#
    #== Refresh Slots ==#
    #===================#
    @Slot()
    def refresh_controllers_list(self):
        # Remember previous controllers guid
        previousGuid = {j.guid for j in self.controllers}
        pilotsGuid = self.get_pilot_controllers_guid()

        # Update detected controllers
        joysticks = []
        for i in range(pygame.joystick.get_count()):
            try:
                joystick = pygame.joystick.Joystick(i)
                joystick.init()
                joystick.get_name() 
                # I had a weird crash here when hibernating the computer with a controller plugged in
                # and then waking it up with the controller unplugged.
                # Pygame still register the controller but get_name() crashes without exception...
            except pygame.error:
                pass
            else:
                joysticks.append(Controller(joystick))

        # Sort by GUID to keep the same order
        self.controllers = sorted(joysticks, key=lambda j: j.guid) 

        # Update current controllers
        currentGuid = [j.guid for j in self.controllers]
        lostGuid = previousGuid - set(currentGuid)
        newGuid = set(currentGuid) - previousGuid

        if lostGuid or newGuid:
            self.namesChanged.emit()

        # Remove lost controllers
        pilotsGuid = [None if guid in lostGuid else guid for guid in pilotsGuid]

        # Assign new controllers to empty slots
        for i, guid in enumerate(pilotsGuid):
            if not newGuid:
                break
            if guid is None:
                pilotsGuid[i] = newGuid.pop()

        # Translate pilot guid back to controller index
        def guid2index(guid):
            if guid is None:
                return None
            elif guid == "KEYBOARD":
                return 0
            try:
                return currentGuid.index(guid) + 1
            except ValueError:
                return None

        p1_id = guid2index(pilotsGuid[0])
        p2_id = guid2index(pilotsGuid[1])

        self.list_refresh_timer.start()

        # Update QML
        if self._pilot1ControllerId != p1_id:
            self._pilot1ControllerId = p1_id
            self.pilot1ControllerIdChanged.emit()
        if self._pilot2ControllerId != p2_id:
            self._pilot2ControllerId = p2_id
            self.pilot2ControllerIdChanged.emit()

    @Slot()
    def refresh_pilot_controllers_state(self):
        p1 = self.pilot1Controller
        p2 = self.pilot2Controller
        if p1 is None and p2 is None:
            return

        p1LastState = self._pilot1State
        p2LastState = self._pilot2State

        pygame.event.pump()
        if p1 is not None:
            p1State = p1.get_state(pump_event=False)
            if p1State != p1LastState:
                self._setPilot1State(p1State)
        if p2 is not None:
            p2State = p2.get_state(pump_event=False)
            if p2State != p2LastState:
                self._setPilot2State(p2State)
        
        self.state_refresh_timer.start()

    @Slot(int, int)
    def set_pilot_controllerId(self, pilotId: int, controllerId: int):
        if controllerId == -1:
            controllerId = None
        p1, p2 = self._pilot1ControllerId, self._pilot2ControllerId

        # Swap controllers logic
        if pilotId == 0:
            if self._pilot2ControllerId == controllerId:
                self._pilot2ControllerId = self._pilot1ControllerId
            self._pilot1ControllerId = controllerId
        elif pilotId == 1:
            if self._pilot1ControllerId == controllerId:
                self._pilot1ControllerId = self._pilot2ControllerId
            self._pilot2ControllerId = controllerId

        # Notify QML
        if p1 != self._pilot1ControllerId:
            self.pilot1ControllerIdChanged.emit()
        if p2 != self._pilot2ControllerId:
            self.pilot2ControllerIdChanged.emit()

    #===========================#
    #== Controllers Accessors ==#
    #===========================#
    @property
    def pilot1Controller(self) -> Controller | None:
        return self.get_controller_by_id(self._pilot1ControllerId)

    @property
    def pilot2Controller(self) -> Controller | None:
        return self.get_controller_by_id(self._pilot2ControllerId)

    def get_pilot_controllers_states(self, refresh=True) -> tuple[ControllerState, ControllerState]:
        if refresh:
            self.refresh_pilot_controllers_state()
        return (self._pilot1State, self._pilot2State)

    def get_pilot_controllers_guid(self) -> list[str, str]:
        p1, p2 = self.pilot1Controller, self.pilot2Controller
        p1_guid = None if p1 is None else p1.guid
        p2_guid = None if p2 is None else p2.guid
        return [p1_guid, p2_guid]

    def get_controller_by_id(self, controllerId: int | None) -> Controller | None:
        if controllerId is None or  not (0 <= controllerId <= len(self.controllers)):
            return None
        if controllerId == 0:
            return self.keyboard_controller
        return self.controllers[controllerId - 1]

    #====================#
    #== QML PROPERTIES ==#
    #====================#
    # --- Pilot 1 controller --- #
    pilot1ControllerIdChanged = Signal()
    @Property(int, notify=pilot1ControllerIdChanged)
    def pilot1ControllerId(self) -> int:
        return self._pilot1ControllerId if self._pilot1ControllerId is not None else -1

    @pilot1ControllerId.setter
    def pilot1ControllerId(self, controllerId: int):
        self.update_pilot_controller(0, controllerId)
    

    # --- Pilot 2 controller --- #
    pilot2ControllerIdChanged = Signal()
    @Property(int, notify=pilot2ControllerIdChanged)
    def pilot2ControllerId(self)-> int:
        return self._pilot2ControllerId if self._pilot2ControllerId is not None else -1

    @pilot2ControllerId.setter
    def pilot2ControllerId(self, controllerId: int):
        self.update_pilot_controller(1, controllerId)

    # --- Controllers names --- #
    namesChanged = Signal()
    @Property(list, notify=namesChanged)
    def names(self) ->list[str]:
        return [j.name for j in self.controllers]

    # --- Controllers states --- #
    pilot1StateChanged = Signal()
    @Property(dict, notify=pilot1StateChanged)
    def pilot1State(self):
        if self._pilot1StateDict is None:
            self._pilot1StateDict = self._pilot1State.as_dict()
        return self._pilot1StateDict

    def _setPilot1State(self, state: ControllerState):
        self._pilot1State = state
        self._pilot1StateDict = None
        self.pilot1StateChanged.emit()

    pilot2StateChanged = Signal()
    @Property(dict, notify=pilot2StateChanged)
    def pilot2State(self):
        if self._pilot2StateDict is None:
            self._pilot2StateDict = self._pilot2State.as_dict()
        return self._pilot2StateDict

    def _setPilot2State(self, state: ControllerState):
        self._pilot2State = state
        self._pilot2StateDict = None
        self.pilot2StateChanged.emit()

    @Property(bool, notify=pilot1StateChanged)
    def isPilot1ControllerActive(self):
        return not self._pilot1State.is_neutral()

    @Property(bool, notify=pilot2StateChanged)
    def isPilot2ControllerActive(self):
        return not self._pilot2State.is_neutral()


class ControllerState(NamedTuple):
    leftX: float = 0
    leftY: float = 0
    rightX: float = 0
    rightY: float = 0
    leftTrigger: float = -1
    rightTrigger: float = -1

    A: bool = False
    B: bool = False
    X: bool = False
    Y: bool = False
    LeftBumper: bool = False
    RightBumper: bool = False
    Back: bool = False
    Start: bool = False
    LeftStick: bool = False
    RightStick: bool = False
    Left: bool = False
    Right: bool = False
    Up: bool = False
    Down: bool = False

    @property
    def axis(self) -> tuple[float, ...]:
        return self[:6]

    @property
    def buttons(self) -> tuple[bool, ...]:
        return self[6:]

    def is_neutral(self) -> bool:
        return self == ControllerState()

    def with_deadzone(self, deadzone=.05) -> ControllerState:
        return self._replace(
            leftX=self.leftX if abs(self.leftX) > deadzone else 0,
            leftY=self.leftY if abs(self.leftY) > deadzone else 0,
            rightX=self.rightX if abs(self.rightX) > deadzone else 0,
            rightY=self.rightY if abs(self.rightY) > deadzone else 0,
            leftTrigger=self.leftTrigger if self.leftTrigger > deadzone-1 else -1,
            rightTrigger=self.rightTrigger if self.rightTrigger > deadzone-1 else -1,
        )

    def is_same(self, other: ControllerState, axis_tolerance=.05) -> bool:
        return  self.buttons == other.buttons and \
                all(abs(a - b) <= axis_tolerance for a, b in zip(self.axis, other.axis, strict=True))

    def as_dict(self) -> dict[str, float | bool]:
        return self._asdict()

class Controller:
    def __init__(self, joystick: pygame.joystick.Joystick):
        self.joystick = joystick

    @property
    def name(self) -> str:
        return self.joystick.get_name()

    @property
    def guid(self) -> str:
        return self.joystick.get_guid()
    
    def get_state(self, pump_event=True) -> ControllerState:
        if pump_event:
            pygame.event.pump()

        hats = [self.joystick.get_hat(i) for i in range(self.joystick.get_numhats())]
        buttons = [self.joystick.get_button(i) for i in range(self.joystick.get_numbuttons())]
        axes = [self.joystick.get_axis(i) for i in range(self.joystick.get_numaxes())]

        if len(buttons) in (16, 17) and len(hats) == 0:
            # PS5 / PS4 controller
            state = ControllerState(
                leftX=axes[0],
                leftY=axes[1],
                rightX=axes[2],
                rightY=axes[3],
                leftTrigger=axes[4],
                rightTrigger=axes[5],
                
                A=buttons[0],
                B=buttons[1],
                X=buttons[2],
                Y=buttons[3],
                LeftBumper=buttons[9],
                RightBumper=buttons[10],
                Back=buttons[4],
                Start=buttons[6],
                LeftStick=buttons[7],
                RightStick=buttons[8],
                Left=buttons[13],
                Right=buttons[14],
                Up=buttons[11],
                Down=buttons[12],
            )
        elif hats:
            # Default Xbox controller
            state = ControllerState(
                leftX=axes[0],
                leftY=axes[1],
                rightX=axes[2],
                rightY=axes[3],
                leftTrigger=axes[4],
                rightTrigger=axes[5],

                A=buttons[0],
                B=buttons[1],
                X=buttons[2],
                Y=buttons[3],
                LeftBumper=buttons[4],
                RightBumper=buttons[5],
                Back=buttons[6],
                Start=buttons[7],
                LeftStick=buttons[8],
                RightStick=buttons[9],
                Left=hats[0][0]<0,
                Right=hats[0][0]>0,
                Up=hats[0][1]>0,
                Down=hats[0][1]<0,
            )
        else:
            state = ControllerState(
                    leftX=axes[0],
                    leftY=axes[1],
                    rightX=axes[2],
                    rightY=axes[3],
                    leftTrigger=axes[4],
                    rightTrigger=axes[5],

                    A=buttons[0],
                    B=buttons[1],
                    X=buttons[2],
                    Y=buttons[3],
                    LeftBumper=buttons[4],
                    RightBumper=buttons[5],
                    Back=buttons[6],
                    Start=buttons[7],
                    LeftStick=buttons[8],
                    RightStick=buttons[9],
                )
        return state.with_deadzone()


class Keyboard(Controller):
    def __init__(self, axes_strength=1):
        super().__init__(None)
        self.axes_strength = axes_strength
        self.state = ControllerState()

    @property
    def name(self) -> str:
        return "Keyboard"

    @property
    def guid(self) -> str:
        return "KEYBOARD"
    
    def get_state(self, pump_event=True) -> ControllerState:
        return self.state

    def key_event(self, event: QKeyEvent):
        if event.isAutoRepeat():
            return True

        s = self.state
        press = event.type() == QKeyEvent.KeyPress

        def update_axis(axis, positiveKey: bool):
            v = getattr(s, axis)
            v += self.axes_strength * (1 if positiveKey else -1) * (1 if press else -1)
            v = max(-self.axes_strength, min(self.axes_strength, v))
            return s._replace(**{axis: v})

        match event.key():
            case Qt.Key_Right | Qt.Key_Left:
                s = update_axis('rightX', event.key() == Qt.Key_Right)
            case Qt.Key_Up | Qt.Key_Down:
                s = update_axis('rightY', event.key() == Qt.Key_Down)
            case Qt.Key_D | Qt.Key_A:
                s = update_axis('leftX', event.key() == Qt.Key_D)
            case Qt.Key_W | Qt.Key_S:
                s = update_axis('leftY', event.key() == Qt.Key_S)

            case Qt.Key_Z:
                s = s._replace(leftTrigger=self.axes_strength if press else -1)
            case Qt.Key_C:
                s = s._replace(rightTrigger=self.axes_strength if press else -1)
            
            case Qt.Key_B:
                s = s._replace(A=press)
            case Qt.Key_H:
                s = s._replace(B=press)
            case Qt.Key_G:
                s = s._replace(X=press)
            case Qt.Key_Y:
                s = s._replace(Y=press)
            case Qt.Key_Q:
                s = s._replace(LeftBumper=press)
            case Qt.Key_E:
                s = s._replace(RightBumper=press)
            case Qt.Key_Insert:
                s = s._replace(Back=press)
            case Qt.Key_Delete:
                s = s._replace(Start=press)
            case Qt.Key_X:
                s = s._replace(LeftStick=press)
            case Qt.Key_M:
                s = s._replace(RightStick=press)

            case Qt.Key_J:
                s = s._replace(Left=press)
            case Qt.Key_L:
                s = s._replace(Right=press)
            case Qt.Key_I:
                s = s._replace(Up=press)
            case Qt.Key_K:
                s = s._replace(Down=press)
                
            case _:
                return False

        self.state = s
        return True
        