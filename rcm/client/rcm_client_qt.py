#!/usr/bin/env python3
#
# Copyright (c) 2014-2019 CINECA.
#
# This file is part of RCM (Remote Connection Manager) 
# (see http://www.hpc.cineca.it/software/rcm).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

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
from client.miscellaneous.config_parser import parser
from client.utils.rcm_enum import Mode
from client.miscellaneous.logger import configure_logger


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
