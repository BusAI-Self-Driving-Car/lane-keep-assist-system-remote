from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2
import numpy as np
import time

camera_resolution = (640, 480)

image = np.zeros((640, 480, 3), np.uint8)

if_writing = False
if_opened_done = False
if_closed_done = True

timestr = time.strftime("%Y%m%d_%H%M%S")
out = cv2.VideoWriter('video_' + timestr + '.mp4', cv2.VideoWriter_fourcc('M','J','P','G'), 10, camera_resolution)


def capture_image(event, x, y, flags, param):
    global if_writing
    if event == cv2.EVENT_LBUTTONDOWN:
         if_writing = not if_writing
#        timestr = time.strftime("%Y%m%d_%H%M%S")
#        cv2.imwrite("cam-calibration-images/IMG_" + timestr + ".png", image)


# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = camera_resolution
camera.framerate = 25
camera.rotation = 180
rawCapture = PiRGBArray(camera, size=camera_resolution)

i = 1

# allow the camera to warmup
time.sleep(0.1)
cv2.namedWindow("Frame")
cv2.setMouseCallback("Frame", capture_image)

start_time = time.time()


# capture frames from the camera
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    # grab the raw NumPy array representing the image, then initialize the timestamp
    # and occupied/unoccupied text
    image = frame.array
    if if_writing:
        if not if_opened_done:
            timestr = time.strftime("%Y%m%d_%H%M%S")
            out = cv2.VideoWriter('video_' + timestr + '.mp4', cv2.VideoWriter_fourcc('M','J','P','G'), 10, camera_resolution)
            if_opened_done = True
            if_closed_done = False
            print("WRITING")
        out.write(image)
    else:
        if not if_closed_done:
            out.release()
            print("SAVED")
            if_closed_done = True
            if_opened_done = False

    image_show = image.copy()
    cv2.line(image_show, (0, 378), (630, 378), (0, 0, 255), 2)
    cv2.line(image_show, (630, 378), (376, 234), (0, 0, 255), 2)
    cv2.line(image_show, (376, 234), (264, 234), (0, 0, 255), 2)
    cv2.line(image_show, (264, 234), (0, 378), (0, 0, 255), 2)

    image_show = cv2.resize(image_show, (360, 240))

    # show the frame
    # cv2.line(image_show, (180, 0), (180, 239), (0, 0, 255), 2)
    cv2.imshow("Frame", image_show)
    key = cv2.waitKey(1) & 0xFF

    # clear the stream in preparation for the next frame
    rawCapture.truncate(0)

    # if the `q` key was pressed, break from the loop
    if key == ord("q"):
        cv2.destroyAllWindows()
        break
    #
    # if time.time() - start_time >= 3:
    #     print("saving")
    #     cv2.imwrite("cam-calibration-images/calib" + str(i) + ".png", image)
    #     i += 1
    #     start_time = time.time()
    # if i > 25:
    #     cv2.destroyAllWindows()
    #     break


