import cv2
import numpy as np
from LaneDetection import LaneDetection
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
        self.camera.rotation = 180
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
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                stop_event.set()
            # print("Showing")


camera_capture_thread = CameraCaptureThread()
image_processing_thread = ImageProcessingThread()
output_display_thread = OutputDisplayThread()

camera_capture_thread.start()
image_processing_thread.start()
output_display_thread.start()


start_time = time.time()
while 10 > time.time() - start_time:
    pass


stop_event.set()
captured_event.clear()
processed_event.clear()
