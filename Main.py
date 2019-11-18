import cv2
import numpy as np
from LaneDetection import LaneDetection
from BluetoothServer import BluetoothServer
import threading
import time
from picamera import PiCamera
from picamera.array import PiRGBArray
import picamera.array


camera_resolution = (640, 480)
screen_size = (360, 240)


capture_image = np.zeros(camera_resolution + tuple([3]), np.uint8)
output_image = capture_image
show_image = np.zeros(camera_resolution + tuple([3]), np.uint8)

stop_event = threading.Event()
captured_event = threading.Event()
processed_event = threading.Event()


class CameraCaptureThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        threading.Thread.setDaemon(self, True)

        self.camera = PiCamera()
        self.camera.resolution = camera_resolution
        self.camera.framerate = 25
        self.camera.rotation = 90
        self.raw_capture = PiRGBArray(self.camera, size=self.camera.resolution)

        time.sleep(1)

    def run(self):
        global capture_image
        # while not stop_event.is_set():
        #     with picamera.array.PiRGBArray(self.camera) as frame:
        #         self.camera.capture(frame, format='bgr')
        #         # At this point the image is available as stream.array
        #         capture_image = frame.array
        #         captured_event.set()
        # cv2.destroyAllWindows()
        # self.camera.close()
        for frame in self.camera.capture_continuous(self.raw_capture, format="bgr", use_video_port=True):
            capture_image = frame.array
            captured_event.set()
            # print("Captured")
            self.raw_capture.truncate(0)
            if stop_event.is_set():
                cv2.destroyAllWindows()
                self.camera.close()
                break


class ImageProcessingThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        threading.Thread.setDaemon(self, True)

        self.lane_detection = LaneDetection()

    def run(self):
        global output_image
        while not stop_event.is_set():
            captured_event.wait()
            captured_event.clear()
            output_image = self.lane_detection.process(capture_image)
            # print("Processed")
            processed_event.set()



class OutputDisplayThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        threading.Thread.setDaemon(self, True)

    def run(self):
        global show_image
        while not stop_event.is_set():
            # wait for process to finish
            processed_event.wait()
            processed_event.clear()
            show_image = cv2.resize(output_image, screen_size)
            cv2.imshow("Output", show_image)
            cv2.waitKey(1) & 0xFF
            # print("Showing")

class BluetoothConnectionThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        threading.Thread.setDaemon(self, True)
        self.bluetooth_server = BluetoothServer()
        self.client_socket = None

    def run(self):
        self.bluetooth_server.wait_for_client()
        self.client_socket = self.bluetooth_server.get_client_socket()

    class ReceiveThread(threading.Thread):
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

    class SendThread(threading.Thread):
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






camera_capture_thread = CameraCaptureThread()
image_processing_thread = ImageProcessingThread()
output_display_thread = OutputDisplayThread()

camera_capture_thread.start()
image_processing_thread.start()
output_display_thread.start()


start_time = time.time()
while 60 > time.time() - start_time:
    pass


stop_event.set()
captured_event.clear()
processed_event.clear()
