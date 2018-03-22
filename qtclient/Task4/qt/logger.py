import logging

logger = logging.getLogger("RCM")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

fh = logging.FileHandler("Debug.log")
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

logger.addHandler(fh)

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