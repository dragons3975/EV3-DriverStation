import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts
import QtQuick.Controls.Material 2.15

import "CustomUI/"

Rectangle {
    width: 1000
    height: 300

    id: root

    color: Material.backgroundColor

    component ControllerSelector: Pane {
        id: controllerSelector
        property int controllerId: 0
        property string controllerName: ""

        anchors.right: parent.right
        anchors.left: parent.left
        height: 40

        Label {
            anchors.left: parent.left
            anchors.right: b1.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            verticalAlignment: Text.AlignVCenter
            text: controllerName
        }

        RadioButton {
            id: b1
            checked: controllerId === controllers.pilot1ControllerId
            width: 35
            anchors.right: b2.left
            anchors.rightMargin: 10
            anchors.verticalCenter: parent.verticalCenter
            onClicked: controllers.set_pilot_controllerId(0, controllerId)
        }

        RadioButton {
            id: b2
            checked: controllerId === controllers.pilot2ControllerId
            width: 35
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            onClicked: controllers.set_pilot_controllerId(1, controllerId)
        }
    }


    RowLayout {
        anchors.fill: parent
        spacing: 20
        anchors.margins: 5

        ColumnLayout {
            Layout.fillHeight: true
            Layout.fillWidth: true
            Layout.horizontalStretchFactor: 4

            Header{
                text: qsTr("Detected Controllers")

                HeaderButton {
                    text: "⟳"
                    tooltip: qsTr("Refresh Controllers List")
                    onClicked: controllers.refresh_controllers_list()
                }
            }
            /*
            RowLayout {
                Layout.fillWidth: true

                Label {
                    Layout.fillWidth: true
                    text: "Detected Controllers"
                    leftPadding: 30
                    font.bold: true
                    font.pixelSize: 17
                }

                ToolButton {
                    text: "⟳"
                    font.bold: true
                    font.pixelSize: 20
                    Layout.minimumWidth: parent.height
                    onClicked: controllers.refresh_controllers_list()
                }
            }
            */

            Item{
                height: 7
                Layout.fillWidth: true
            }

            Rectangle {
                Layout.fillWidth: true
                height: 45

                color: Material.backgroundColor

                Pane {
                    anchors.fill: parent
                    anchors.bottomMargin: 5
                    Material.background: Material.primaryColor
                    Material.roundedScale: Material.SmallScale
                    Material.elevation: 4

                    RowLayout {
                        anchors.fill: parent
                        spacing: 10

                        Label {
                            leftPadding: 10
                            verticalAlignment: Text.AlignVCenter
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            text: qsTr("Controller Name")
                            font.bold: true
                        }

                        Label {
                            id: labelP1
                            text: "P1"
                            Layout.fillHeight: true
                            Layout.minimumWidth: 35
                            Layout.maximumWidth: 35
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            font.bold: true
                        }

                        Label {
                            id: labelP2
                            text: "P2"
                            Layout.fillHeight: true
                            Layout.minimumWidth: 35
                            Layout.maximumWidth: 35
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            font.bold: true
                        }
                    }
                }
            }

            ListView {
                Layout.fillHeight: true
                Layout.fillWidth: true
                clip: true

                id: listView
                model: controllers.names
                spacing: 5

                delegate: ControllerSelector {
                    controllerId: index + 1
                    controllerName: modelData
                }

                Label {
                    anchors.fill: parent
                    text: qsTr("No controllers detected")
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    visible: controllers.names.length === 0
                }
            }

            Item {
                height: 40
                Layout.minimumHeight: height
                Layout.maximumHeight: height
                Layout.fillWidth: true

                ControllerSelector {
                    controllerId: 0
                    controllerName: qsTr("Keyboard <i>(Emulate Controller)</i>")

                    anchors.fill: parent
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

            ControllerView {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.verticalCenter
                anchors.bottomMargin: 5

                pilotId: 0
                controllerEnabled: controllers.pilot1ControllerId !== -1
                isKeyboard: controllers.pilot1ControllerId === 0
            }

            ControllerView {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                anchors.top: parent.verticalCenter
                anchors.topMargin: 5

                pilotId: 1
                controllerEnabled: controllers.pilot2ControllerId !== -1
                isKeyboard: controllers.pilot2ControllerId === 0
            }
        }
    }
}
