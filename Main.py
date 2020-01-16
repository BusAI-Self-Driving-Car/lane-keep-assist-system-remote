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

camera_resolution = (640, 480)
screen_size = (360, 240)

assistant_time_brake = 1 # seconds

alert_time_brake = 2 # seconds

capture_image = np.zeros(camera_resolution + tuple([3]), np.uint8)
output_image = capture_image
show_image = np.zeros(camera_resolution + tuple([3]), np.uint8)

stop_event = threading.Event()
captured_event = threading.Event()
processed_event = threading.Event()
showed_event = threading.Event()
showed_event.set()

bluetooth_server = BluetoothServer()

lane_detection = LaneDetection()



class CameraCaptureThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        # threading.Thread.setDaemon(self, True)

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
            frame_img = lane_detection.camera.undistort(frame.array)
            capture_image = frame_img
            bluetooth_server.set_image(frame_img)
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
        # threading.Thread.setDaemon(self, True)

        # self.lane_detection = LaneDetection()

        self.alert_time = time.time()
        self.assistant_time = time.time()
        self.fps_time = time.time()

    def run(self):
        global output_image
        while not stop_event.is_set():
            captured_event.wait()
            captured_event.clear()
            output_image, alert, offset, priority = lane_detection.process(capture_image) # self.lane_detection.camera.mark_roi(capture_image) # self.lane_detection.process(capture_image)
            fps = round(1. / (time.time() - self.fps_time), 1)
            output_image = self.mark_fps(output_image, fps)
            self.fps_time = time.time()
            if time.time() - self.assistant_time > assistant_time_brake:
                direction = "L " if offset > 0 else "R "
                # if abs(offset) < 0.2:
                #     priority = 0
                # elif abs(offset) < 0.39:
                #     priority = 1
                # else:
                #     priority = 2
                bluetooth_server.send("alert " + str(priority) + " " + direction + str(abs(offset)), BluetoothServer.STATE_CUSTOM_SENDING)

                self.assistant_time = time.time()

            # output_image = lane_detection.camera.mark_roi(output_image)
            processed_event.set()

    def mark_fps(self, img, fps):
        out_img = img.copy()
        font = cv2.FONT_HERSHEY_SIMPLEX
        text1 = str(fps) + " fps"
        cv2.putText(out_img, text1, (500, 10), font, 0.75, (255, 0, 150), 2)
        return out_img


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

bluetooth_server.wait_for_client()
# bluetooth_server.set_camera(image_processing_thread.lane_detection.camera)
bluetooth_server.set_lane_detection(lane_detection)
bluetooth_server.initialize_communication_threads()
bluetooth_server.start_communication_threads()

camera_capture_thread.start()
image_processing_thread.start()
output_display_thread.start()
