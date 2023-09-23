import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts
import QtQuick.Controls.Material 2.15

Rectangle {
    width: 180
    height: 300

    color: Material.backgroundColor

    component PanelButton: Button {
        id: panelButton
        property string panel: ""

        property bool selected: app.panel === panel
        
        text: panel
        height: 40
        Layout.fillWidth: true
        Layout.minimumHeight: height
        Layout.maximumHeight: height

        padding: 0
        bottomInset: 0
        topInset: 0

        Material.background: selected ? Material.primaryColor : Material.frameColor
        Material.elevation: selected ? 5 : -5
        Material.roundedScale: Material.NotRounded

        font.bold: selected

        onClicked: app.panel = panel
    }

    ColumnLayout {
        id: column
        anchors.fill: parent
        spacing: 5

        PanelButton {
            panel: 'Robot'
            text: qsTr("Robot Status")
        }

        Item {
            // spacer item
            Layout.fillWidth: true
            Layout.fillHeight: true
        }

        PanelButton {
            panel: 'Controllers'
            text: qsTr("Controllers")
        }
        PanelButton {
            panel: 'Network'
            text: qsTr("Network")
        }

        Item {
            // spacer item
            Layout.fillWidth: true
            height: 10
        }

        Button {
            id: quitButton
            text: qsTr("Quit")
            Layout.fillWidth: true
            Layout.minimumHeight: 20
            Material.roundedScale: Material.SmallScale

            Material.background: Material.Red
            onClicked: Qt.quit()
        }
    }
}
