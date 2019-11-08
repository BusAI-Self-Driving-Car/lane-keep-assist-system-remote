import threading
from bluetooth import *
import time

from BluetoothServer import BluetoothServer


class BluetoothSendThread(threading.Thread):

    def __init__(self, socket):
        threading.Thread.__init__(self)
        # threading.Thread.setDaemon(self, True)
        self.socket = socket

    def run(self):
        i = 1
        while True:
            self.socket.send(str(i))
            i += 1
            time.sleep(1)


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


