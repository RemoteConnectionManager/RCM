
exec("import dummy_rcm_scheduler as rcm_scheduler")

testJobScriptDict = {}
from  logger_server import logger

def get_checksum(build_platform):
    logger.debug("get_checksum")
    import ConfigParser
    config = ConfigParser.RawConfigParser()
    myPath =  os.path.dirname(os.path.abspath(__file__))
    config.read(os.path.join(myPath, 'versionRCM.cfg'))

    checksum = config.get('checksum', build_platform)
    downloadurl = config.get('url', build_platform)
    return ((checksum,downloadurl))

def get_checksum(build_platform):
    logger.debug("get_checksum")
    return (('dummy','dummy'))
