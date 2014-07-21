exec("import dummy_rcm_scheduler as rcm_scheduler")

testJobScriptDict = {}

def get_checksum(build_platform):
    import ConfigParser
    config = ConfigParser.RawConfigParser()
    myPath =  os.path.dirname(os.path.abspath(__file__))
    config.read(os.path.join(myPath, 'versionRCM.cfg'))

    checksum = config.get('checksum', build_platform)
    downloadurl = config.get('url', build_platform)
    return ((checksum,downloadurl))

def get_checksum(build_platform):
    return (('dummy','dummy'))
