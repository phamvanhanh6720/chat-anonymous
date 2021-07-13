import socket
import json
import threading
import argparse
import sys
import os
import time
from datetime import datetime
from message import Message
from streaming import create_msg, stream_data, initialize_AES
import pyDHE
import eel

# this is temporary, just for debuggining when you want to open two clients on one computer
# Note that there is a small chance the random port numbers will be the same and crash anyway.
import random

# [GLOBAL VARIABLES]
client = None # so we can use it in exposed functions

# diffie hellman object
clientDH = pyDHE.new()

# contains names only of all the clients connected
client_list = [];


class Client:
    def __init__(self, server_ip, port, client_ip):
        self.SERVER_IP = server_ip
        self.PORT = port
        self.CLIENT_IP = client_ip
        self.finalDecryptionKey = None

        print(f"[*] Host: {self.CLIENT_IP} | Port: {self.PORT}")

        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect_to_server(self):
        try:
            self.client.connect((self.SERVER_IP, self.PORT))
        except socket.error as e:
            print(str(e))
            sys.exit()

        iv = self.recv_vector() # we receive the vector
        final_decryption_key = self.recv_server_key()

        self.share_public_info()
        initialize_AES(str(final_decryption_key).encode("utf-8"), iv.cont) # we even parse the vector message content
        self.set_username()

    def recv_server_key(self):
        # receives the servers public key and uses it to generate the final decryption key
        server_key = Message.from_json(stream_data(self.client).decode("utf-8"))
        return clientDH.update(int(server_key.cont))

    def share_public_info(self):
        packet = Message(self.CLIENT_IP, self.SERVER_IP, "temp", str(datetime.now()), str(clientDH.getPublicKey()), 'key_exc')
        self.client.send(packet.pack())

    def recv_vector(self):
        iv = stream_data(self.client).decode("utf-8")
        return Message.from_json(iv)

    def set_username(self):
        while True:
            self.USERNAME = input("Enter username> ")
            if self.USERNAME:
                if self.USERNAME != "*server*":
                    # encrypted_username = self.cipher.encrypt(self.USERNAME.encode("utf-8"))
                    packet = Message(self.CLIENT_IP, self.SERVER_IP, "temp", str(datetime.now()), self.USERNAME, 'setuser')

                    self.client.send(packet.pack())

                    check = stream_data(self.client).decode("utf-8")
                    check = Message.from_json(check)
                    print(check.cont)

                    if check.cont != "[*] Username already in use!":
                        break

                else:
                    print("Can't set username as *server*!")

            else:
                print("Username can't be empty!")

    def send_msg(self, to_send_msg):
        if to_send_msg == "[export_chat]":
            packet = Message(self.CLIENT_IP, self.SERVER_IP, self.USERNAME, str(datetime.now()), to_send_msg, 'export')
        else:
            packet = Message(self.CLIENT_IP, self.SERVER_IP, self.USERNAME, str(datetime.now()), to_send_msg, 'default')

        self.client.send(packet.pack())

    def receive_data(self):
        while True:
            try:
                data = stream_data(self.client)
                data = data.decode("utf-8")
                data = Message.from_json(data) # it's a dataclass object
            except AttributeError:
                print("\r[*] Connection closed by the server")
                break
            print(data)
            if data.typ == "export":
                timestamp = str(datetime.now())
                timestamp = timestamp.replace(":", ".") # windowz is stoopid

                chat_file = f"./exported/chat{timestamp}.txt"

                try:
                    with open(chat_file, "wb+") as chat:
                        chat.write(data.cont.encode("utf-8"))
                        print("\r[*] Writing to file...")

                    print(f"[*] Finished! You can find the file at {chat_file}")
                except:
                    print('\r' + "[*] Something went wrong")
            elif data.typ == "client_list_update_add" or data.typ == "disconnection":
                update_client_list(data.cont)
            else:
                eel.writeMsg(data.cont, data.username)

        self.client.close()


# updates the gui with the list 'c_list'
def update_client_list(c_list):
    client_list = c_list

    # update the GUI
    eel.updateClientList(client_list);


# [Eel functions]
@eel.expose
def exposeSendMsg(to_send_msg):
    client.send_msg(to_send_msg)


@eel.expose
def getUsername():
    return client.USERNAME


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--server", dest="server_ip", help="Enter server IP")
    parser.add_argument("-p", "--port", dest="server_port", help="Enter server PORT")

    options = parser.parse_args()

    if not options.server_ip and not options.server_port:
        raise Exception # raising exception in case the user doesn't provide values from the terminal

    if not options.server_ip:
        parser.error("*** Please specify a server IP ***")
    elif not options.server_port:
        parser.error("*** Please specify a port number ***")
    else:
        return options


def start_eel():
    try:
        eel.init(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'GUI', 'web'))
        eel.start('main.html', port=random.choice(range(8000, 8080)))

    except (SystemExit, MemoryError, KeyboardInterrupt):
        print("*** Closing the app... ***")
        os._exit(0)


def main():
    try:
        os.mkdir('exported')
    except FileExistsError:
        pass

    try:
        options = get_args()

        SERVER_IP = options.server_ip
        PORT = int(options.server_port)
    except Exception:
        SERVER_IP = input("*** Enter server IP address > ")
        PORT = int(input("*** Enter server PORT number > "))

    CLIENT_IP = socket.gethostbyname(socket.gethostname())

    global client
    client = Client(SERVER_IP, PORT, CLIENT_IP)
    client.connect_to_server()

    # threading eel in the background
    e_thread = threading.Thread(target = start_eel)
    e_thread.daemon = True
    e_thread.start()

    # this is a loop and also stream_data is blocking
    client.receive_data()


if __name__ == "__main__":
    main()
