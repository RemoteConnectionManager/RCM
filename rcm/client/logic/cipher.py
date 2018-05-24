# std lib
import sys
import string
import random

# local includes
# VNC password encription python implementation
# from https://github.com/trinitronx/vncpasswd.py
import client.logic.d3des as d3des
from client.miscellaneous.logger import logic_logger


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
            import client.logic.aes_cipher as aes_cipher
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
