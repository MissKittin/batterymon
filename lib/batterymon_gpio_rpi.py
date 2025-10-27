try:
    import RPi.GPIO as GPIO
except ImportError:
    raise ImportError(
        "RPi.GPIO not available - use batterymon_gpio_dummy instead"
    )

import time
import os
from . import batterymon_common

def led(on):
    if on:
        if not os.path.exists(batterymon_common.GPIO_LED_IND):
            open(batterymon_common.GPIO_LED_IND, "w").close()

        if batterymon_common.GPIO_LED is None:
            return

        return GPIO.output(batterymon_common.GPIO_LED, GPIO.HIGH)

    if os.path.exists(batterymon_common.GPIO_LED_IND):
        os.remove(batterymon_common.GPIO_LED_IND)

    if batterymon_common.GPIO_LED is None:
        return

    GPIO.output(batterymon_common.GPIO_LED, GPIO.LOW)

def led_err(blink_count=5):
    if batterymon_common.GPIO_LED is None:
        return

    blink_sleep=3/blink_count/2 # 0.6 second per blink

    for _ in range(blink_count):
        time.sleep(blink_sleep)
        GPIO.output(batterymon_common.GPIO_LED, GPIO.HIGH)
        time.sleep(blink_sleep)
        GPIO.output(batterymon_common.GPIO_LED, GPIO.LOW)
        time.sleep(blink_sleep)

def led_b(on):
    if on:
        if not os.path.exists(batterymon_common.GPIO_LED_B_IND):
            open(batterymon_common.GPIO_LED_B_IND, "w").close()

        if batterymon_common.GPIO_LED_B is None:
            return

        return GPIO.output(batterymon_common.GPIO_LED_B, GPIO.HIGH)

    if os.path.exists(batterymon_common.GPIO_LED_B_IND):
        os.remove(batterymon_common.GPIO_LED_B_IND)

    if batterymon_common.GPIO_LED_B is None:
        return

    GPIO.output(batterymon_common.GPIO_LED_B, GPIO.LOW)

def butt():
    if os.path.exists(batterymon_common.GPIO_BUTT_SW):
        os.remove(batterymon_common.GPIO_BUTT_SW)
        return True

    if batterymon_common.GPIO_BUTT is None:
        return False

    return GPIO.input(batterymon_common.GPIO_BUTT) == GPIO.LOW

# init
GPIO.setmode(GPIO.BCM)

if not batterymon_common.GPIO_BUTT is None:
    GPIO.setup(batterymon_common.GPIO_BUTT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
if not batterymon_common.GPIO_LED is None:
    GPIO.setup(batterymon_common.GPIO_LED, GPIO.OUT)
    GPIO.output(batterymon_common.GPIO_LED, GPIO.LOW)
if not batterymon_common.GPIO_LED_B is None:
    GPIO.setup(batterymon_common.GPIO_LED_B, GPIO.OUT)
    GPIO.output(batterymon_common.GPIO_LED_B, GPIO.LOW)

if os.path.exists(batterymon_common.GPIO_LED_IND):
    os.remove(batterymon_common.GPIO_LED_IND)
if os.path.exists(batterymon_common.GPIO_LED_B_IND):
    os.remove(batterymon_common.GPIO_LED_B_IND)
if os.path.exists(batterymon_common.GPIO_BUTT_SW):
    os.remove(batterymon_common.GPIO_BUTT_SW)
