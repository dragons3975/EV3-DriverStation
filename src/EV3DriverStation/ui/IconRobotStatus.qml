import QtQuick 2.15
import QtQuick.Layouts 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Effects

Control {
    id: icon

    width: 40
    height: 30

    component IconSource: Image {
        anchors.centerIn: parent
        visible: false
        mipmap: true
        antialiasing: true
        fillMode: Image.PreserveAspectFit
    }
    component HeartBeatIcon: MultiEffect { 
        id: heartBeatIcon
        property color color: Material.foreground
        property color lowHeartBeatColor: Material.accentColor
        property color highHeartBeatColor: Material.accentColor
        property alias heartBeat: heartBeatAnimation.running

        anchors.fill: source
        colorization: 1.0
        property color heartBeatColor: lowHeartBeatColor
        colorizationColor: heartBeat ? heartBeatColor : color
        visible: true

        SequentialAnimation on heartBeatColor {
            id: heartBeatAnimation
            loops: Animation.Infinite
            ColorAnimation {to: highHeartBeatColor; duration: 250; easing.type: Easing.InQuad}
            ColorAnimation {to: lowHeartBeatColor; duration: 250; easing.type: Easing.InQuad}
            ColorAnimation {to: highHeartBeatColor; duration: 250; easing.type: Easing.OutQuad}
            ColorAnimation {to: lowHeartBeatColor; duration: 750; easing.type: Easing.OutQuad}
        }
    } 

    HeartBeatIcon {
        source: modeAuto
        visible: robot.mode=='Autonomous'

        lowHeartBeatColor: Material.foreground
        highHeartBeatColor: Material.color( Material.Orange, Material.Shade200)
        heartBeat: robot.enabled
    }

    HeartBeatIcon {
        source: modeTele
        visible: robot.mode=='Teleoperated'
        
        lowHeartBeatColor: Material.foreground
        highHeartBeatColor: Material.color( Material.LightGreen, Material.Shade200)
        heartBeat: robot.enabled
    }


    IconSource{
        id: modeAuto
        height: 23
        anchors.verticalCenterOffset: -2
        source: "assets/modeAuto.svg"
    }
    IconSource{
        id: modeTele
        height: 27
        source: "assets/modeTele.svg"
    }
}
