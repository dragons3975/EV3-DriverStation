from src.EV3DriverStation.app import GuiApp
import signal


def launch():
    signal.signal(signal.SIGINT, signal.SIG_DFL)    # Allow Ctrl-C to close the program
    GuiApp().exec()


if __name__ == '__main__':
    launch()
