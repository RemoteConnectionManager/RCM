# std lib
import logging
import logging.handlers
import json

# pyqt5
from PyQt5.QtCore import pyqtSignal, QObject

# local import
from client.log.config_parser import parser

rootLogger = logging.getLogger()
rootLogger.setLevel(logging.INFO)
consoleHandler = logging.StreamHandler()
rootLogger.addHandler(consoleHandler)

logger = logging.getLogger("RCM.gui")
logic_logger = logging.getLogger('RCM.client')
ssh_logger = logging.getLogger('paramiko')


try:
    debug = json.loads(parser.get('Settings', 'debug_log_level'))
    if debug:
        logger.setLevel(logging.DEBUG)
        logic_logger.setLevel(logging.DEBUG)
        ssh_logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.INFO)
        logic_logger.setLevel(logging.INFO)
        ssh_logger.setLevel(logging.WARNING)
except Exception:
    logger.setLevel(logging.INFO)
    logic_logger.setLevel(logging.INFO)
    ssh_logger.setLevel(logging.WARNING)


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

    def __init__(self, text_edit):
        """
        Initialize the handler.
        """
        super().__init__()

        self.setFormatter(logging.Formatter('%(asctime)-15s - %(levelname)s - %(message)s'))
        self.widget = text_edit
        self.logger_signals = LoggerSignals()
        self.html_msg = ""

    def flush(self):
        """
        Flushes the html message into the text edit widget using signal/slot
        """
        self.logger_signals.log_message.emit(self.html_msg)

    def emit(self, record):
        """
        Emit a record.
        """
        try:
            msg = self.format(record)

            if record.levelno == logging.ERROR or record.levelno == logging.CRITICAL:
                self.html_msg = "<span style=\" font-size:10pt; font-weight:600; color:#ff0000;\" >"
            elif record.levelno == logging.WARNING:
                self.html_msg = "<span style=\" font-size:10pt; font-weight:600; color:#ff9900;\" >"
            else:
                self.html_msg = "<span style=\" font-size:10pt; font-weight:600; color:#000000;\" >"
            self.html_msg += str(msg)
            self.html_msg += "</span>"

            self.flush()
        except Exception:
            self.handleError(record)

    def write(self, m):
        pass
