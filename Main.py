import cv2
import numpy as np
from Camera import Camera
from LaneKeepAssistSystem import LaneKeepAssistSystem
import threading
import time

camera_resolution = (1296, 972)

capture_image = np.zeros(camera_resolution + tuple(3), np.uint8)


class CameraCaptureThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

        self.camera = PiCamera()
        self.camera.resolution = camera_resolution
        self.camera.framerate = 25
        self.camera.rotation = 90
        self.raw_capture = PiRGBArray(camera, size=self.camera.resolution)

    def run(self):
        global capture_image
        for frame in self.camera.capture_continuous(self.raw_capture, format="bgr", use_video_port=True):
            capture_image = frame.array


class ImageProcessingThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        pass


class OutputDisplayThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        pass


camera = Camera()
lka = LaneKeepAssistSystem()

# camera.calibrateCamera()
# camera.loadCameraProperties()

image = cv2.imread("sample_road_img_13.png")
out_img = lka.process(image)

cv2.imwrite("out.png", out_img)

# c = cv2.waitKey(0)
# if 'q' == chr(c & 255):
#     cv2.destroyAllWindows()