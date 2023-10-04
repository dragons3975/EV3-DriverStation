import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.12

Item {
    property alias text : button.text
    property string source: ""
    property string tooltip: ""

    signal clicked

    height: 25
    width: 40

    ToolButton {
        id: button
        anchors.left: parent.left
        anchors.horizontalCenter: parent.horizontalCenter

        flat: true
        icon.source: source.length>0 ? "../"+source : ""
        icon.color: Material.foreground

        font.bold: true
        font.pixelSize: 20

        ToolTip.visible: tooltip!="" ? hovered : false
        ToolTip.text: tooltip

        onClicked: parent.clicked()

        height: 25
        width: 25
        icon.width: 15
        icon.height: 15
    }
}