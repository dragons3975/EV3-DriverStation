import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.12


ApplicationWindow  {
    id: window
    visible: true
    width: 1200
    
    minimumHeight: 300    
    maximumHeight: minimumHeight

    title: "EV3 Driver Station"
    Component.onCompleted: robot.install_event_filter(window)
    

    Item {
        id: sidePanel

        PanelSelector {
            id: panelSelector;
            anchors.fill: parent;
        }

        anchors.left: parent.left;
        anchors.top: parent.top;
        anchors.bottom: parent.bottom;
        anchors.margins: 10;
        width: 170
    }


    Item {
        anchors.right: parent.right;
        anchors.top: parent.top;
        anchors.bottom: parent.bottom;
        anchors.left: sidePanel.right;
        anchors.margins: 10;

        RobotPanel {
            anchors.fill: parent;
            visible: app.panel==="Robot";
        }

        ControllersPanel {
            anchors.fill: parent;
            visible: app.panel==="Controllers";
        }

        NetworkPanel {
            anchors.fill: parent;
            visible: app.panel==="Network";
        }

    }
}
