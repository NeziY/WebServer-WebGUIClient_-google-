import socket
import sys
import threading
from _thread import *
import hashlib
import base64

all_connections = []
all_addresses = []

# -----------------CREATE SOCKET----------------- #

def socket_create():
    try:
        global host
        global port
        global s
        host = ''
        port = 9989
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error as msg:
        print("Socket creation error " + str(msg))

# -----------------BIND SOCKET----------------- #

def socket_bind():
    try:
        global host
        global port
        global s
        print("Binding socket to port " + str(port))
        s.bind((host, port)) # tuple
        s.listen(5)
    except socket.error as msg:
        print("Socket binding error " + str(msg) + "\n" + "Retrying...")
        socket_bind()

# -----------------THREAD FOR LISTENING TO INCOMING DATA----------------- #

class startThreadClass(threading.Thread):
    def __init__(self, conn):
        threading.Thread.__init__(self)
        self.conn = conn

    def run(self):
        listening_for_msgs(self.conn)

# -----------------THREAD FOR RESPONDING TO CLIENTS HANDSHAKE----------------- #

class startHandshakeThread(threading.Thread):
    def __init__(self, handshake, conn):
        threading.Thread.__init__(self)
        self.handshake = handshake
        self.conn = conn
    def run(self):
        handshake_resp = create_handshake_resp(self.handshake)
        self.conn.send(str.encode(handshake_resp, 'utf-8'))
        print("handshake sent to client")

# -----------------ACCEPT CONNECTIONS FROM MULTIPLE CLIENTS----------------- #

def accept_connections():
    try:
        for c in all_connections:
            c.close()
            del all_connections[:]
            del all_addresses[:]
        while 1:
            try:
                conn, address = s.accept()
                conn.setblocking(1) # I dont want any time out
                all_connections.append(conn)
                all_addresses.append(address)

                startThread = startThreadClass(conn)
                startThread.start()

                print("\nConnection has been established: " + address[0]) # Printing out the IP address
            except:
                print("Error accepting connections")
    except KeyboardInterrupt:
        sys.exit()
# -----------------SENDS FILE WHEN CLIENT REQUESTS FOR HTML FILE ----------------- #


def send_file(conn, msg):
    file_content = ""
    if msg == "server":
        with open("clientHTML.html") as f:
            for line in f:
                file_content += line
            conn.send(str.encode(file_content, 'utf-8'))
            f.close()
    if msg == 'google.com':
        conn.send(str.encode('google.com', 'utf-8'))

# -----------------LISTEN FOR INCOMING DATA FUNCTION----------------- #


def listening_for_msgs(conn):
    while True:
        try:
            rcv_msg = conn.recv(1024)
            rcv_msg_str = str(rcv_msg[:].decode("utf-8"))
            rcv_msg_list = rcv_msg_str.split('\r\n')
            if rcv_msg_list[0] == 'GET / HTTP/1.1':
                HandshakeThread = startHandshakeThread(rcv_msg_str, conn)
                HandshakeThread.start()
            elif rcv_msg_str == 'server':
                send_file(conn, "server")
            elif rcv_msg_str == "google.com" or rcv_msg_str != "":
                send_file(conn, 'google.com')
                print(rcv_msg_str)
            else:
                pass

        except UnicodeDecodeError:
            client_resp = unmask_data(rcv_msg)
            print(client_resp)

# -----------------UNMASKING CLIENTS PACKET FUNCTION----------------- #


def unmask_data(rcv_msg):
    try:
        # as a simple server, we expect to receive:
        #    - all data at one go and one frame
        #    - one frame at a time
        #    - text protocol
        #    - no ping pong messages
        data = bytearray(rcv_msg)
        if len(data) < 6:
            raise Exception("Error reading data")
        # FIN bit must be set to indicate end of frame
        assert (0x1 == (0xFF & data[0]) >> 7)
        # data must be a text frame
        # 0x8 (close connection) is handled with assertion failure
        assert (0x1 == (0xF & data[0]))

        # assert that data is masked
        assert (0x1 == (0xFF & data[1]) >> 7)
        datalen = (0x7F & data[1])

        # print("received data len %d" %(datalen,))

        str_data = ''
        if datalen > 0:
            mask_key = data[2:6]
            masked_data = data[6:(6 + datalen)]
            unmasked_data = [masked_data[i] ^ mask_key[i % 4] for i in range(len(masked_data))]
            str_data = str(bytearray(unmasked_data).decode("utf-8"))
        return str_data
    except AssertionError:
        pass
# -----------------HANDSHAKE RESPONSE FUNCTION----------------- #


def create_handshake_resp(handshake):
    final_line = ""
    lines = handshake.splitlines()
    for line in lines:
        parts = line.partition(": ")
        if parts[0] == "Sec-WebSocket-Key":
            key = parts[2]

    magic = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
    key_magic_encoded = (key + magic).encode('utf-8')
    accept_key = base64.b64encode(hashlib.sha1(key_magic_encoded).digest())
    accept_key = str(accept_key.decode("utf-8"))
    return (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: WebSocket\r\n"
        "Connection: Upgrade\r\n"
        "Sec-WebSocket-Accept: " + str(accept_key) + "\r\n\r\n")

# -----------------MAIN FUNCTION----------------- #

def main():
    socket_create()
    socket_bind()
    accept_connections()

main()
