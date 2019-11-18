import threading
from bluetooth import *
import time
import math


from BluetoothServer import BluetoothServer

with open("snap2_tiny.png", "rb") as image:
    f = image.read()
    b = bytearray(f)

single_img_byte_packet_size = 400



class BluetoothSendThread(threading.Thread):

    def __init__(self, socket):
        threading.Thread.__init__(self)
        # threading.Thread.setDaemon(self, True)
        self.socket = socket

    def run(self):
        i = 1
        # while True:
        time.sleep(5)
        self.socket.send(str(len(b)))
        for i in range(math.ceil(len(b) / single_img_byte_packet_size)):
            self.socket.send(bytes(b[i * single_img_byte_packet_size : (i+1) * single_img_byte_packet_size]))
            print("Sending ", i)

            # self.socket.send(str(i))
            # i += 1
            # time.sleep(1)


class BluetoothReceiveThread(threading.Thread):

    def __init__(self, socket):
        threading.Thread.__init__(self)
        # threading.Thread.setDaemon(self, True)
        self.socket = socket

    def run(self):
        try:
            while True:
                data = self.socket.recv(1024)
                if len(data) == 0:
                    break
                print("received [%s]" % data)
        except IOError:
            pass


bt_server = BluetoothServer()
bt_server.wait_for_client()

receive_thread = BluetoothReceiveThread(bt_server.get_client_socket())
send_thread = BluetoothSendThread(bt_server.get_client_socket())


receive_thread.start()
send_thread.start()


