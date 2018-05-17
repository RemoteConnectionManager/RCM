# std lib
import unittest
import sys
import os

# pyqt5
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest

# add python paths
source_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(source_root)
sys.path.append(os.path.join(source_root, 'rcm'))

# local includes
from rcm.client.gui.ssh_session_widget import QSSHSessionWidget
from client.utils.rcm_enum import Mode
from client.log.logger import configure_logger

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
        from rcm.client.logic.aes_cipher import AESCipher

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


if __name__ == '__main__':
    configure_logger(mode=Mode.TEST, debug=False)
    unittest.main(verbosity=2)
