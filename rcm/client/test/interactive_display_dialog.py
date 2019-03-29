
# stdlib
import json
import sys
import re

# pyqt5
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QLabel, QLineEdit, QDialog, QComboBox, \
    QHBoxLayout, QVBoxLayout, QPushButton, \
    QApplication, QTabWidget, QWidget, QSlider, QSizePolicy, QFrame


app = QApplication(sys.argv)

import os
import sys
root_rcm_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_rcm_path)
sys.path.append(os.path.join(root_rcm_path, 'utils'))
sys.path.append(os.path.join(root_rcm_path, 'server', 'lib'))
sys.path.append(os.path.join(root_rcm_path, 'client'))

import logging
import os


#from server.lib.config import *
from server.lib.jobscript_builder import *
from server.lib.scheduler import *
from server.lib.manager import *
import config

from gui.new_display_dialog import *

#This is needed, otherwise no default logging happen
logging.debug("Start test app")
logger = logging.getLogger('RCM.test_gui')
logger.setLevel(logging.INFO)

print("sys.argv",sys.argv[1:])


# test_base_path = os.path.join(root_rcm_path, 'server', 'test', 'etc')
# list_paths=[]
# for path in sys.argv[1:]:
#     path = os.path.join(test_base_path, path)
#     if os.path.exists(path):
#         list_paths.append(path)
#     else:
#         print("WARNING path ", path, "not found")
# #list_paths.append(os.path.join(os.environ.get('HOME',''), '.rcm', 'config', 'config.yaml'))                                CascadeYamlConfig.get()

# set up default test environment if not used

config.getConfig( )
manager = ServerManager()
manager.init()

display_dialog_ui = manager.root_node.get_gui_options()
logger.debug("-----------------------------------")
logger.debug(json.dumps(display_dialog_ui, indent=4))
with open(os.path.join(os.environ['HOME'],'.rcm','display_dialog.json'), 'w') as f:
    f.write(json.dumps(display_dialog_ui, indent=4))

logger.debug("-----------------------------------")

def print_result(choices):
    choices_string = json.dumps(choices, indent=4)
    logger.debug(choices_string)
    manager.handle_choices(choices_string)
    manager.new_session()
    # SchedulerManager._allInstances[0].active_scheduler()
    for k, v in manager.top_templates.items():
        logger.debug(k + " :::>\n" + str(v) +"\n<:::::::::::::::::::::")

    for sched in manager.schedulers:
        for templ in manager.schedulers[sched].templates:
            logger.debug("@@@@scheduler " + str(sched) + str(templ) + ":::>\n" +
                         str(manager.schedulers[sched].templates[templ]) +
                         "\n<:::::::::::::::::::::")

display_dialog = QDisplayDialog(display_dialog_ui, callback=print_result)
display_dialog.show()
sys.exit(app.exec_())