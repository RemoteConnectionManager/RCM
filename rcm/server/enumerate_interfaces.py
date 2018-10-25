# Use those functions to enumerate all interfaces available on the system using Python.
# found on <http://code.activestate.com/recipes/439093/#c1>

import socket
import fcntl
import struct
import array
import re
from  logger_server import logger

def all_interfaces():
    logger.debug("all_interfaces")
    max_possible = 128  # arbitrary. raise if needed.
    bytes = max_possible * 32
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    names = array.array('B', '\0' * bytes)
    outbytes = struct.unpack('iL', fcntl.ioctl(
        s.fileno(),
        0x8912,  # SIOCGIFCONF
        struct.pack('iL', bytes, names.buffer_info()[0])
    ))[0]
    namestr = names.tostring()
    lst = []
    for i in range(0, outbytes, 40):
        name = namestr[i:i+16].split('\0', 1)[0]
        ip   = namestr[i+20:i+24]
        lst.append((name, ip))
    return lst

def format_ip(addr):
    logger.debug("format_ip")
    return str(ord(addr[0])) + '.' + \
           str(ord(addr[1])) + '.' + \
           str(ord(addr[2])) + '.' + \
           str(ord(addr[3]))

def external_name(subnet):
  logger.debug("external_name")
  ifs = all_interfaces()
  for i in ifs:
    ip=format_ip(i[1])
    if(re.match('^'+subnet,ip)):
      name=socket.gethostbyaddr(ip)[0]
      if(name): return name
  return None    


if __name__ == "__main__":

  import sys
  if(1 < len(sys.argv)):
    subnet=sys.argv[1]
  else:
    subnet="127.0.0"
  name=external_name(subnet)
  if(name): print "name-->"+name+"<--"
  ifs = all_interfaces()
  for i in ifs:
    print "%12s   %s" % (i[0], format_ip(i[1]))
  for i in ifs:
    print "%12s   %s" % (i[0], socket.gethostbyaddr(format_ip(i[1]))[0])
