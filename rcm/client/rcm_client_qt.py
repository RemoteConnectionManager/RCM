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
import pathlib
import json

# pyqt5
from PyQt5.QtWidgets import QApplication

# # add python path
# source_root = pathlib.Path(__file__).absolute().parents[1]
# sys.path.append(source_root)

# local includes
from rcm.client.gui.rcm_main_window import RCMMainWindow
from rcm.client.miscellaneous.config_parser import parser
from rcm.client.utils.rcm_enum import Mode
from rcm.client.miscellaneous.logger import configure_logger

def main():
    try:
        debug_log_level = json.loads(parser.get('Settings', 'debug_log_level'))
        configure_logger(Mode.GUI, debug_log_level)
    except Exception:
        configure_logger(Mode.GUI, False)

    app = QApplication(sys.argv)
    rcm_win = RCMMainWindow()
    rcm_win.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()