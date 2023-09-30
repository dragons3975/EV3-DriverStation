import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts

import "CustomUI/"

Rectangle {
    width: 1000
    height: 300

    id: root
    color: Material.backgroundColor

    DisableRect {
        visible: network.connectionStatus !== "Connected"
        text: "Robot is Disconnected"
    }

    property int modeButtonHeight: 40
    component ModeButton: Button {
        id: modeButton
        property string mode: ""

        property bool currentMode: robot.mode === mode
        
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

        onClicked: {
            robot.mode = mode
        }
    }

    component PlayStopButton: Button {
        property bool enabled: false

        icon.width: 50
        icon.height: 50

        Material.roundedScale: Material.SmallScale

        opacity: enabled ? 1 : 0.3
        Material.elevation: enabled ? 3 : -5

        width: height
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
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

        Item {
            Layout.fillHeight: true
            Layout.fillWidth: true
            Layout.horizontalStretchFactor: 4

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                RowLayout {
                    Layout.fillWidth: true

                    Label {
                        Layout.fillWidth: true
                        text: "Robot Mode"
                        leftPadding: 30
                        font.bold: true
                        font.pixelSize: 17
                    }
                }
                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                }
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
                        ModeButton {
                            mode: "Teleoperated"
                        }
                        ModeButton {
                            mode: "Test"
                        }
                    }
                }

                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                }

                Item{
                    Layout.fillWidth: true
                    Layout.minimumHeight: 60

                    Item{
                        anchors.fill: parent
                        PlayStopButton{
                            id: startButton
                            icon.source: "assets/play.svg"
                            Material.background: Material.Green

                            enabled: robot.enabled
                            onClicked: robot.enabled = true
                        }
                        PlayStopButton{
                            id: stopButton
                            icon.source: robot.mode=="Autonomous" ? "assets/stop.svg" : "assets/pause.svg"
                            Material.background: Material.Red
                            
                            enabled: !robot.enabled
                            onClicked: robot.enabled = false
                            
                            anchors.left: startButton.right
                        }

                        Label {
                            Layout.fillHeight: true
                            Layout.fillWidth: true

                            text: Qt.formatTime(new Date(robot.time*1000), 'mm:ss')
                            font.pixelSize: 30
                            horizontalAlignment: Qt.AlignHCenter
                            verticalAlignment: Qt.AlignVCenter

                            anchors.top: parent.top
                            anchors.bottom: parent.bottom
                            anchors.left: startButton.right
                            anchors.right: parent.right
                        }
                    }
                }

                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                }

                CheckBox {
                    text: "Auto-disable robot with timer"
                    font.pixelSize: 12
                    checked: robot.auto_disable
                    onCheckedChanged: {robot.auto_disable = checked}

                    height: 20
                    Layout.fillWidth: true
                    Layout.maximumHeight: height
                    Layout.minimumHeight: height
                }
            }

            
        }

        ToolSeparator {
            id: toolSeparator
            Layout.fillHeight: true
        }

        Item {
            Layout.fillHeight: true
            Layout.fillWidth: true
            Layout.horizontalStretchFactor: 5

            ColumnLayout {
                anchors.fill: parent
                Label {
                    Layout.fillWidth: true
                    text: "Telemetry"
                    leftPadding: 30
                    font.bold: true
                    font.pixelSize: 17
                }

                Item {
                    Layout.fillWidth: true
                    height: 10
                }

                ListView {
                    id: telemetryList
                    clip: true
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    model: telemetry.telemetryData

                    delegate: Entry {
                        width: telemetryList.width
                        name: modelData.key
                        value: modelData.value
                    }

                    Label{
                        anchors.centerIn: parent
                        anchors.verticalCenterOffset: -30
                        visible: network.connectionStatus === "Connected" &&  telemetry.telemetryStatus === "Unavailable"
                        text: {
                            if (telemetry.telemetryStatus === "Connecting") return "Connecting to Telemetry..."
                            else return "Telemetry is unavailable"
                        }
                    }

                    ScrollIndicator.vertical: ScrollIndicator { }
                }

                Row {
                    Layout.fillWidth: true

                    Entry {
                        width: parent.width / 2
                        name: "EV3 Voltage:"
                        value: telemetry.ev3Voltage.toFixed(2)
                        suffix: " V"
                        isNA: telemetry.ev3Voltage === 0
                        color: {
                            if (telemetry.ev3Voltage > 7) return Material.color(Material.LightGreen)
                            else if (telemetry.ev3Voltage > 6.7) return Material.color(Material.Orange)
                            else return Material.color(Material.Red)
                        }
                        alignValue: Text.AlignLeft
                    }

                    Entry {
                        width: parent.width / 2
                        name: "Auxilary Voltage:"
                        value: telemetry.auxVoltage.toFixed(2)
                        suffix: " V"
                        isNA: telemetry.auxVoltage === 0
                        color: {
                            if (telemetry.auxVoltage > 7) return Material.color(Material.LightGreen)
                            else if (telemetry.auxVoltage > 6) return Material.color(Material.Orange)
                            else return Material.color(Material.Red)
                        }
                        alignValue: Text.AlignLeft
                    }
                }

                Row {
                    Layout.fillWidth: true

                    Entry {
                        property bool ampere: telemetry.ev3Current > 1000
                        width: parent.width / 2
                        name: "EV3 Current:"
                        value: ampere ? (telemetry.ev3Current/1000).toFixed(2) : telemetry.ev3Current.toFixed(0)
                        suffix: ampere ? " A" : " mA"
                        isNA: telemetry.ev3Current === 0

                        alignValue: Text.AlignLeft
                    }
                    
                    Entry {
                        width: parent.width / 2
                        name: "CPU Load:"
                        value: (telemetry.cpu*100).toFixed(0)
                        suffix: "%"
                        isNA: telemetry.cpu === 0
                        color: {
                            if (telemetry.cpu < 60) return Material.color(Material.LightGreen)
                            if (telemetry.cpu < 80) return Material.color(Material.Orange)
                            else return Material.color(Material.Red)
                        }
                        alignValue: Text.AlignLeft
                    }

                }
                Entry{
                    Layout.fillWidth: true
                    name: "Program last Update:"
                    value: telemetry.programLastUpdate
                    alignValue: Text.AlignLeft
                    isNA: telemetry.programLastUpdate === ""
                }
            }
        }
    }
}
