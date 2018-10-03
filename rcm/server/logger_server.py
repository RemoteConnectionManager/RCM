import os
import sys
import logging.handlers

logger = logging.getLogger('basic')
logger.setLevel( os.environ.get("RCM_DEBUG_LEVEL","debug").upper())
ch = logging.StreamHandler(sys.stdout)
rcmdir = os.path.join(os.path.expanduser('~'), '.rcm')
if ( not os.path.isdir(rcmdir) ):
    os.mkdir(rcmdir)
    os.chmod(rcmdir,755)
rcmlog=os.path.join(rcmdir,'logfile')
#fh = logging.FileHandler(rcmlog, mode='a')
fh = logging.handlers.RotatingFileHandler(rcmlog, mode='a', maxBytes=50000,
                             backupCount=2, encoding=None, delay=0)
formatter = logging.Formatter('[%(levelname)s] %(asctime)s (%(module)s:%(lineno)d %(funcName)s) : %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

#logger.addHandler(ch)
logger.addHandler(fh)