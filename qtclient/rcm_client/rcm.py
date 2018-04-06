#!/usr/bin/env python3

# std lib
import sys
import os

# pyqt5
from PyQt5.QtWidgets import QApplication

# add python path
pypath,libpath = os.path.split(os.path.split(os.path.realpath(sys.argv[0]))[0])
sys.path.append(pypath)

# local includes
from rcm_client.gui.rcm_main_window import RCMMainWindow


if __name__ == '__main__':
    app = QApplication(sys.argv)
    rcm_win = RCMMainWindow()
    rcm_win.show()
    sys.exit(app.exec_())
