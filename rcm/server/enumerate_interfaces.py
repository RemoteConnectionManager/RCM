# Use those functions to enumerate all interfaces available on the system using Python.
# found on <http://code.activestate.com/recipes/439093/#c1>

import sys
import socket
import fcntl
import struct
import array
import re
from  logger_server import logger


def all_interfaces():
    is_64bits = sys.maxsize > 2**32
    struct_size = 40 if is_64bits else 32
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    max_possible = 8 # initial value
    while True:
        _bytes = max_possible * struct_size
        names = array.array('B')
        for i in range(0, _bytes):
            names.append(0)
        outbytes = struct.unpack('iL', fcntl.ioctl(
            s.fileno(),
            0x8912,  # SIOCGIFCONF
            struct.pack('iL', _bytes, names.buffer_info()[0])
        ))[0]
        if outbytes == _bytes:
            max_possible *= 2
        else:
            break
    namestr = names.tostring()
    ifaces = []
    for i in range(0, outbytes, struct_size):
        iface_name = bytes.decode(namestr[i:i+16]).split('\0', 1)[0]
        iface_addr = socket.inet_ntoa(namestr[i+20:i+24])
        ifaces.append((iface_name, iface_addr))

    return ifaces

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
        try:
            name=socket.gethostbyaddr(ip)[0]
            if(name): return name
        except Exception as e:
            logger.warning("ERROR {0}: ".format(e) + "in external_name subnet->" +
                                  subnet + "< ip->" + ip + "<")
  return None


if __name__ == "__main__":

  import sys
  if(1 < len(sys.argv)):
    subnet=sys.argv[1]
  else:
    subnet="127.0.0"
  name=external_name(subnet)
  if(name): print("name-->"+name+"<--")
  ifs = all_interfaces()
  for i in ifs:
    print("%12s   %s" % (i[0], format_ip(i[1])))
  for i in ifs:
    print("%12s   %s" % (i[0], external_name(format_ip(i[1]))))
