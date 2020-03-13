from LaneDetection import LaneDetection
import cv2
import time

lka = LaneDetection()

img = cv2.imread("snap2.png")
start = time.time()
result = lka.process(img)
passed = time.time() - start
print(passed)

cv2.imwrite("result.png", result)

