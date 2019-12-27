import cv2
from Camera import Camera

img = cv2.imread("snap2.png")

img_str = cv2.imencode(".png", img)

print(img_str[1])

b = bytearray(img_str[1])
print(b[0])

cam = Camera()
print(cam.get_perspective_src_points_to_str())

with open("snap2.png", "rb") as image:
    f = image.read()
    b = bytearray(f)
    print(b)

