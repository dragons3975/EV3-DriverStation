import QtQuick 2.15
import QtQuick.Layouts 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Effects

Control {
    id: icon

    width: 40
    height: 30

    readonly property color activeColor: Material.color(Material.LightBlue, Material.Shade100)
    readonly property color passiveColor: Material.foreground
    readonly property color disabledColor: Material.color(Material.Grey, Material.Shade600)

    readonly property color controller1Color: {
        if (controllers.pilot1ControllerId<0) return disabledColor
        else if (controllers.isPilot1ControllerActive) return activeColor
        else return passiveColor 
    }
    readonly property color controller2Color: {
        if (controllers.pilot2ControllerId<0) return disabledColor
        else if (controllers.isPilot2ControllerActive) return activeColor
        else return passiveColor 
    }

    component IconSource: Image {
        source: "assets/controllerStatus.svg"
        anchors.fill: parent
        visible: false
        mipmap: true
        antialiasing: true
    }
    component IconComponent: MultiEffect { 
        property color color: Material.foreground
        anchors.fill: source
        colorization: 1.0
        colorizationColor: color
        visible: true
    } 


    IconComponent {
        source: key1
        visible: controllers.pilot1ControllerId==0
        color: controller1Color
    }
    IconComponent{
        source: key2
        visible: controllers.pilot2ControllerId==0
        color: controller2Color
    }
    IconComponent{
        source: con1
        visible: controllers.pilot1ControllerId!=0
        color: controller1Color
    }
    IconComponent{
        source: con2
        visible: controllers.pilot2ControllerId!=0
        color: controller2Color
    }
    IconComponent{
        source: slash
    }


    IconSource{
        id: key1
        source: "assets/controllerStatus-key1.svg"
    }
    IconSource{
        id: key2
        source: "assets/controllerStatus-key2.svg"
    }
    IconSource{
        id: con1
        source: "assets/controllerStatus-con1.svg"
    }
    IconSource{
        id: con2
        source: "assets/controllerStatus-con2.svg"
    }
    IconSource{
        id: slash
        source: "assets/controllerStatus-slash.svg"
    }
}
