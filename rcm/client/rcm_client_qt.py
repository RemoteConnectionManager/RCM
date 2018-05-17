#!/usr/bin/env python3

# std lib
import sys
import os
import json

# pyqt5
from PyQt5.QtWidgets import QApplication

# add python path
source_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(source_root)

# local includes
from client.gui.rcm_main_window import RCMMainWindow
from client.log.config_parser import parser
from client.utils.rcm_enum import Mode
from client.log.logger import configure_logger


if __name__ == '__main__':
    try:
        debug_log_level = json.loads(parser.get('Settings', 'debug_log_level'))
        configure_logger(Mode.GUI, debug_log_level)
    except Exception:
        configure_logger(Mode.GUI, False)

    app = QApplication(sys.argv)
    rcm_win = RCMMainWindow()
    rcm_win.show()
    sys.exit(app.exec_())
