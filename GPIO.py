#   GPIO library I hacked together to be able to use the BeagleBone Black in 2021.
#   Apparently, no one maintains libraries for the beaglebone anymore so there are no easy to use GPIO libs that I could find.
#
#   Author: Timo Birnschein
#   email: timo.birnschein@microforge.de

"""
This library uses os.access. According to https://docs.python.org/2/library/os.html#os.access this is not the preferred way to check if a file can be accessed.
It might pose a security risk. However, since we are talking about GPIOs and not actual data or text files, I prefer to not use exceptions.
"""

import os
import time
from time import sleep

GPIO_WAIT_TIME = 0.01
GPIO_TIMEOUT = 1

# Arduino-like function to set up a GPIO pin. Apparently, none of the old libraries work anymore
# like the Ardafruit GPIO libs. So I wrote my own really quick (research and trial and error)
def pinMode(gpioNumber, direction):
    # First we have to check if the directory for GPIO45 already exists
    # If not, ask 'export' to create it for us
    if os.path.isdir("/sys/class/gpio/gpio" + str(gpioNumber)) == False:
        gpio_export = open("/sys/class/gpio/export", "w")
        # gpio_export.seek(0)
        gpio_export.write(str(gpioNumber))
        gpio_export.flush()
        gpio_export.close()
    
    # Then, define the direction of the GPIO
    timeout = time.time()
    while os.path.isfile("/sys/class/gpio/gpio" + str(gpioNumber) + "/direction") == False:
        if time.time() - timeout > GPIO_TIMEOUT:
            print("GPIO direction file not created, yet:", str(gpioNumber))
            return -1
        sleep(GPIO_WAIT_TIME)
    
    timeout = time.time()
    while os.access("/sys/class/gpio/gpio" + str(gpioNumber) + "/direction", os.W_OK) == False:
        if time.time() - timeout > GPIO_TIMEOUT:
            print("GPIO direction file cannot be written, yet:", str(gpioNumber))
            return -1
        sleep(GPIO_WAIT_TIME)
        
    gpio_direction = open("/sys/class/gpio/gpio" + str(gpioNumber) + "/direction", "w")
    gpio_direction.seek(0)
    gpio_direction.write(direction)
    gpio_direction.close()
    
    timeout = time.time()
    while os.access("/sys/class/gpio/gpio" + str(gpioNumber) + "/value", os.W_OK) == False: 
        if time.time() - timeout > GPIO_TIMEOUT:
            print("GPIO direction file cannot be written, yet:", str(gpioNumber))
            return -1
        sleep(GPIO_WAIT_TIME)
        
    return open("/sys/class/gpio/gpio" + str(gpioNumber) + "/value", "r+")
    
# Python seems to ignore when a file is alreay open and just opens it again.
# All of these files will remain open until the program stops.
def digitalWrite(gpio, value):
    gpio.write(str(value))
    gpio.flush()
    
# Python seems to ignore when a file is alreay open and just opens it again.
# All of these files will remain open until the program stops.
def digitalRead(gpio):
    gpio.seek(0)
    value = gpio.read()
    return value
    
def pinCleanUp(gpioNumber):
    # First we have to check if the directory for GPIO45 already exists
    # If not, ask export to create it for us
    if os.path.isdir("/sys/class/gpio/gpio" + str(gpioNumber)) == True:
        gpio_unexport = open("/sys/class/gpio/unexport", "w")
        # gpio_export.seek(0)
        gpio_unexport.write(str(gpioNumber))
        gpio_unexport.close()
        