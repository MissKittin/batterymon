# Dev note:
# all calls to batterymon_gpio_files
# must be implemented
# exactly as in this file

import time
import os
from . import batterymon_common
from . import batterymon_gpio_files

if os.getenv("BATTERYMON_GPIO_DRV_DUMMY_DEBUG", "").lower() == "true":
    def print_debug(str):
        print(str)
else:
    def print_debug(str):
        return

# function for operating LED A
# on [boolean] -> if true - turn on the LED, if false - turn off the LED
def led(on):
    batterymon_gpio_files.led(on)

    if on:
        print_debug("LED-ON")
        return

    print_debug("LED-OFF")

# function to operate LED A in case of an error (flashing)
# blink_count [int] -> how many times should the LED flash
def led_err(blink_count=5):
    blink_sleep=3/blink_count/2 # 0.6 second per blink

    for _ in range(blink_count):
        time.sleep(blink_sleep)
        print_debug("LED-ERR-ON")
        time.sleep(blink_sleep)
        print_debug("LED-ERR-OFF")
        time.sleep(blink_sleep)

# function for operating LED B
# on [boolean] -> if true - turn on the LED, if false - turn off the LED
def led_b(on):
    batterymon_gpio_files.led_b(on)

    if on:
        print_debug("LEDB-ON")
        return

    print_debug("LEDB-OFF")

# function that checks whether the GPIO button
# or the software button is pressed
def butt():
    if batterymon_gpio_files.butt():
        print_debug("BUTT-ON")
        return True

    return False

# init
batterymon_gpio_files.setup()
