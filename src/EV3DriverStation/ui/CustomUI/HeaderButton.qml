import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.12

Item {
    property string source: ""
    property string tooltip: ""

    signal clicked

    height: 25
    width: 40

    ToolButton {
        anchors.left: parent.left
        anchors.horizontalCenter: parent.horizontalCenter

        flat: true
        icon.source: "../"+source
        icon.color: Material.foreground

        ToolTip.visible: tooltip!="" ? hovered : false
        ToolTip.text: tooltip

        onClicked: parent.clicked()

        height: 25
        width: 25
        icon.width: 15
        icon.height: 15
    }
}