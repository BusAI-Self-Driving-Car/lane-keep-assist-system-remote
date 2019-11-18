import os
import time
from bluetooth import *
import select

# os.system("sudo hciconfig hci0 piscan")
# os.system("sudo sdptool add SP")
#
# server = BluetoothSocket(RFCOMM)
# server.bind(("", PORT_ANY))
# server.listen(1)
#
# port = server.getsockname()[1]
# print(port)
#
# uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
# advertise_service(server, "RaspberryServer", uuid)
# print("Waiting for connection")
# client_sock, client_info = server.accept()
# print("Accepted connection from ", client_info)
#
# try:
# 	while True:
# 		data = client_sock.recv(1024)
# 		if len(data) == 0: break
# 		print("received [%s]" % data)
# except IOError:
# 	pass
#
# print("disconnected")
#
# client_sock.close()
# server.close()
# print("all done")


class BluetoothServer:

	uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"

	def __init__(self):
		os.system("sudo hciconfig hci0 piscan")
		os.system("sudo sdptool add SP")
		self.server = BluetoothSocket(RFCOMM)
		self.server.bind(("", PORT_ANY))
		self.server.listen(1)
		self.port = self.server.getsockname()[1]

		self.client_sock = None
		self.client_info = None
		self.sendFlag = False

	def wait_for_client(self):
		advertise_service(self.server, "RaspberryServer", service_id=self.uuid)
		print("Waiting for connection")
		self.client_sock, self.client_info = self.server.accept()
		print("Accepted connection from: ", self.client_info)
		return True

	def get_client_socket(self):
		return self.client_sock
