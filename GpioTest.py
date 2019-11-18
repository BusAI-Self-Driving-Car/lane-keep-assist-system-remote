import RPi.GPIO as GPIO
import time

contrPin = 33

GPIO.setmode(GPIO.BOARD)

GPIO.setup(contrPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

try:
    while True:
        state = GPIO.input(contrPin)
        if state:
            print("open")
        if state:
            print("closed")
        time.sleep(0.05)
finally:
    GPIO.cleanup()
