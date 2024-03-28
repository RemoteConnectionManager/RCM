#
# Copyright (c) 2014-2019 CINECA.
#
# This file is part of RCM (Remote Connection Manager) 
# (see http://www.hpc.cineca.it/software/rcm).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import sys
import string
import random

# local includes
# VNC password encription python implementation
# from https://github.com/trinitronx/vncpasswd.py
import rcm.client.logic.d3des as d3des
from rcm.client.miscellaneous.logger import logic_logger


def vnc_crypt(vncpass, decrypt=False):
    if decrypt:
        try:
            if sys.version_info >= (3, 0):
                import binascii
                passpadd = binascii.unhexlify(vncpass)
            else:
                passpadd = vncpass.decode('hex')
        except TypeError as e:
            if e.message == 'Odd-length string':
                logic_logger.warning('WARN: %s . Chopping last char off... "%s"' % (e.message, vncpass[:-1] ))
                passpadd = vncpass[:-1].decode('hex')
            else:
                raise
    else:
        passpadd = (vncpass + '\x00'*8)[:8]
        passpadd = passpadd.encode('utf-8')
    strkey = u''.join([chr(x) for x in d3des.vnckey])

    if sys.version_info >= (3, 0):
        # python3
        key = d3des.deskey(strkey.encode('utf-8'), decrypt)
        crypted = d3des.desfunc(passpadd, key)
    else:
        key = d3des.deskey(strkey, decrypt)
        crypted = d3des.desfunc(passpadd, key)

    if decrypt:
        if sys.version_info >= (3, 0):
            import binascii
            hex_crypted = binascii.unhexlify(binascii.hexlify(crypted)).decode('utf-8')
        else:
            hex_crypted = crypted.encode('hex').decode('hex')
        return hex_crypted
    else:
        if sys.version_info >= (3, 0):
            import binascii
            hex_crypted = binascii.hexlify(crypted).decode('utf-8')
        else:
            hex_crypted = crypted.encode('hex')
        return hex_crypted


class RCMCipher:
    def random_pwd_generator(self, size=8, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    def __init__(self, encryptpass=None):
        self.encryptpass = encryptpass
        self.vncpassword = self.random_pwd_generator()
        self.acypher = None
        if self.encryptpass:
            import rcm.client.logic.aes_cipher as aes_cipher
            self.acypher = aes_cipher.AESCipher(self.encryptpass)

    def encrypt(self, vncpassword=None):
        if not vncpassword:
            vncpassword = self.vncpassword
        if self.acypher:
            return self.acypher.encrypt(vncpassword).decode('utf-8')
        else:
            return vnc_crypt(vncpassword, decrypt=False)

    def decrypt(self, vncpassword):
        if self.acypher:
            return self.acypher.decrypt(vncpassword).decode('utf-8')
        else:
            return vnc_crypt(vncpassword, decrypt=True)
