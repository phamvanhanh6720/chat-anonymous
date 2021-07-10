import json
import base64
from encryption import AESEncryption

BUFFERSIZE = 10
PASSWORD = b''
enc = None


def initialize_AES(key, VECTOR): # vector parsed
    global PASSWORD
    global enc
    PASSWORD = key
    enc = AESEncryption(PASSWORD, VECTOR)


# generates a message with a fixed header which specifies the length of the message (returns bytes)
def create_msg(data):
    if enc is not None:
        cipher = enc.generate_cipher() # everytime we generate a object, it can't be reused
        encrypted_data = base64.b64encode(cipher.encrypt(data.encode("utf-8"))) # base64 rappresents bytes object in strings

        final_msg = encrypted_data.decode("utf-8")
        final_msg = f'{len(final_msg):<10}' + final_msg

        return final_msg.encode("utf-8")
    else:
        final_msg = data
        final_msg = f'{len(final_msg):<10}' + final_msg

        return final_msg.encode("utf-8")


def stream_data(target):
    data = target.recv(BUFFERSIZE)
    if len(data) != 0:
        msglen = int(data[:BUFFERSIZE].strip())
        full_data = b''

        # stream the data in with a set buffer size
        while len(full_data) < msglen:
            full_data += target.recv(BUFFERSIZE)

        if "iv_exc" not in full_data.decode("utf-8") and "key_exc" not in full_data.decode("utf-8"):
            # everytime we generate a object, it can't be reused
            cipher = enc.generate_cipher()

            full_data = base64.b64decode(full_data)

            decrypted_data = cipher.decrypt(full_data)
            # returning just the bytes, json operations done later in the code to avoid importing errors

            return decrypted_data
        return full_data
    else:
        pass
