#!/usr/bin/env python3

# std lib
import sys
import os

# pyqt5
from PyQt5.QtWidgets import QApplication

# add python path
source_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(source_root)

# local includes
from rcm.client.gui.rcm_main_window import RCMMainWindow


if __name__ == '__main__':
    app = QApplication(sys.argv)
    rcm_win = RCMMainWindow()
    rcm_win.show()
    sys.exit(app.exec_())
