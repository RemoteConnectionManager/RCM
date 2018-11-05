import os
from  baseconfig import baseconfig
from  logger_server import logger


class versionconfig(baseconfig):
    def __init__(self): 
        logger.debug("version config init")
        baseconfig.__init__(self)
        self.filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'versionRCM.cfg')
        self.parse()
    
    def get_checksum(self, buildPlatformString=''):
        logger.debug("get_checksum")
        checksum = self.confdict.get(('checksum', buildPlatformString), '')
        downloadurl = self.confdict.get(('url', buildPlatformString), '')
        return(checksum, downloadurl)
