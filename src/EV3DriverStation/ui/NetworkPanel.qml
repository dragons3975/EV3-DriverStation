import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts
import QtQuick.Dialogs

import "CustomUI/"

Rectangle {
    width: 1000
    height: 300

    id: root
    color: Material.backgroundColor

    MessageDialog {
        id: disconnectConfirmation

        property string nextAddress: ""
        property bool removeAddress: false

        function safeSetAddress(nextAddress, removeAddress = false) {
            disconnectConfirmation.nextAddress = nextAddress
            disconnectConfirmation.removeAddress = removeAddress

            if(network.connectionStatus !== "Disconnected") {
                disconnectConfirmation.open()
            } else {
                onAccepted()
            }
        }

        title: qsTr("You're about to be disconnected")
        text: qsTr("Are you sure you want to disconnect from the robot?")
        buttons: MessageDialog.Ok | MessageDialog.Cancel

        onAccepted: {
            if (removeAddress && network.connectionStatus !== "Disconnected")
                network.removeAddress(network.robotAddress)

            network.connectRobot(nextAddress) 
            if (nextAddress !== ""){
                network.addAddress(nextAddress)
                manualAddress.text = nextAddress
            }
        }
    }

    MessageDialog {
        id: connectionFailedDialog
        property string reason: ""

        title: qsTr("Connection failed") + ": " + reason

        Component.onCompleted: network.connectionFailed.connect(setAndOpenFailed)
        function setAndOpenFailed(reason, info){
            reason = reason
            informativeText = info
            connectionFailedDialog.open()
        }
    }

    MessageDialog {
        id: connectionLostDialog
        title: qsTr("Connection Lost")

        Component.onCompleted: network.connectionLost.connect(setAndOpenLost)
        function setAndOpenLost(ip, info){
            informativeText = info
            connectionLostDialog.open()
        }
    }

    RowLayout {
        anchors.fill: parent
        spacing: 10
        anchors.margins: 5

        Item {
            Layout.fillHeight: true
            Layout.minimumWidth: parent.width * 4/10

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                RowLayout {
                    Layout.fillWidth: true

                    Label {
                        id: robotIpHeaderLabel
                        Layout.fillWidth: true
                        text: "Robot IP Adress"
                        leftPadding: 30
                        font.bold: true
                        font.pixelSize: 17
                    }

                    ToolButton {
                        visible: network.connectionStatus !== "Disconnected"
                        icon.source: "assets/disconnect.svg"
                        icon.color: Material.foreground
                        ToolTip.visible: hovered
                        ToolTip.text: "Disconnect from robot"
                        flat: true
                        Layout.maximumHeight: robotIpHeaderLabel.height
                        Layout.minimumWidth: height
                        onClicked: disconnectConfirmation.safeSetAddress("")
                    }
                }

                Item {
                    Layout.fillWidth: true
                    height: 10
                }

                ListView {
                    id: listAddress

                    Layout.fillHeight: true
                    Layout.fillWidth: true
                    spacing: 2
                    clip: true

                    Material.background: Material.frameColor

                    model: network.availableAddresses
                    delegate: Component {
                        Rectangle {
                            property bool selected: network.robotAddress===modelData
                            height: 30
                            radius: 15
                            width: parent.width

                            color: network.robotAddress===modelData ? Material.accentColor : Material.frameColor

                            Label { 
                                id: label
                                anchors.fill: parent
                                anchors.right: deleteButton.left

                                text: modelData 
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter

                                font.bold: selected
                            }

                            IconNetworkStatus {
                                anchors.left: parent.left
                                anchors.leftMargin: 15
                                anchors.verticalCenter: parent.verticalCenter
                                height: parent.height-15
                                width: height * 1.3

                                visible: network.robotAddress===modelData
                                color: Material.foreground
                            }

                            MouseArea {
                                anchors.fill: label
                                onClicked: {
                                    if (network.robotAddress !== modelData)
                                        disconnectConfirmation.safeSetAddress(modelData)
                                }
                            }

                            Button {
                                id: deleteButton
                                flat: true
                                icon.source: "assets/delete.svg"
                                onClicked: {
                                    if (network.robotAddress === modelData)
                                        disconnectConfirmation.safeSetAddress("", true)
                                    else
                                        network.removeAddress(modelData)
                                }

                                topInset: 0
                                bottomInset: 0
                                anchors.right: parent.right
                                anchors.top: parent.top
                                anchors.bottom: parent.bottom
                                width: parent.height
                                topPadding: 10
                                bottomPadding: 10
                                leftPadding: 10
                                rightPadding: 10
                            }
                        }
                    }
                    focus: true
                }
                Item {
                    Layout.fillWidth: true
                    height: 10
                }

                TextField{
                    id: manualAddress
                    Layout.fillWidth: true
                    Layout.maximumHeight: 35
                    horizontalAlignment: Text.AlignHCenter

                    placeholderText: "Manual IP"
                    text: "192.168.0.0"
                    onAccepted: disconnectConfirmation.safeSetAddress(manualAddress.text)
                }
            }
        }

        ToolSeparator {
            id: toolSeparator
            Layout.fillHeight: true
        }

        ColumnLayout{
            Layout.fillHeight: true

            Label {
                Layout.fillWidth: true
                text: "Network Settings"
                leftPadding: 30
                font.bold: true
                font.pixelSize: 17
            }

            Item {
                Layout.fillWidth: true
                height: 20
            }

            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true

                Column{

                    anchors.fill: parent
                    anchors.leftMargin: 30
                    
                    Entry {
                        name: "Connection status" 
                        value: network.connectionStatus
                    }

                    Entry {
                        name: "Ping" 
                        value: network.ping
                        isNA: network.ping===0
                        suffix: " ms"
                    }

                    Entry {
                        name: "Average time between UDP sends" 
                        value: network.udpAvgDt
                        isNA: network.udpAvgDt===0
                        suffix: " ms"
                    }
                }
            }
        }
    }
}
