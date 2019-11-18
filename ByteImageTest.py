


with open("snap2.png", "rb") as image:
    f = image.read()
    b = bytearray(f)
    print(b[0], b[1], b[2])

