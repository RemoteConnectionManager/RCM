# std lib
import logging
import json

# pyqt5
from PyQt5.QtGui import QTextCursor

# local import
from rcm_client.log.config_parser import parser

logger = logging.getLogger("RCM")

try:
    debug = json.loads(parser.get('Settings', 'debug_log_level'))
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
except Exception:
    logger.setLevel(logging.DEBUG)


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


class QTextEditLoggerHandler(logging.Handler):
    """
    We redirect the log info messages to the log text edit of the main window
    """

    def __init__(self, text_edit):
        super().__init__()

        self.setFormatter(logging.Formatter('%(asctime)-15s - %(levelname)s - %(message)s'))
        self.widget = text_edit
        self.lock = False

    def emit(self, record):
        msg = self.format(record)

        if record.levelno == logging.ERROR or record.levelno == logging.CRITICAL:
            html_msg = "<span style=\" font-size:10pt; font-weight:600; color:#ff0000;\" >"
        elif record.levelno == logging.WARNING:
            html_msg = "<span style=\" font-size:10pt; font-weight:600; color:#ff9900;\" >"
        else:
            html_msg = "<span style=\" font-size:10pt; font-weight:600; color:#000000;\" >"
        html_msg += msg
        html_msg += "</span>"

        self.widget.moveCursor(QTextCursor.EndOfLine)
        self.widget.appendHtml(html_msg)

    def write(self, m):
        pass
