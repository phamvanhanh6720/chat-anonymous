# This class stores all the necessary information for a client connection all in a single object
class ClientConnection:
    def __init__(self, socket_obj, username, enc_key):
        self.socket_obj = socket_obj
        self.username = username
        self.enc_key = enc_key

    # returns the clients address
    def get_ip(self):
        return self.socket_obj.getsockname()[0]