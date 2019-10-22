import cv2
from Camera import Camera
from LaneKeepAssistSystem import LaneKeepAssistSystem


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