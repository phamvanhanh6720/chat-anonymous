import json
import base64
from encryption import AESEncryption, generate_vector

BUFFERSIZE = 10
PASSWORD = b''
enc = None


def return_vector():
    # it's a bit sketchy but it's needed because we import encryption.py only in this file
    return generate_vector()


def initialize_AES(key):
    global PASSWORD
    global enc
    PASSWORD = key
    enc = AESEncryption(PASSWORD)


# generates a message with a fixed header which specifies the length of the message (returns bytes)
def create_msg(data):
    if "iv_exc" not in data and "key_exc" not in data:
        # everytime we generate a object, it can't be reused
        cipher = enc.generate_cipher()

        # base64 represents bytes object in strings
        encrypted_data = base64.b64encode(cipher.encrypt(data.encode("utf-8")))

        final_msg = encrypted_data.decode("utf-8")
        final_msg = f'{len(final_msg):<10}' + final_msg

        return final_msg.encode("utf-8")
    else:
        final_msg = data
        final_msg = f'{len(final_msg):<10}' + final_msg
        return final_msg.encode("utf-8")
