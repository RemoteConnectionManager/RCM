import os
import pwd
import re
#from __future__ import print_function

import rcm


import rcm_protocol_server
import rcm_protocol_parser

import platformconfig



if __name__ == '__main__':
    p=platformconfig.platformconfig()
    s=p.get_rcm_server()
    r=rcm_protocol_server.rcm_protocol(s)
    c=rcm_protocol_parser.CommandParser(r)
    c.handle()

