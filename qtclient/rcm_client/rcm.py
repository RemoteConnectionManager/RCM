# std lib
import sys

# pyqt5
from PyQt5.QtWidgets import QApplication

# local includes
from rcm_client.gui.rcm_main_window import RCMMainWindow


if __name__ == '__main__':
    app = QApplication(sys.argv)
    rcm_win = RCMMainWindow()
    rcm_win.show()
    sys.exit(app.exec_())
