from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Hash import MD5
import base64

BS = 16
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS) 
unpad = lambda s : s[0:-ord(s[-1])]

class AESCipher:
    def __init__( self, key ):
        h = MD5.new()
        h.update(key)
        self.key = h.hexdigest()[16:]

    def encrypt( self, raw ):
        raw = pad(raw)
        iv = Random.new().read( AES.block_size )
        cipher = AES.new( self.key, AES.MODE_CBC, iv )
        return base64.b64encode( iv + cipher.encrypt( raw ) ) 

    def decrypt( self, enc ):
        enc = base64.b64decode(enc)
        iv = enc[:16]
        cipher = AES.new(self.key, AES.MODE_CBC, iv )
        return unpad(cipher.decrypt( enc[16:] ))
    
if __name__ == '__main__':
        rcm_cipher=AESCipher('pippo')
        
        message="messaggio in chiaro"
        for i in range(10):
            secret=rcm_cipher.encrypt(message)
            print "secret-->"+secret+"<---"
            clear=rcm_cipher.decrypt(secret)
            print "clear-->"+clear+"<---"
