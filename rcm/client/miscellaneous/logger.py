# std lib
import sys
import logging
import logging.handlers
import json

# pyqt5
from PyQt5.QtCore import pyqtSignal, QObject

# local import
from client.utils.rcm_enum import Mode

rootLogger = logging.getLogger()
rootLogger.setLevel(logging.INFO)
consoleHandler = logging.StreamHandler()
rootLogger.addHandler(consoleHandler)

logger = logging.getLogger("RCM.gui")
logic_logger = logging.getLogger('RCM.client')
ssh_logger = logging.getLogger('paramiko')


class QLabelLoggerHandler(logging.Handler):
    """
    We redirect the log info messages to the log label of the main window
    """

    def __init__(self, label):
        super().__init__()

        self.setFormatter(logging.Formatter('%(message)s'))
        self.widget = label
        self.lock = False

    def emit(self, record):
        if record.levelno == logging.INFO:
            msg = self.format(record)
            self.widget.setText(msg)

    def write(self, m):
        pass


class LoggerSignals(QObject):
    """
    Defines the signals available for thread-safe logging
    Read here https://stackoverflow.com/questions/2104779/qobject-qplaintextedit-multithreading-issues
    """

    log_message = pyqtSignal(str)


class QTextEditLoggerHandler(logging.Handler):
    """
    We redirect the log info messages to the log text edit of the main window
    """

    def __init__(self):
        """
        Initialize the handler.
        """
        super().__init__()

        self.setFormatter(logging.Formatter('%(asctime)-15s - %(levelname)s - %(message)s'))
        self.logger_signals = LoggerSignals()
        self.html_msg = ""

    def emit(self, record):
        """
        Emit a html message into the text edit widget using signal/slot
        """
        if sys.platform == 'win32':
            font_size = 8
        else:
            font_size = 10

        try:
            msg = self.format(record)

            if record.levelno == logging.ERROR or record.levelno == logging.CRITICAL:
                self.html_msg = "<span style=\" font-size:%spt; font-weight:600; color:#ff0000;\" >" % str(font_size)
            elif record.levelno == logging.WARNING:
                self.html_msg = "<span style=\" font-size:%spt; font-weight:600; color:#ff9900;\" >" % str(font_size)
            elif record.levelno == logging.INFO:
                self.html_msg = "<span style=\" font-size:%spt; font-weight:600; color:#000000;\" >" % str(font_size)
            else:
                self.html_msg = "<span style=\" font-size:%spt; font-weight:400; color:#000000;\" >" % str(font_size - 1)
            self.html_msg += str(msg)
            self.html_msg += "</span>"

            self.logger_signals.log_message.emit(self.html_msg)
        except Exception:
            self.handleError(record)

    def write(self, m):
        pass


def configure_logger(mode=Mode.GUI, debug=False):
    if mode is Mode.GUI:
        if debug:
            logger.setLevel(logging.DEBUG)
            logic_logger.setLevel(logging.DEBUG)
            ssh_logger.setLevel(logging.INFO)

            text_log_handler.setFormatter(
                logging.Formatter('%(asctime)s [%(levelname)s:%(name)s] ' +
                                  '[%(threadName)-12.12s] [%(filename)s:' +
                                  '%(funcName)s:%(lineno)d]-->%(message)s')
            )
        else:
            logger.setLevel(logging.INFO)
            logic_logger.setLevel(logging.INFO)
            ssh_logger.setLevel(logging.WARNING)
            text_log_handler.setFormatter(logging.Formatter('%(asctime)-15s - %(levelname)s - %(message)s'))
    else:
        logger.setLevel(logging.ERROR)
        logic_logger.setLevel(logging.ERROR)
        ssh_logger.setLevel(logging.ERROR)


text_log_handler = QTextEditLoggerHandler()
