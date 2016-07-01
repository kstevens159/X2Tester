import RPi.GPIO as GPIO
import time

##Define GPIO Interface
GPIO.setmode(GPIO.BOARD) #Sets the pin mode to use the board's pin numbers
#Define the pin numbers in a dictionary to allow easy reference
pin = {"IO1"       :   11,
       "IO2"       :   13,
       "IO3"       :   15,
       "IO4"       :   12,
       "TRIGGER1"  :   16,
       "TRIGGER2"  :   18
       }
#Set the GPIO directions
GPIO.setup(pin["IO1"], GPIO.OUT)
GPIO.setup(pin["IO2"], GPIO.OUT)
GPIO.setup(pin["IO3"], GPIO.OUT)
GPIO.setup(pin["IO4"], GPIO.OUT)
GPIO.setup(pin["TRIGGER1"], GPIO.OUT)
GPIO.setup(pin["TRIGGER2"], GPIO.OUT)

try:
    while(True):
        print("Blink Off")
        GPIO.output(pin["IO1"],GPIO.HIGH)
        time.sleep(2)
        print("Blink On")
        GPIO.output(pin["IO1"],GPIO.LOW)
        time.sleep(2)
except KeyboardInterrupt:
    GPIO.cleanup()
    print("User cancelled by keyboard")
