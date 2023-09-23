import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts

Rectangle {
    width: 1000
    height: 300

    id: root
    color: Material.backgroundColor

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
                        text: "Robot IP Adress"
                        leftPadding: 30
                        font.bold: true
                        font.pixelSize: 17
                    }
                }
                Item {
                    Layout.fillWidth: true
                    height: 10
                }

                ListView {
                    id: listIP

                    Layout.fillHeight: true
                    Layout.fillWidth: true
                    spacing: 2

                    Material.background: Material.frameColor

                    model: network.availableIPs
                    delegate: Component {
                        Rectangle {
                            property bool selected: network.robotIP===modelData
                            height: 30
                            radius: 15
                            width: parent.width

                            color: network.robotIP===modelData ? Material.accentColor : Material.frameColor

                            Label { 
                                id: label
                                anchors.fill: parent
                                anchors.right: deleteButton.left

                                text: modelData 
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter

                                font.bold: selected
                            }
                            MouseArea {
                                anchors.fill: label
                                onClicked: network.robotIP = modelData
                            }

                            Button {
                                id: deleteButton
                                flat: true
                                icon.source: "delete.svg"
                                onClicked: network.removeIP(modelData)

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
                    id: ip
                    Layout.fillWidth: true
                    Layout.maximumHeight: 35
                    horizontalAlignment: Text.AlignHCenter

                    placeholderText: "Manual IP"
                    text: "192.168.0.0"
                    onAccepted: {
                        network.addIP(ip.text)
                        network.robotIP = ip.text
                        ip.text = "192.168.0.0"
                    }
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
        }
    }
}
