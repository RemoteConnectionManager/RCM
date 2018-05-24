# std lib
import os
from configparser import RawConfigParser

# local includes

config_file_name = os.path.join(os.path.expanduser('~'), '.rcm', 'rcm.cfg')
parser = RawConfigParser()

# parse config file to load the most recent sessions
if os.path.exists(config_file_name):
    try:
        with open(config_file_name, 'r') as config_file:
            parser.read_file(config_file, source=config_file_name)
    except Exception:
        print("Failed to load the config file")
else:
    print("Failed to load the config file: file does not exist")