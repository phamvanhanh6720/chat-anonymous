import socket
import hashlib
import base64
from Crypto.Cipher import AES 
from Crypto import Random

# vector is global, we start with None
IV = None


def generate_vector():
    global IV

    if IV is None:
        # we save it as bytes
        IV = Random.new().read(AES.block_size)

    # initialization vector, we need to make this random. It can be shared in plain text, it's not secret.
    return base64.b64encode(IV)


class AESEncryption:
    def __init__(self, password):
        self.PASSWORD = password
        # generating a 32 bytes key
        self.KEY = hashlib.sha256(self.PASSWORD).digest()

        self.MODE = AES.MODE_CFB

    def generate_cipher(self):
        # so here we can grab the unique vector
        return AES.new(self.KEY, self.MODE, IV=IV)






