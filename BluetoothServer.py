import os
from bluetooth import *

os.system("sudo hciconfig hci0 piscan")
os.system("sudo sdptool add SP")

server = BluetoothSocket(RFCOMM)
server.bind(("", PORT_ANY))
server.listen(1)

port = server.getsockname()[1]
print(port)

uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
advertise_service(server, "SampleServer", uuid)
print("Waiting for connection")
client_sock, client_info = server.accept()
print("Accepted connection from ", client_info)

try:
	while True:
		data = client_sock.recv(1024)
		if len(data) == 0: break
		print("received [%s]" % data)
except IOError:
	pass

print("disconnected")

client_sock.close()
server.close()
print("all done")
