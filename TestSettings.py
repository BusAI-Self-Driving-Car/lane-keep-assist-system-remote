import cv2
import numpy as np
from LaneDetection import LaneDetection
import threading
import time
from BluetoothServer import BluetoothServer


camera_resolution = (640, 480)
screen_size = (360, 240)


capture_image = np.zeros(camera_resolution + tuple([3]), np.uint8)
output_image = capture_image
show_image = np.zeros(camera_resolution + tuple([3]), np.uint8)

stop_event = threading.Event()
captured_event = threading.Event()
processed_event = threading.Event()
showed_event = threading.Event()

showed_event.set()

bluetooth_server = BluetoothServer()


class CameraCaptureThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        threading.Thread.setDaemon(self, True)

        # self.camera = PiCamera()
        # self.camera.resolution = camera_resolution
        # self.camera.framerate = 25
        # self.camera.rotation = 180
        # self.raw_capture = PiRGBArray(self.camera, size=self.camera.resolution)

        self.cap = cv2.VideoCapture('long_vid.mp4')
        if not self.cap.isOpened():
            print("Error opening file")
        time.sleep(1)

    def run(self):
        global capture_image
        while self.cap.isOpened() and not stop_event.is_set():
            showed_event.wait()
            showed_event.clear()
            ret, frame = self.cap.read()
            if ret:
                capture_image = frame
                bluetooth_server.set_image(frame)
                captured_event.set()
            else:
                break

        self.cap.release()
        stop_event.set()


class ImageProcessingThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        # threading.Thread.setDaemon(self, True)

        self.lane_detection = LaneDetection()

    def run(self):
        global output_image
        while not stop_event.is_set():
            captured_event.wait()
            captured_event.clear()
            output_image = self.lane_detection.process(capture_image) # self.lane_detection.camera.mark_roi(capture_image) # self.lane_detection.process(capture_image)
            output_image = self.lane_detection.camera.mark_roi(output_image)
            processed_event.set()


class OutputDisplayThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        # threading.Thread.setDaemon(self, True)

    def run(self):
        global show_image
        while not stop_event.is_set():
            # wait for process to finish
            processed_event.wait()
            processed_event.clear()
            show_image = cv2.resize(output_image, screen_size)
            cv2.imshow("Output", show_image)
            key = cv2.waitKey(1) & 0xFF
            showed_event.set()

            if key == ord("q"):
                stop_event.set()
            # print("Showing")


camera_capture_thread = CameraCaptureThread()
image_processing_thread = ImageProcessingThread()
output_display_thread = OutputDisplayThread()

# bluetooth_server.wait_for_client()
# # bluetooth_server.set_camera(image_processing_thread.lane_detection.camera)
# bluetooth_server.set_lane_detection(image_processing_thread.lane_detection)
# bluetooth_server.initialize_communication_threads()
# bluetooth_server.start_communication_threads()

camera_capture_thread.start()
image_processing_thread.start()
output_display_thread.start()