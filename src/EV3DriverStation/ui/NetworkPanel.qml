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
                
                Header {
                    text: qsTr("Robot IP Adresses")
                    HeaderButton{
                        visible: network.connectionStatus !== "Disconnected"
                        source: "assets/disconnect.svg"
                        tooltip: "Disconnect from robot"
                        onClicked: disconnectConfirmation.safeSetAddress("")
                    }
                }

                /*
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
                */

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

                    placeholderText: qsTr("Manual IP")
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

            Header {
                text: qsTr("Network Settings")

                HeaderButton{
                    visible: network.connectionStatus === "Connected"
                    source: network.muteUdpRefresh ? "assets/play.svg" : "assets/pause.svg"
                    tooltip: network.muteUdpRefresh ? "Resume UDP" : "Mute UDP"
                    onClicked: network.muteUdpRefresh = !network.muteUdpRefresh
                }
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
                        name: qsTr("Connection status")
                        value:{
                            switch(network.connectionStatus){
                                case "Connected": return qsTr("Connected")
                                case "Authenticating": return qsTr("Authenticating")
                                case "Check Available": return qsTr("Check Available")
                                case "Wait Available": return qsTr("Wait Available")
                                case "Setuping": return qsTr("Setuping")
                                case "Disconnected": return qsTr("Disconnected")
                            }
                        } 
                    }

                    Entry {
                        name: "Ping" 
                        value: network.ping
                        isNA: network.ping===0
                        suffix: " ms"
                    }

                    Entry {
                        name: qsTr("Average time between UDP sends")
                        value: network.udpAvgDt
                        isNA: network.udpAvgDt===0
                        suffix: " ms"
                    }

                    Item {
                        width: parent.width
                        height: 20
                    }

                    NetworkOption {
                        id: udpMaxRefreshRate
                        name: qsTr("UDP max refresh rate (ms)")
                        tooltip: qsTr("Time between UDP sends when the controllers state remains the same.")
                        value: network.maxUdpRefreshRate
                        minValue: 10
                        maxValue: 10000
                        stepSize: 10
                        onValueModified: (value) => {network.maxUdpRefreshRate = value}
                        editable: network.connectionStatus=="Connected" && !network.muteUdpRefresh
                        enabled: editable
                    }

                    NetworkOption {
                        id: udpMinRefreshRate
                        name: qsTr("UDP min refresh rate (ms)")
                        tooltip: qsTr("Time between UDP sends when the controllers state changes.")
                        value: network.minUdpRefreshRate !== 0 ? network.minUdpRefreshRate : network.maxUdpRefreshRate
                        minValue: 10
                        maxValue: udpMaxRefreshRate.value
                        stepSize: 10
                        onValueModified: (value) => {network.minUdpRefreshRate = value}
                        editable: network.connectionStatus=="Connected" && !telemetry.freezeTelemetry
                        enabled: editable && value < network.maxUdpRefreshRate && value > 0 
                    }

                    NetworkOption {
                        name: qsTr("Telemetry pull rate (ms)")
                        value: network.pullTelemetryRate
                        minValue: 50 
                        maxValue: 1000
                        stepSize: 100
                        onValueModified: (value) => {network.pullTelemetryRate = value}
                        editable: network.connectionStatus=="Connected" && !telemetry.freezeTelemetry
                        enabled: editable
                    }

                }
            }
        }
    }

    component NetworkOption: Item{
        id: networkOptionRoot
        property alias name: label.text
        property string tooltip: ""
        property double value: 30
        property bool enabled: true
        property bool editable: true
        property color color: enabled ? Material.foreground : Material.color(Material.Grey, Material.Shade500)
        property bool hovered: mouseArea.containsMouse

        signal valueModified(value: double)

        property alias minValue: spinbox.from
        property alias maxValue: spinbox.to
        property alias stepSize: spinbox.stepSize

        width: parent.width
        height: 25

        Rectangle{
            id: background
            anchors.fill: parent

            radius: height / 2

            color: Material.foreground
            opacity: hovered ? 0.1 : 0
            Behavior on opacity {
                NumberAnimation {
                    duration: 200
                }
            }
        }

        Label {
            id: label
            anchors.left: parent.left
            anchors.leftMargin: 10
            anchors.right: parent.horizontalCenter
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            verticalAlignment: Text.AlignVCenter

            text: ""
            font.pixelSize: networkOptionRoot.height * .5
            color: networkOptionRoot.color

            ToolTip.visible: parent.tooltip ? hovered : false
            ToolTip.text: parent.tooltip
        }

        MouseArea {
            id: mouseArea
            anchors.fill: parent
            onClicked: spinbox.forceActiveFocus()
            hoverEnabled: true
        }

        Item{
            anchors.right: parent.right
            anchors.left: parent.horizontalCenter
            anchors.top: parent.top
            anchors.bottom: parent.bottom

            SpinBox {
                id : spinbox
                height: networkOptionRoot.height
                anchors.centerIn: parent

                stepSize: 10
                validator: DoubleValidator {
                    bottom: Math.min(spinbox.from, spinbox.to)
                    top:  Math.max(spinbox.from, spinbox.to)
                }

                from: 0
                to: 100
                value : networkOptionRoot.value
                onValueModified: networkOptionRoot.valueModified(value)
                editable: networkOptionRoot.editable
                enabled: networkOptionRoot.editable

                font.pixelSize: networkOptionRoot.height * .6

                topPadding: 5
                bottomPadding: 3
                leftPadding: 0
                rightPadding: 0
            }
            
        }
    }
}
