import QtQuick 2.15
import QtQuick.Layouts 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Effects

Control {
    id: icon

    property color color: {
        if (network.connectionStatus==='Disconnected') return Material.color(Material.Red, Material.Shade200)
        else if(network.connectionStatus!=='Connected') return Material.foreground
        else if (network.signalStrength <=1) return Material.color(Material.Red, Material.Shade200)
        else if (network.signalStrength <=3) return Material.color(Material.Orange, Material.Shade200)
        else return Material.color(Material.LightGreen, Material.Shade200)
    }

    width: 35
    height: 23

    property double animLoadingIndex: 1
    SequentialAnimation on animLoadingIndex{
        running: true
        loops: Animation.Infinite
        PropertyAnimation{to: 4; duration: 750; easing.type: Easing.Linear}
        PropertyAnimation{to: 1; duration: 750; easing.type: Easing.Linear}
    }

    component Bar: Rectangle {
        property int barID: 0
        height: icon.height * (barID + 1)/5

        Layout.alignment: Qt.AlignHCenter | Qt.AlignBottom

        id: barOuter
        width: icon.width / 5
        radius: 3

        color: {
            const c = icon.color
            if (network.connectionStatus!=='Connected'){
                const animFactor = 1 - Math.min(Math.abs(icon.animLoadingIndex - barID), 1)
                return Qt.rgba(c.r, c.g, c.b, animFactor)
            } else {
                return network.signalStrength > barID ? c : "transparent"
            }
        }
        border.color: icon.color
        border.width: 1
    }

    RowLayout {
        anchors.fill: parent
        visible: network.connectionStatus !== "Disconnected"
        spacing: icon.width / (3*5)

        Bar {barID: 1}
        Bar {barID: 2}
        Bar {barID: 3}
        Bar {barID: 4}

    }

    Rectangle {
        id: disconnectIcon
        visible: network.connectionStatus === "Disconnected"
        opacity: 0

        SequentialAnimation on opacity{
            running: true
            id: iconAnimation
            loops: Animation.Infinite
            PropertyAnimation{to: 1; duration: 750; easing.type: Easing.OutQuad}
            PropertyAnimation{to: 0.1; duration: 750; easing.type: Easing.InQuad}
        }

        anchors.centerIn: parent
        height: parent.height
        width: height
        radius: width/4
        color: "transparent"

        border.color: icon.color
        border.width: 1

        Image {
            id: iconSource
            source: "assets/disconnect.svg"
            anchors.centerIn: parent
            width: parent.width * 0.8
            height: parent.height * 0.8
            visible: false
        }

        MultiEffect {
            anchors.fill: iconSource
            visible: true

            source: iconSource
            
            colorizationColor: icon.color
            colorization: 1.0
        }
    }
}
