import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Effects
import QtQuick.Layouts

import "CustomUI/"

Rectangle {
    width: 1000
    height: 300

    id: root
    color: Material.backgroundColor

    DisableRect {
        visible: network.connectionStatus !== "Connected"
        text: network.connectionStatus !== "Disconnected" ? qsTr("Connecting to Robot") : qsTr("Robot is Disconnected")
    }

    property int modeButtonHeight: 40
    component ModeButton: Button {
        id: modeButton
        property string mode: ""

        property bool currentMode: robot.mode === mode && robot.programStatus === "Running"
        
        text: mode
        height: modeButtonHeight
        Layout.fillWidth: true
        Layout.minimumHeight: height
        Layout.maximumHeight: height

        padding: 0
        bottomInset: 0
        topInset: 0

        Material.background: currentMode ? Material.accentColor : Material.frameColor
        Material.elevation: currentMode ? 5 : -5
        Material.roundedScale: Material.NotRounded

        font.bold: currentMode

        onClicked: if(robot.robotStatus !== "Idle") robot.mode = mode
    }

    component PlayStopButton: Button {
        property bool enabled: false

        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.left: parent.left

        height: parent.height
        width: height
        icon.width: height
        icon.height: height

        Material.roundedScale: Material.SmallScale

        opacity: enabled ? 1 : 0.3
        Material.elevation: enabled ? 3 : -5

        bottomInset: 0
        topInset: 0
        leftPadding: 15
        topPadding: 15
        rightPadding: 15
        bottomPadding:15
    }

    RowLayout {
        anchors.fill: parent
        spacing: 10
        anchors.margins: 5


        /********************************************
         *             Robot Mode Frame             *
         ********************************************/
        ColumnLayout {
            Layout.fillHeight: true
            Layout.fillWidth: true

            spacing: 0

            Header {
                text: qsTr("Robot Mode")
            }

            // === Robot program Frame ===
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true

                //  -- Warning Robot Program --
                Rectangle {
                    visible: robot.programStatus === 'Idle'

                    anchors.centerIn: parent
                    width: parent.width - 40
                    height: 30
                    radius: 15

                    color: Material.color(Material.Orange, Material.Shade500)
                    Image {
                        id: iconSource
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left: parent.left
                        anchors.leftMargin: 20
                        mipmap: true
                        source: "assets/warning.svg"
                        width: 21
                        height: 18
                        visible : false
                    }

                    MultiEffect {
                        anchors.fill: iconSource
                        source: iconSource
                        colorization: 1.0
                        colorizationColor: Material.color(Material.Orange, Material.Shade100)
                    }

                    Label {
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left: parent.left
                        anchors.leftMargin: 60
                        text: qsTr("Robot program is not running.")
                        font.pixelSize: 15
                        color: Material.foreground
                    }

                    SequentialAnimation on opacity {
                        loops: Animation.Infinite
                        running: true
                        PropertyAnimation { to: 0.5; duration: 750 ; easing.type: Easing.InOutQuad }
                        PropertyAnimation { to: 1;   duration: 750 ; easing.type: Easing.InOutQuad }
                    }
                }

                Rectangle {
                    visible: robot.programStatus === 'Starting'

                    anchors.centerIn: parent
                    width: parent.width - 40
                    height: 30
                    radius: 15

                    color: Material.accentColor

                    Label {
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left: parent.left
                        anchors.leftMargin: 60
                        text: qsTr("Robot program is starting.")
                        font.pixelSize: 15
                        color: Material.foreground
                    }

                    SequentialAnimation on opacity {
                        loops: Animation.Infinite
                        running: true
                        PropertyAnimation { to: 0.5; duration: 750 ; easing.type: Easing.InOutQuad }
                        PropertyAnimation { to: 1;   duration: 750 ; easing.type: Easing.InOutQuad }
                    }
                }

                Entry{
                    visible: robot.programStatus === 'Running'
                    name: qsTr("Program last Update:")
                    value: robot.programLastUpdate
                    isNA: robot.programLastUpdate === ""

                    anchors.centerIn: parent
                    height: 18
                    width: parent.width - 40
                }
            }

            // === Robot mode selector ===
            Item {
                Layout.fillWidth: true
                Layout.maximumHeight: modeButtonHeight * 3
                Layout.minimumHeight: modeButtonHeight * 3

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 0
                    ModeButton {
                        mode: "Autonomous"
                    }
                    Rectangle { width: parent.width; height: 2; color: Material.frameColor }
                    ModeButton {
                        mode: "Teleoperated"
                    }
                    Rectangle { width: parent.width; height: 2; color: Material.frameColor }
                    ModeButton {
                        mode: "Test"
                    }
                }
            }

            // === Spacer ===
            Item {
                Layout.fillWidth: true
                height: 20
            }

            // === Robot Enable/Disable frame ===
            Item{
                Layout.fillWidth: true
                height: 50

                // Enable button
                PlayStopButton{
                    id: startButton
                    icon.source: "assets/play.svg"
                    Material.background: Material.Green

                    enabled: robot.robotStatus === "Enabled"
                    onClicked: if (robot.robotStatus !== "Idle") robot.enabled = true
                }
                // Disable button
                PlayStopButton{
                    id: stopButton
                    icon.source: robot.mode=="Autonomous" ? "assets/stop.svg" : "assets/pause.svg"
                    Material.background: Material.Red
                    
                    enabled: robot.robotStatus === "Disabled"
                    onClicked: if (robot.robotStatus !== "Idle") robot.enabled = false

                    anchors.left: startButton.right
                }

                // Timer
                Label {
                    text: Qt.formatTime(new Date(robot.time*1000), 'mm:ss:') + (robot.time).toFixed(2).slice(-2)
                    font.pixelSize: 30
                    horizontalAlignment: Qt.AlignHCenter
                    verticalAlignment: Qt.AlignVCenter
                    
                    anchors.left: stopButton.right
                    anchors.leftMargin: 10
                    anchors.right: autoDisable.left
                    anchors.rightMargin: 10
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                }
                
                // Auto-disable
                Item{
                    id: autoDisable
                    width: 100
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom

                    Label{
                        id: autoDisableLabel
                        text: qsTr("Auto-disable")
                        font.pixelSize: 12

                        horizontalAlignment: Qt.AlignHCenter
                        verticalAlignment: Qt.AlignVCenter
                        anchors.top: parent.top
                        anchors.left: parent.left
                        anchors.right: parent.right
                    }
                    Switch{
                        checked: robot.auto_disable
                        onCheckedChanged: robot.auto_disable = checked

                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.top: autoDisableLabel.bottom
                        anchors.topMargin: 10
                        anchors.bottom: parent.bottom
                        width: 65
                        height: autoDisable.height - autoDisableLabel.height - 20
                    }
                }
            }
            
        }

        // === Central Separator ===
        Rectangle {
                Layout.fillHeight: true
                Layout.maximumWidth: width
                height: parent.height
                width: 1
                color: Material.frameColor
        }

        /********************************************
         *             Telemetry Frame              *
         ********************************************/
        ColumnLayout {
            Layout.fillHeight: true
            width: .55 * parent.width
            Layout.minimumWidth: width
            Layout.maximumWidth: width

            Header {
                text: qsTr("Telemetry")
            }

            // === Spacer ===
            Item {
                Layout.fillWidth: true
                height: 10
            }

            // === Telemetry List ===
            ListView {
                id: telemetryList
                clip: true
                Layout.fillWidth: true
                Layout.fillHeight: true

                model: telemetry.telemetryData

                delegate: Entry {
                    width: telemetryList.width
                    name: modelData.name
                    value: modelData.formattedValue
                    valueType: modelData.valueType
                    editable: modelData.editable
                    onValueEdited: (v) => {
                        if(!modelData.setValue(v))
                            invalidValue()
                    }
                }

                Label{
                    anchors.centerIn: parent
                    anchors.verticalCenterOffset: -30
                    visible: telemetry.telemetryTransmitted && telemetry.telemetryData.length === 0 
                    text: {
                        if (robot.programStatus !== "Running") return qsTr("Waiting for the robot program to start.")
                        else return qsTr('  No telemetry data received.\n\nTo send data to the driver station use: \n  Telemetry.putNumber("name", value); \n  Telemetry.putData("name", "value");')
                    }
                }

                ScrollIndicator.vertical: ScrollIndicator { }
            }

            // === Horizontal separator ===
            Rectangle {
                Layout.fillWidth: true
                Layout.maximumHeight: height
                width: parent.width
                height: 1
                color: Material.frameColor
            }

            // === Robot Performance Stats ===
            GridLayout {
                Layout.fillWidth: true
                columns: 3

                columnSpacing: 2
                rowSpacing: 3

                Entry {
                    property bool ampere: telemetry.ev3Current > 1000
                    tooltip: qsTr("Current drawn from the EV3 battery.")
                    name: qsTr("EV3 Current:")
                    value: ampere ? (telemetry.ev3Current/1000).toFixed(2) : telemetry.ev3Current.toFixed(0)
                    suffix: ampere ? " A" : " mA"
                    isNA: telemetry.ev3Current === 0
                    alignValue: Text.AlignLeft

                    Layout.fillWidth: true
                }

                Entry {
                    name: qsTr("EV3 Voltage:")
                    tooltip: qsTr("Voltage of the EV3 battery.")
                    value: telemetry.ev3Voltage.toFixed(2)
                    suffix: " V"
                    isNA: telemetry.ev3Voltage === 0
                    color: {
                        if (telemetry.ev3Voltage > 7.5) return Material.color(Material.LightGreen)
                        else if (telemetry.ev3Voltage > 7.2) return Material.color(Material.Orange)
                        else return Material.color(Material.Red)
                    }
                    alignValue: Text.AlignLeft

                    Layout.fillWidth: true
                }

                Entry {
                    name: qsTr("Aux. Voltage:")
                    tooltip: qsTr("Voltage of the external 12V battery.")
                    value: telemetry.auxVoltage.toFixed(2)
                    suffix: " V"
                    isNA: telemetry.auxVoltage === 0
                    color: {
                        if (telemetry.auxVoltage > 7) return Material.color(Material.LightGreen)
                        else if (telemetry.auxVoltage > 6) return Material.color(Material.Orange)
                        else return Material.color(Material.Red)
                    }
                    alignValue: Text.AlignLeft

                    Layout.fillWidth: true
                }

                Entry {
                    name: qsTr("Skipped Frame:")
                    tooltip: qsTr("Average number of frames skipped.")
                    value: (telemetry.skippedFrames).toFixed(1)
                    isNA: telemetry.skippedFrames === -1
                    color: {
                        if (telemetry.skippedFrames < 1) return Material.color(Material.LightGreen)
                        if (telemetry.skippedFrames < 4) return Material.color(Material.Orange)
                        else return Material.color(Material.Red)
                    }
                    alignValue: Text.AlignLeft

                    Layout.fillWidth: true
                }

                Entry {
                    name: qsTr("Compute Time:")
                    tooltip: qsTr("Average time to execute one frame.")
                    value: (telemetry.frameExecTime).toFixed(0)
                    suffix: "ms"
                    isNA: telemetry.frameExecTime < 0
                    color: {
                        if (telemetry.frameExecTime < 40) return Material.color(Material.LightGreen)
                        if (telemetry.frameExecTime < 100) return Material.color(Material.Orange)
                        else return Material.color(Material.Red)
                    }
                    alignValue: Text.AlignLeft

                    Layout.fillWidth: true
                }
                
                Entry {
                    name: qsTr("CPU Load:")
                    tooltip: qsTr("Average CPU load during the last minute.")
                    value: (telemetry.cpu*100).toFixed(0)
                    suffix: "%"
                    isNA: telemetry.cpu === 0
                    color: {
                        if (telemetry.cpu < 1.25) return Material.color(Material.LightGreen)
                        if (telemetry.cpu < 2) return Material.color(Material.Orange)
                        else return Material.color(Material.Red)
                    }
                    alignValue: Text.AlignLeft

                    Layout.fillWidth: true
                }
            }
        }
    }
}
