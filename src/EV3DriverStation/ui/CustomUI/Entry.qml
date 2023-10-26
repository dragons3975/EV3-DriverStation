import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.12

Item {
    id: root

    property alias name: keyLabel.text
    property string value: ""
    property string valueType: "string"
    property alias alignValue: valueLabel.horizontalAlignment
    property string prefix: ""
    property string suffix: ""
    property bool isNA: false
    property bool hovered: mouseArea.containsMouse
    property string tooltip: ""

    property bool editable: false
    signal valueEdited(value: string) 
    property bool valueSuccessfullyTransmitted: true
    property bool entryInitialized: false
    onValueChanged: {
        if (editable){
            if (valueType == "bool")
                valueSwitch.checked = value == "true"
            else
                valueTextField.text = value
        }
        if (entryInitialized){
            highlightBackground.color = Material.frameColor
            invalidValueAnimation.start()
        } else {
            entryInitialized = true
        }
    }
    function invalidValue(){
        if (editable){
            valueTextField.text = value
            valueSuccessfullyTransmitted = true
            highlightBackground.color = Material.color(Material.Red, Material.Shade500)
            invalidValueAnimation.start()
        }
    }
    function valueTransmitted(){
        valueSuccessfullyTransmitted = true
    }

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
        Behavior on opacity { PropertyAnimation { duration: 200 } }
    }

    Rectangle{
        id: highlightBackground
        anchors.fill: parent
        radius: height / 2

        color: Material.color(Material.Red, Material.Shade400)
        SequentialAnimation on opacity {
            id : invalidValueAnimation
            running: false
            PropertyAnimation {
                to: .2
                easing.type: Easing.InOutQuad
                duration: 200
            }
            PropertyAnimation {
                to: 0
                easing.type: Easing.InOutQuad
                duration: 200
            }
        }
        opacity: 0

    }



    Label {
        id: keyLabel
        anchors.left: parent.left
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
        visible: !editable

        anchors.left: parent.horizontalCenter
        anchors.right: parent.right
        anchors.leftMargin: 20
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

    TextField{
        id: valueTextField
        visible: editable && valueType != "bool"

        onFocusChanged: {
            if (focus)
                robot.lockKeyboard()
            else
                robot.releaseKeyboard()
        }

        anchors.left: parent.horizontalCenter
        anchors.right: parent.right
        anchors.leftMargin: 20
        anchors.rightMargin: 10
        anchors.verticalCenter: parent.verticalCenter
        height: parent.height

        font.pixelSize: parent.height * .6
        font.bold: valueSuccessfullyTransmitted
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter

        onEditingFinished: {
            valueSuccessfullyTransmitted = false
            focus = false
            entryInitialized = false
            root.valueEdited(text)
        }

        enabled: !isNA
    }

    CheckBox {
        id: valueSwitch
        visible: editable && valueType == "bool"

        anchors.left: parent.horizontalCenter
        anchors.right: parent.right
        anchors.leftMargin: 20
        anchors.rightMargin: 10
        anchors.verticalCenter: parent.verticalCenter
        height: parent.height
        topPadding: 0
        bottomPadding: 0

        onCheckedChanged: {
            root.valueEdited(checked)
        }
        enabled: !isNA
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent

        onClicked: {
            root.clicked()
            if (editable) {
                if (valueType == "bool")
                    valueSwitch.toggle()
                else
                    valueTextField.forceActiveFocus()
            }
        }
        hoverEnabled: true
        ToolTip.visible: tooltip ? hovered : false
        ToolTip.text: tooltip 
    }
}