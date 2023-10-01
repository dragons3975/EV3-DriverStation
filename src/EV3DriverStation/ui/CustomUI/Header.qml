import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import QtQuick.Controls.Material 2.12

RowLayout {
    Layout.fillWidth: true
    height: 25
    Layout.minimumHeight: height
    Layout.maximumHeight: height
    property alias text: headerLabel.text

    Label {
        id: headerLabel
        Layout.fillWidth: true
        text: "Title"
        leftPadding: 30
        font.bold: true
        font.pixelSize: 17
    }
}