# std lib
import unittest
import sys
import os
import json
from collections import OrderedDict

# pyqt5
from PyQt5.QtWidgets import QApplication
# from PyQt5.QtCore import Qt
# from PyQt5.QtTest import QTest

# add python path
rcm_root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(rcm_root_path)

# local import
from client.gui.dynamic_display_dialog import QDynamicDisplayDialog
from client.utils.rcm_enum import Mode
from client.miscellaneous.logger import configure_logger


class TestQDisaplyDialog(unittest.TestCase):

    def test_qdisplay_dialog(self):
        app = QApplication(sys.argv)
        display_dialog_ui = json.load(open("scheduler.json"), object_pairs_hook=OrderedDict)
        display_dialog = QDynamicDisplayDialog(display_dialog_ui)
        display_dialog.show()
        self.assertEqual(app.exec_(), 0)


if __name__ == '__main__':
    configure_logger(mode=Mode.TEST, debug=False)
    unittest.main(verbosity=2)
