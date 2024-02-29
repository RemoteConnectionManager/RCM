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

import unittest
import sys
import os
import uuid
import re
import getpass
from datetime import datetime, timedelta

# pyqt
try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    from PyQt6.QtTest import QTest
    PyQt = 6
except ImportError:
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt
    from PyQt5.QtTest import QTest
    PyQt = 5

# add python path
rcm_root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(rcm_root_path)

# local import
from client.gui.ssh_session_widget import QSSHSessionWidget
from client.logic.manager import RemoteConnectionManager
from client.miscellaneous.logger import configure_logger
from client.utils.rcm_enum import Mode

app = QApplication(sys.argv)


class TestSSHSessionWidget(unittest.TestCase):

    class QSSHSessionTestWidget(QSSHSessionWidget):

        def __init__(self, parent):
            super().__init__(parent)
            self.login_success = True

        def login(self):
            # Show the waiting widget
            self.containerLoginWidget.hide()
            self.containerSessionWidget.hide()
            self.containerWaitingWidget.show()

            # fake login logic
            self.is_logged = self.login_success
            self.on_logged()

        def reload(self):
            # Show the reload widget
            self.containerLoginWidget.hide()
            self.containerSessionWidget.hide()
            self.containerWaitingWidget.hide()
            self.containerReloadWidget.show()

            # fake logic
            self.on_reloaded()

    def test_login_successful(self):
        ssh_session_widget = self.QSSHSessionTestWidget(None)

        self.assertEqual(ssh_session_widget.containerLoginWidget.isHidden(), False)
        self.assertEqual(ssh_session_widget.containerSessionWidget.isHidden(), True)
        self.assertEqual(ssh_session_widget.containerWaitingWidget.isHidden(), True)

        QTest.mouseClick(ssh_session_widget.login_button, Qt.LeftButton)

        self.assertEqual(ssh_session_widget.is_logged, True)
        self.assertEqual(ssh_session_widget.containerLoginWidget.isHidden(), True)
        self.assertEqual(ssh_session_widget.containerSessionWidget.isHidden(), False)
        self.assertEqual(ssh_session_widget.containerWaitingWidget.isHidden(), True)

    def test_login_fail(self):
        ssh_session_widget = self.QSSHSessionTestWidget(None)
        ssh_session_widget.login_success = False

        self.assertEqual(ssh_session_widget.containerLoginWidget.isHidden(), False)
        self.assertEqual(ssh_session_widget.containerSessionWidget.isHidden(), True)
        self.assertEqual(ssh_session_widget.containerWaitingWidget.isHidden(), True)

        QTest.mouseClick(ssh_session_widget.login_button, Qt.LeftButton)

        self.assertEqual(ssh_session_widget.is_logged, False)
        self.assertEqual(ssh_session_widget.containerLoginWidget.isHidden(), False)
        self.assertEqual(ssh_session_widget.containerSessionWidget.isHidden(), True)
        self.assertEqual(ssh_session_widget.containerWaitingWidget.isHidden(), True)


class TestAESCipher(unittest.TestCase):
    def test_encryption(self):
        from client.logic.aes_cipher import AESCipher

        rcm_cipher = AESCipher(key='hyTedDfs')
        message = "lorem_ipsum"
        encrypted_messaged = rcm_cipher.encrypt(message).decode('utf-8')
        decrypted_messge = rcm_cipher.decrypt(encrypted_messaged).decode('utf-8')
        self.assertEqual(message, decrypted_messge)


class TestD3DESCipher(unittest.TestCase):
    def test_encryption(self):
        import client.logic.d3des as d3des
        if sys.version_info >= (3, 0):
            import binascii
            key = binascii.unhexlify(b'0123456789abcdef')
            plain = binascii.unhexlify(b'0123456789abcdef')
            cipher = binascii.unhexlify(b'6e09a37726dd560c')
            ek = d3des.deskey(key, False)
            dk = d3des.deskey(key, True)
            self.assertEqual(d3des.desfunc(plain, ek), cipher)
            self.assertEqual(d3des.desfunc(d3des.desfunc(plain, ek), dk), plain)
            self.assertEqual(d3des.desfunc(d3des.desfunc(plain, dk), ek), plain)
        else:
            key = '0123456789abcdef'.decode('hex')
            plain = '0123456789abcdef'.decode('hex')
            cipher = '6e09a37726dd560c'.decode('hex')
            ek = d3des.deskey(key, False)
            dk = d3des.deskey(key, True)
            self.assertEqual(d3des.desfunc(plain, ek), cipher)
            self.assertEqual(d3des.desfunc(d3des.desfunc(plain, ek), dk), plain)
            self.assertEqual(d3des.desfunc(d3des.desfunc(plain, dk), ek), plain)


class TestRCMCipher(unittest.TestCase):
    def test_encryption(self):
        import client.logic.cipher as cipher
        rcm_cipher = cipher.RCMCipher()
        self.assertEqual(rcm_cipher.decrypt(rcm_cipher.encrypt()), rcm_cipher.vncpassword)
        rcm_cipher = cipher.RCMCipher("hyTedDfs")
        self.assertEqual(rcm_cipher.decrypt(rcm_cipher.encrypt()), rcm_cipher.vncpassword)


class TestManager(unittest.TestCase):

    def test_newcon_api(self):
        import client.logic.rcm_utils as rcm_utils

        exe = rcm_utils.which('vncviewer')

        if not exe:
            self.fail("vncviewer not found")
        print("vncviewer path: " + exe)

        remote_connection_manager = RemoteConnectionManager()
        host = 'login.galileo.cineca.it' # marconi o galileo
        user = input("User:")
        pswd = getpass.getpass('Password:')
        sessionname = str(uuid.uuid4())
        queues = ["light_2gb_1cor",
                  "medium_8gb_1core",
                  "med_16gb_2core",
                  "alarge_32gb_4core",
                  "xtralarge_64gb_8c",
                  "zfull_120gb_16c"]

        state = ["pending", "valid", "killing"]

        remote_connection_manager.login_setup(host=host, user=user, password=pswd)
        print("open sessions on " + host)
        out = remote_connection_manager.list()
        out.write(2)

        session = remote_connection_manager.new(queue='light_2gb_1cor',
                                                geometry='1024x968',
                                                sessionname=sessionname,
                                                vnc_id='fluxbox_turbovnc_vnc')

        remote_connection_manager.submit(session)
        out = remote_connection_manager.list()
        out.write(2)

        created = datetime.strptime(session.hash['created'],"%Y%m%d-%H:%M:%S")
        now = datetime.now()

        self.assertTrue(re.search("([0-9]{8}\-)(([0-9]{2}\:){2})([0-9]{2})", session.hash['created']))
        self.assertTrue(created - timedelta(minutes=2) < now or created + timedelta(minutes=2) > now)

        self.assertTrue(re.search("(node)([0-9]{1,3})", session.hash['node']))
        self.assertEqual(session.hash['nodelogin'],host)
        self.assertEqual(session.hash['session name'], sessionname)
        self.assertTrue(session.hash['sessionid'][:-1] == '{0}-{1}-'.format(user,session.hash['sessiontype'])
                        and
                        re.search(".*([1-9]|(10))$", session.hash['sessionid']))
        self.assertEqual(session.hash['sessiontype'], "pbs")
        self.assertTrue(session.hash['state'] in state)
        self.assertEqual(session.hash['tunnel'], "y")
        self.assertEqual(session.hash['username'], user)
        self.assertTrue(datetime.strptime(session.hash['timeleft'], "%H:%M:%S")
                        <= datetime.strptime(session.hash['walltime'], "%H:%M:%S"))

        print("created session:", session.hash['sessionid'],
              " display: ", session.hash['display'],
              " node:", session.hash['node'])

        remote_connection_manager.kill(session)
        out = remote_connection_manager.list()
        out.write(2)


if __name__ == '__main__':
    configure_logger(mode=Mode.TEST, debug=False)
    unittest.main(verbosity=2)
