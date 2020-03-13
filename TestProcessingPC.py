import cv2
import time
from LaneDetection import LaneDetection

cap = cv2.VideoCapture('./test-videos/motorway-tests/captures/video_1.mp4')
if not cap.isOpened():
    print("Error opening file")
time.sleep(1)

lka = LaneDetection()

while cap.isOpened():
    ret, frame = cap.read()
    if ret:
        out_frame, _, _ = lka.process(frame)
        cv2.imshow("out", out_frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break
    else:
        break

cv2.destroyAllWindows()