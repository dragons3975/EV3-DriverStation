import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.12

Item {
    id: root

    property alias name: keyLabel.text
    property string value: ""
    property alias alignValue: valueLabel.horizontalAlignment
    property string prefix: ""
    property string suffix: ""
    property bool isNA: false
    property bool editable: false
    property bool hovered: mouseArea.containsMouse

    property color color: Material.foreground
    property color disabledColor: Material.color(Material.Grey, Material.Shade500)

    signal clicked

    width: parent.width
    height: 20

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
        id: keyLabel
        anchors.left: parent.left
        anchors.right: parent.horizontalCenter
        anchors.leftMargin: 10
        anchors.rightMargin: 10
        anchors.verticalCenter: parent.verticalCenter

        font.pixelSize: parent.height * .65
        horizontalAlignment: Text.AlignLeft
        verticalAlignment: Text.AlignVCenter

        color: isNA ? root.disabledColor : Material.foreground
    }

    Label {
        id: valueLabel
        anchors.left: parent.horizontalCenter
        anchors.right: parent.right
        anchors.leftMargin: 10
        anchors.rightMargin: 10
        anchors.verticalCenter: parent.verticalCenter

        font.pixelSize: parent.height * .65
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter

        color: isNA ? root.disabledColor : root.color

        text: {
            if (root.isNA) return qsTr("N/A")
            else return prefix + "<b>" + value + "</b>" + suffix
        }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent

        onClicked: {
            root.clicked()
        }
        hoverEnabled: true
    }

}