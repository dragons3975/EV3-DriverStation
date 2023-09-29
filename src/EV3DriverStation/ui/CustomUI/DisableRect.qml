import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.12

Item {
    id: root
    anchors.fill: parent
    property string text: ""

    z: 1000

    Rectangle {
        anchors.fill: parent
        color: Material.background
        opacity: 0.8
    }

    Label {
        anchors.fill: parent
        text: root.text
        font.pixelSize: 25
        font.bold: true
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        color: Material.foreground
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        onClicked: {}
    }
}