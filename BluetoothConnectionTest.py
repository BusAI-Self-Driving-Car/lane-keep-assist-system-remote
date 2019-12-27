import threading
from bluetooth import *
import time
import math
import cv2

from Camera import Camera

from BluetoothServer import BluetoothServer

capture_image = cv2.imread("snap2.png")

# with open("snap2_tiny.png", "rb") as image:
#     f = image.read()
#     b = bytearray(f)
#
# single_img_byte_packet_size = 400


cam = Camera()

bt_server = BluetoothServer()
bt_server.wait_for_client()

bt_server.set_camera(cam)

bt_server.set_image(capture_image)

bt_server.initialize_communication_threads()
bt_server.start_communication_threads()

while True:
    print("cam", cam.get_perspective_src_points_to_str())
    time.sleep(6)

# receive_thread = BluetoothReceiveThread(bt_server.get_client_socket())
# send_thread = BluetoothSendThread(bt_server.get_client_socket())
#
#
# receive_thread.start()
# send_thread.start()


