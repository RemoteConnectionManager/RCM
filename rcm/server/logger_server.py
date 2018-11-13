import os
import sys
import logging.handlers

# Remove oll handlers

for h in logging.root.handlers:
    # print("REMOVING-->"+str(h))
    logging.root.removeHandler(h)

LONG_FORMAT='[%(levelname)s:::%(name)s %(asctime)s (%(module)s:%(lineno)d %(funcName)s) : %(message)s'
SHORT_FORMAT='[%(levelname)s:::%(name)s (%(module)s:%(lineno)d : %(message)s'

ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(logging.Formatter(SHORT_FORMAT))
logging.root.addHandler(ch)

for l in ['basic', 'RCM.composer']:
    logging.getLogger(l).setLevel( os.environ.get("RCM_DEBUG_LEVEL", "warning").upper())

logger=logging.getLogger('basic')

ch = logging.StreamHandler(sys.stdout)
rcmdir = os.path.join(os.path.expanduser('~'), '.rcm')
if ( not os.path.isdir(rcmdir) ):
    os.mkdir(rcmdir)
    os.chmod(rcmdir,755)
rcmlog=os.path.join(rcmdir,'logfile')
fh = logging.handlers.RotatingFileHandler(rcmlog, mode='a', maxBytes=50000,
                             backupCount=2, encoding=None, delay=0)
formatter = logging.Formatter(LONG_FORMAT)
fh.setFormatter(formatter)

# logger.propagate=False
logger.addHandler(fh)



def logger_setup(level=1):
    if level <= 0:
        logging.getLogger('RCM.composer').setLevel(logging.WARNING)
        logging.getLogger('basic').setLevel(logging.INFO)
        fh.setLevel(logging.INFO)
        ch.setLevel(logging.ERROR)
    else:
        if level == 1:
            logging.getLogger('RCM.composer').setLevel(logging.INFO)
            logging.getLogger('basic').setLevel(logging.INFO)
            fh.setLevel(logging.INFO)
            ch.setLevel(logging.WARNING)
        else:
            logging.getLogger('RCM.composer').setLevel(logging.DEBUG)
            logging.getLogger('basic').setLevel(logging.DEBUG)
            fh.setLevel(logging.DEBUG)
            ch.setLevel(logging.INFO)


