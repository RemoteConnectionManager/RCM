# std lib
import logging

# pyqt5
from PyQt5.QtGui import QTextCursor

logger = logging.getLogger("RCM")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

fh = logging.FileHandler("Debug.log")
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

logger.addHandler(fh)


class QLabelLoggerHandler(logging.Handler):
    """
    We redirect the log info messages to the log label of the main window
    """

    def __init__(self, label):
        super(logging.Handler, self).__init__()

        self.setFormatter(logging.Formatter('%(message)s'))
        self.setLevel(logging.DEBUG)
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

        def __init__(self, label):
            super(logging.Handler, self).__init__()

            self.setFormatter(logging.Formatter('%(asctime)-15s - %(levelname)s - %(message)s'))
            self.setLevel(logging.DEBUG)
            self.widget = label
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
