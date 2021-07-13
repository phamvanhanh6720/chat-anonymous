import socket
import json
import threading
import sys
import argparse
import os
from datetime import datetime
from message import Message
from streaming import create_msg, stream_data, initialize_AES, decrypt_msg, return_vector
from client_connection_obj import ClientConnection
import pyDHE
import time

# DiffieHellman object
serverDH = pyDHE.new()


class Server:
    def __init__(self, ip, port):
        self.IP = ip
        self.PORT = port

        self.USERNAME = "*server*"

        # flag for loop logic
        self.temp_f = False

        # holds a list of client connection objects
        self.client_connections = []

        self.current_chat = os.path.join(os.path.dirname(os.path.relpath(__file__)), 'logs/currentchat.txt')

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start_server(self):
        try:
            self.server.bind((self.IP, self.PORT))
        except socket.error as e:
            print(str(e))

        self.server.listen(10)

        print(f"[*] Starting server ({self.IP}) on port {self.PORT}")

    def accept_connections(self):
        while True:
            client_socket, address = self.server.accept()
            print(f"[*] Connection from {address} has been established!")

            # instantiate a client connection obj with the username and encryption key initially set to null
            self.client_connections.append(ClientConnection(client_socket, None, None))

            c_thread = threading.Thread(target=self.handler, args=[self.find_connection_from_socket(client_socket)])
            c_thread.daemon = True
            c_thread.start()

            self.share_vector(client_socket, address[0])
            # to avoid buffer congestion
            time.sleep(0.1)
            self.share_public_key(client_socket, address[0])
            # to avoid buffer congestion
            time.sleep(0.1)

    # exception is the name it should not include (leave blank to get all)
    def generate_client_names(self, exception=None):
        names = []
        for connection in self.client_connections:
            if exception is not None:
                if connection.username != exception:
                    names.append(connection.username)

        return names

    def stop_server(self):
        for conn in self.client_connections:
            conn.socket_obj.close()

        try:
            os.remove(self.current_chat)
        except FileNotFoundError:
            print("*** Nothing to clear in the logs")

        self.server.close()

    def share_vector(self, client_socket, address):
        # returns vector from streaming.py where we get it from encryption, this is base64
        content = return_vector().decode("utf-8")
        packet = Message(self.IP, address, self.USERNAME, str(datetime.now()), content, typ='iv_exc')
        client_socket.send(packet.pack())

    def share_public_key(self, client_socket, address):
        packet = Message(self.IP, address, self.USERNAME, str(datetime.now()), str(serverDH.getPublicKey()), 'key_exc')
        client_socket.send(packet.pack())

    def log_current_chat(self, username, msg):
        with open(self.current_chat, 'a+') as currentchat:
            currentchat.write(username + "> " + msg + '\n')

    def check_username(self, client_socket_obj, data):
        flag = False

        for user in self.client_connections:
            if user.username == data.cont:
                flag = True
                self.temp_f = True

                content = "[*] Username already in use!"

                warning = Message(self.IP, client_socket_obj.get_ip(), self.USERNAME, str(datetime.now()), content,
                                  'username_taken')

                self.send_message_to_client(client_socket_obj, warning)
                break

        if not flag:
            client_socket_obj.username = data.cont

            content = "[*] You have joined the chat!"

            joined = Message(self.IP, client_socket_obj.get_ip(), self.USERNAME, str(datetime.now()), content,
                             'approved_conn')

            self.send_message_to_client(client_socket_obj, joined)
            time.sleep(1)

            # update all others client list
            for connection in self.client_connections:

                list_to_send = self.generate_client_names(
                    connection.username)
                client_list_update = Message(self.IP, connection.get_ip(), self.USERNAME, str(datetime.now()),
                                             list_to_send, 'client_list_update_add', True)
                self.send_message_to_client(connection, client_list_update)

    def send_logged_chat(self, client_socket_obj):
        with open(self.current_chat, "rb") as chat:
            content = chat.read().decode("utf-8")

            packet = Message(self.IP, client_socket_obj.get_ip(), self.USERNAME, str(datetime.now()), content, 'export')

            self.send_message_to_client(client_socket_obj, packet)
            print("[*] Sent!")

    def close_connection(self, client_socket_obj):
        disconnected_msg = f"[{client_socket_obj.username}] has left the chat"
        left_msg_obj = Message(self.IP, "allhosts", self.USERNAME, str(datetime.now()), disconnected_msg, 'default')

        self.client_connections.remove(client_socket_obj)

        for connection in self.client_connections:
            # sends an alert in chat that they left
            self.send_message_to_client(connection, left_msg_obj)

            # update everyone client list with the new list
            list_to_send = self.generate_client_names(
                connection.username) 
            client_list_update = Message(self.IP, connection.get_ip(), self.USERNAME, str(datetime.now()), list_to_send,
                                         'disconnection', True)
            self.send_message_to_client(connection, client_list_update)

        if not self.client_connections:
            try:
                os.remove(self.current_chat)
            except FileNotFoundError:
                print("*** Nothing to clear in the logs")

        client_socket_obj.socket_obj.close()

    @staticmethod
    def send_message_to_client(client, content):
        """
        Send a message to specified client using their unique encryption key
        :param client: a client socket connection object
        :param content: instance of Message class
        :return:
        """
        key = client.enc_key

        # update the servers encryption class with the specific clients key
        initialize_AES(str(key).encode("utf-8"))

        # send the message with the new AES object initialized
        client.socket_obj.send(content.pack())

    def handler(self, client_socket_obj):
        # renaming
        client_socket = client_socket_obj.socket_obj
        # renaming
        address = client_socket_obj.get_ip()

        while True:
            try:
                ''' HANDLING DATA FLOW '''
                # stream it
                data = stream_data(client_socket)

                # decrypting it
                data = decrypt_msg(data, client_socket_obj.enc_key)
                # converting to obj
                data = Message.from_json(data)

            except ConnectionResetError:
                print(f"*** [{address}] unexpectedly closed the connection, received only an RST packet.")
                self.close_connection(client_socket_obj)
                break
            except AttributeError:
                print(f"*** [{address}] disconnected")
                self.close_connection(client_socket_obj)
                break
            except UnicodeDecodeError:
                print(f"*** [{address}] disconnected due to an encoding error")
                self.close_connection(client_socket_obj)
                break
            except TypeError:
                print(f"*** [{address}] disconnected")
                self.close_connection(client_socket_obj)
                break

            if data.typ == 'setuser':
                # clientConnection obj updated in the self.checkUsername function
                self.check_username(client_socket_obj, data)

                if self.temp_f:
                    continue
            elif data.typ == 'key_exc':
                final_key = serverDH.update(int(data.cont))  # generating the shared private secret
                client_socket_obj.enc_key = final_key
            else:
                if data.cont != '':
                    if data.typ == 'default':
                        self.log_current_chat(data.username, data.cont)

                    if data.typ == 'export':
                        print("*** Sending chat...")
                        self.send_logged_chat(client_socket_obj)
                    else:
                        for connection in self.client_connections:
                            if connection.socket_obj != client_socket:
                                # broadcasting
                                self.send_message_to_client(connection, data)

    # returns the client connection object from a socket object (returns None if none exist)
    def find_connection_from_socket(self, sock_obj):
        for connection in self.client_connections:
            if connection.socket_obj == sock_obj:
                return connection
        return None


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", dest="port", help="Start server on port X")

    options = parser.parse_args()

    if not options.port:
        raise Exception
    else:
        return options


def main():
    try:
        os.mkdir('logs')
    except FileExistsError:
        pass

    with open('./logs/currentchat.txt', 'w+') as f:
        f.write("{Start of conversation}\n")
    try:
        options = get_args()
        PORT = int(options.port)
    except Exception:  # if the user doesn't parse values from the command line
        PORT = int(input("*** Start server on port > "))

    IP = '127.0.0.1'

    server = Server(IP, PORT)

    try:
        server.start_server()
        server.accept_connections()

    except KeyboardInterrupt:
        print("*** Closing all the connections ***")
        server.stop_server()
        print("*** Server stopped ***")

    except Exception as e:
        print("General error", str(e))


if __name__ == "__main__":
    main()
