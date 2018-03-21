import logging

logger = logging.getLogger("RCM")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

ch = logging.StreamHandler()
ch.setLevel(logging.WARNING)
ch.setFormatter(formatter)

logger.addHandler(ch)

class QLabelLogger(logging.Handler):

    def __init__(self, label):
        super(logging.Handler,self).__init__()
        formatter = logging.Formatter('%(message)s')
        self.setFormatter(formatter)
        self.setLevel(logging.DEBUG)

        self.widget = label
        self.lock = False

    def emit(self, record):
        if record.levelno == logging.INFO:
            msg = self.format(record)
            self.widget.setText(msg)

    def write(self, m):
        pass