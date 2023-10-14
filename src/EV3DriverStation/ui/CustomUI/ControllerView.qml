

/*
This is a UI file (.ui.qml) that is intended to be edited in Qt Design Studio only.
It is supposed to be strictly declarative and only uses a subset of QML. If you edit
this file manually, you might introduce QML code that is not supported by Qt Design Studio.
Check out https://doc.qt.io/qtcreator/creator-quick-ui-forms.html for details on .ui.qml files.
*/
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Effects
import QtQuick.Layouts
import QtQuick.Controls.Material 2.15

Rectangle {
    width: 640
    height: 145

    color: Material.background

    property bool controllerEnabled: true
    property int pilotId: 0
    property bool isKeyboard: false

    component ButtonHighlight: Rectangle {
        property string buttonName: ""
        property string shortcut: ""

        radius: 8
        height: radius*2
        width: height
        
        color: Material.accentColor

        ToolTip.visible: buttonName ? maButton.containsMouse : false
        ToolTip.text: buttonName + ( (isKeyboard && shortcut !== "") ? "  [<i>" + shortcut + "</i>]" : "") 

        opacity: controllers.states[pilotId][buttonName] ? 1 : .05

        MouseArea {
            id: maButton
            anchors.fill: parent
            hoverEnabled: true
        }
    }

    component SvgHighlight: MultiEffect {
        property string buttonName: ""
        property string shortcut: ""

        source: buttonName.endsWith('Bumper') ? bumperImage : triggerImage
        colorization: 1.0
        colorizationColor: Material.accentColor

        opacity: controllers.states[pilotId][buttonName] ? 1 : .05

        ToolTip.visible: buttonName ? maSvg.containsMouse : false
        ToolTip.text: buttonName + ( (isKeyboard && shortcut !== "") ? "  [<i>" + shortcut + "</i>]" : "") 

        width: source.width
        height: source.height

        transform: Scale{ xScale: buttonName.startsWith('Left') ? 1 : -1 }

        MouseArea {
            id: maSvg
            anchors.fill: parent
            hoverEnabled: true
        }
    }

    function formatAxisValue(value: float) {
        return (value>=0?'+':'') + value.toFixed(2)
    }

    Image {
        id: bumperImage
        source: "../assets/bumper.svg"
        height: 19
        fillMode: Image.PreserveAspectFit
        antialiasing: true
        visible: false
    }

    Image {
        id: triggerImage
        source: "../assets/trigger.svg"
        height: 25
        fillMode: Image.PreserveAspectFit
        antialiasing: true
        visible: false
    }

    component ColoredLabel: Label {
        color: controllerEnabled ? Material.foreground : Material.iconDisabledColor
    }

    Image {
        id: controllerImage
        source: "../assets/xbox.svg"
        anchors.left: parent.left
        anchors.leftMargin: 5
        anchors.verticalCenter: parent.verticalCenter
        height: 135
        fillMode: Image.PreserveAspectFit
        antialiasing: true
        visible: false
    }

    MultiEffect {
        source: controllerImage
        anchors.fill: controllerImage
        colorization: 1.0
        colorizationColor: Material.foreground
        opacity: controllerEnabled ? 1 : .2
        z: 10
    }

    ButtonHighlight {
        buttonName: 'Y'
        shortcut: 'Y'
        x: 194; y: 20
    }

    ButtonHighlight {
        buttonName: 'X'
        shortcut: 'G'
        x: 178; y: 35
    }

    ButtonHighlight {
        buttonName: 'A'
        shortcut: 'F'
        x: 194; y: 51
    }

    ButtonHighlight {
        buttonName: 'B'
        shortcut: 'V'
        x: 210; y: 35
    }

    ButtonHighlight {
        buttonName: 'Back'
        shortcut: 'Insert'
        radius: 5.5
        x: 120; y: 36
    }

    ButtonHighlight {
        buttonName: 'Start'
        shortcut: 'Delete'
        radius: 5.5
        x: 155; y: 36
    }

    /*
    ButtonHighlight {
        id: buttonLogitech
        buttonName: 'Logitech'
        radius: 3
        width: 15

        x: 134; y: 51
    }
    */

    ButtonHighlight {
        id: leftJoystick
        buttonName: 'Left Joystick'
        shortcut: '← / → / ↑ / ↓ '

        opacity: controllers.states[pilotId]['leftX']**2 + controllers.states[pilotId]['leftY']**2 > 0.1 ? 1 : .05
        radius: 12.5
        color: Material.primaryColor
        x: 70; y: 30
    }

    ButtonHighlight {
        id: buttonLeftStick
        buttonName: 'LeftStick'
        shortcut: 'X'

        opacity: 1
        color: controllers.states[pilotId]['LeftStick'] ? Material.accentColor : Material.backgroundColor

        radius: 8
        x: 74; y: 34
    }

    ButtonHighlight {
        id: rightJoystick
        buttonName: 'Right Joystick'
        shortcut: 'W / A / S / D'

        opacity: controllers.states[pilotId]['rightX']**2 + controllers.states[pilotId]['rightY']**2 > 0.1 ? 1 : .05
        radius: 12.5
        color: Material.primaryColor
        x: 161; y: 66
    }

    ButtonHighlight {
        id: buttonRightStick
        buttonName: 'RightStick'
        shortcut: 'M'

        opacity: 1
        color: controllers.states[pilotId]['RightStick'] ? Material.accentColor : Material.backgroundColor
        
        radius: 8
        x: 165; y: 70
    }

    ButtonHighlight {
        id: buttonLeft
        buttonName: 'Left'
        shortcut: 'J'

        radius: 1
        height: 11
        x: 95; y: 75
    }

    ButtonHighlight {
        id: buttonTop
        buttonName: 'Up'
        shortcut: 'I'

        radius: 1
        height: 11
        x: 106; y: 64
    }

    ButtonHighlight {
        id: buttonRight
        buttonName: 'Right'
        shortcut: 'L'

        radius: 1
        height: 11
        x: 117; y: 75
    }

    ButtonHighlight {
        id: buttonDown
        buttonName: 'Down'
        shortcut: 'K'

        radius: 1
        height: 11
        x: 106; y: 86
    }

    SvgHighlight {
        id: leftTrigger
        buttonName: 'LeftTrigger'
        shortcut: 'Z'

        colorizationColor: Material.primaryColor
        opacity: controllers.states[pilotId]['leftTrigger'] > -0.9 ? 1 : .05
        x: 10; y: 24
    }

    SvgHighlight {
        id: buttonLeftBumper
        buttonName: 'LeftBumper'
        shortcut: 'Q'

        x: 7; y: -2
    }

    SvgHighlight {
        id: rightTrigger
        buttonName: 'RightTrigger'
        shortcut: 'C'

        colorizationColor: Material.primaryColor
        opacity: controllers.states[pilotId]['rightTrigger'] > -0.9 ? 1 : .05
        x: 274; y: 24
    }

    SvgHighlight {
        id: buttonRightBumper
        buttonName: 'RightBumper'
        shortcut: 'E'

        x: 277; y: -2
    }

    ColumnLayout {
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.left: controllerImage.right
        anchors.right: parent.right
        anchors.margins: 5
        anchors.leftMargin: 20

        Label {
            Layout.fillWidth: true
            text: "Pilot " + (pilotId+1)
            leftPadding: 30
            font.bold: true
            font.pixelSize: 17
            color: controllerEnabled ? Material.foreground : Material.iconDisabledColor
        }

        GridLayout {
            Layout.fillHeight: true
            Layout.fillWidth: true

            columns: 5

            ColoredLabel {
                text: 'Left X'
                Layout.fillWidth: true
            }
            ColoredLabel {
                Layout.maximumWidth: 50
                Layout.minimumWidth: 50
                text: formatAxisValue(controllers.states[pilotId]['leftX'])
            }

            Rectangle {
                Layout.rowSpan: 3
                Layout.fillHeight: true
                width: 1
                color: Material.frameColor
            }

            ColoredLabel {
                Layout.fillWidth: true
                text: 'Right X'
            }
            ColoredLabel {
                Layout.maximumWidth: 50
                Layout.minimumWidth: 50
                text: formatAxisValue(controllers.states[pilotId]['rightX'])
            }

            ColoredLabel {

                text: 'Left Y'
            }
            ColoredLabel {
                text: formatAxisValue(controllers.states[pilotId]['leftY'])
            }

            ColoredLabel {
                text: 'Right Y'
            }
            ColoredLabel {
                text: formatAxisValue(controllers.states[pilotId]['rightY'])
            }

            ColoredLabel {
                text: 'Left Trigger'
            }

            ColoredLabel {
                text: formatAxisValue(controllers.states[pilotId]['leftTrigger'])
            }

            ColoredLabel {
                text: 'Right Trigger'
            }

            ColoredLabel {
                text: formatAxisValue(controllers.states[pilotId]['rightTrigger'])
            }
        }
    }
}
