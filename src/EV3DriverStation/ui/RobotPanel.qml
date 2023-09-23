import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts

Rectangle {
    width: 1000
    height: 300

    id: root
    color: Material.backgroundColor

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
                            icon.source: "play.svg"
                            Material.background: Material.Green

                            enabled: robot.enabled
                            onClicked: robot.enabled = true
                        }
                        PlayStopButton{
                            id: stopButton
                            icon.source: robot.mode=="Autonomous" ? "stop.svg" : "pause.svg"
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

                Label {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "Not yet implemented"
                    leftPadding: 30
                    horizontalAlignment: Qt.AlignHCenter
                    verticalAlignment: Qt.AlignVCenter
                }
            }
        }
    }
}
