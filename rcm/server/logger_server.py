import os
import sys
import logging.handlers

logger=logging.getLogger('RCM')

class LoggerServer(object):

    def __init__(self):

        # print("######################## LoggerServer init ###########")
        # Remove all handlers
        for h in logging.root.handlers:
            # print("REMOVING-->"+str(h))
            logging.root.removeHandler(h)

        LONG_FORMAT='[%(levelname)s:::%(name)s %(asctime)s (%(module)s:%(lineno)d %(funcName)s) : %(message)s'
        SHORT_FORMAT='[%(levelname)s:::%(name)s (%(module)s:%(lineno)d : %(message)s'

        self.ch = logging.StreamHandler(sys.stdout)
        self.ch.setFormatter(logging.Formatter(SHORT_FORMAT))
        logging.root.addHandler(self.ch)

        rcmdir = os.path.join(os.path.expanduser('~'), '.rcm')
        if ( not os.path.isdir(rcmdir) ):
            os.mkdir(rcmdir)
            os.chmod(rcmdir,755)
        rcmlog=os.path.join(rcmdir,'logfile')
        self.fh = logging.handlers.RotatingFileHandler(rcmlog, mode='a', maxBytes=50000,
                                     backupCount=2, encoding=None, delay=0)
        self.fh.setFormatter(logging.Formatter(LONG_FORMAT))

        level = os.environ.get("RCM_DEBUG_LEVEL", "warning").upper()
        for l in ['RCM']:
            logging.getLogger(l).setLevel(level)
            logging.getLogger(l).addHandler(self.fh)


    def logger_setup(self,level=1):
        if level <= 0:
            logging.getLogger('RCM').setLevel(logging.WARNING)
            self.fh.setLevel(logging.INFO)
            self.ch.setLevel(logging.ERROR)
        else:
            if level == 1:
                logging.getLogger('RCM').setLevel(logging.INFO)
                self.fh.setLevel(logging.INFO)
                self.ch.setLevel(logging.WARNING)
            else:
                logging.getLogger('RCM').setLevel(logging.DEBUG)
                self.fh.setLevel(logging.DEBUG)
                self.ch.setLevel(logging.INFO)

    def config(self,configs=dict()):
        for log in configs:
            logging.getLogger(log).setLevel(configs[log].upper())


logger_server = LoggerServer()
