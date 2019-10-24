import cv2
import numpy as np
from LaneDetection import LaneDetection
import threading
import time
from picamera.array import PiRGBArray
from picamera import PiCamera


camera_resolution = (1296, 972)
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
        for frame in self.camera.capture_continuous(self.raw_capture, format="bgr", use_video_port=True):
            capture_image = frame.array
            captured_event.set()
            print("Captured")
            self.raw_capture.truncate(0)
            if stop_event.is_set():
                cv2.destroyAllWindows()
                break


class ImageProcessingThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        threading.Thread.setDaemon(self, True)

        # self.lane_detection = LaneDetection()

    def run(self):
        global output_image, stop_event
        while not stop_event.is_set():
            output_image = self.lane_detection.process(capture_image)


class OutputDisplayThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        threading.Thread.setDaemon(self, True)

    def run(self):
        global show_image
        while not stop_event.is_set():
            # wait for capturing
            captured_event.wait()
            captured_event.clear()
            show_image = cv2.resize(capture_image, screen_size)
            cv2.imshow("Output", show_image)
            cv2.waitKey(1) & 0xFF
            print("Showing")


camera_capture_thread = CameraCaptureThread()
# image_processing_thread = ImageProcessingThread()
output_display_thread = OutputDisplayThread()

camera_capture_thread.start()
# image_processing_thread.start()
output_display_thread.start()


start_time = time.time()
while 10 > time.time() - start_time:
    pass


stop_event.set()
captured_event.clear()
