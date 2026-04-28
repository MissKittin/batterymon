# Dev note:
# all calls to batterymon_gpio_files
# must be implemented
# exactly as in this file

try:
    import RPi.GPIO as GPIO
except(ImportError):
    raise ImportError(
        "RPi.GPIO not available - use batterymon_gpio_dummy instead"
    )

import time
from . import batterymon_common
from . import batterymon_gpio_files

# function for operating LED A
# on [boolean] -> if true - turn on the LED, if false - turn off the LED
def led(on):
    batterymon_gpio_files.led(on)

    if on:
        if batterymon_common.GPIO_LED is None:
            return

        return GPIO.output(
            batterymon_common.GPIO_LED,
            GPIO.HIGH
        )

    if batterymon_common.GPIO_LED is None:
        return

    GPIO.output(
        batterymon_common.GPIO_LED,
        GPIO.LOW
    )

# function to operate LED A in case of an error (flashing)
# blink_count [int] -> how many times should the LED flash
def led_err(blink_count=5):
    if batterymon_common.GPIO_LED is None:
        return

    blink_sleep=3/blink_count/2 # 0.6 second per blink

    for _ in range(blink_count):
        time.sleep(blink_sleep)
        GPIO.output(
            batterymon_common.GPIO_LED,
            GPIO.HIGH
        )
        time.sleep(blink_sleep)
        GPIO.output(
            batterymon_common.GPIO_LED,
            GPIO.LOW
        )
        time.sleep(blink_sleep)

# function for operating LED B
# on [boolean] -> if true - turn on the LED, if false - turn off the LED
def led_b(on):
    batterymon_gpio_files.led_b(on)

    if on:
        if batterymon_common.GPIO_LED_B is None:
            return

        return GPIO.output(
            batterymon_common.GPIO_LED_B,
            GPIO.HIGH
        )

    if batterymon_common.GPIO_LED_B is None:
        return

    GPIO.output(
        batterymon_common.GPIO_LED_B,
        GPIO.LOW
    )

# function that checks whether the GPIO button
# or the software button is pressed
def butt():
    if batterymon_gpio_files.butt():
        return True

    if batterymon_common.GPIO_BUTT is None:
        return False

    return GPIO.input(batterymon_common.GPIO_BUTT) == GPIO.LOW

# init
batterymon_gpio_files.setup()
GPIO.setmode(GPIO.BCM)

if not batterymon_common.GPIO_BUTT is None:
    GPIO.setup(batterymon_common.GPIO_BUTT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
if not batterymon_common.GPIO_LED is None:
    GPIO.setup(batterymon_common.GPIO_LED, GPIO.OUT)
    GPIO.output(batterymon_common.GPIO_LED, GPIO.LOW)
if not batterymon_common.GPIO_LED_B is None:
    GPIO.setup(batterymon_common.GPIO_LED_B, GPIO.OUT)
    GPIO.output(batterymon_common.GPIO_LED_B, GPIO.LOW)
