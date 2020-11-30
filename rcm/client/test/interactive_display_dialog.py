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

import sys
# pyqt5
from PyQt5.QtWidgets import QApplication

app = QApplication(sys.argv)

import os
import sys

root_rcm_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_rcm_path)
sys.path.append(os.path.join(root_rcm_path, 'utils'))
sys.path.append(os.path.join(root_rcm_path, 'server', 'lib'))
sys.path.append(os.path.join(root_rcm_path, 'client'))


from server.lib.jobscript_builder import *
from server.lib.scheduler import *
from server.lib.manager import *
import config

from gui.dynamic_display_dialog import *

# This is needed, otherwise no default logging happen
logging.debug("Start test app")
logger = logging.getLogger('RCM.test_gui')
logger.setLevel(logging.INFO)

print("sys.argv", sys.argv[1:])

config.getConfig()
manager = ServerManager()
manager.init({'client_info': {"screen_height": 1080, "screen_width": 1920}})

display_dialog_ui = manager.root_node.get_gui_options()
logger.debug("-----------------------------------")
logger.debug(json.dumps(display_dialog_ui, indent=4))
with open(os.path.join(os.environ['HOME'], '.rcm', 'display_dialog.json'), 'w') as f:
    f.write(json.dumps(display_dialog_ui, indent=4))

logger.debug("-----------------------------------")


def print_result(choices):
    choices_string = json.dumps(choices, indent=4)
    logger.debug(choices_string)
    manager.handle_choices(choices_string)
    manager.create_session()

    for k, v in manager.top_templates.items():
        logger.debug(k + " :::>\n" + str(v) + "\n<")

    for sched in manager.schedulers:
        for templ in manager.schedulers[sched].templates:
            logger.debug("@@@@scheduler " + str(sched) + str(templ) + ":::>\n" +
                         str(manager.schedulers[sched].templates[templ]) +
                         "\n<")


display_dialog = QDynamicDisplayDialog(display_dialog_ui, callback=print_result)
display_dialog.show()
sys.exit(app.exec_())
