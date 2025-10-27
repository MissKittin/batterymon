import time
import os
from . import batterymon_common

if os.getenv("BATTERYMON_DEBUG", "").lower() == "true":
    def print_debug(str):
        print(str)
else:
    def print_debug(str):
        return

def led(on):
    if on:
        if not os.path.exists(batterymon_common.GPIO_LED_IND):
            open(batterymon_common.GPIO_LED_IND, "w").close()

        print_debug("LED-ON")

        return

    if os.path.exists(batterymon_common.GPIO_LED_IND):
        os.remove(batterymon_common.GPIO_LED_IND)

    print_debug("LED-OFF")

def led_err(blink_count=5):
    blink_sleep=3/blink_count/2 # 0.6 second per blink

    for _ in range(blink_count):
        time.sleep(blink_sleep)
        print_debug("LED-ERR-ON")
        time.sleep(blink_sleep)
        print_debug("LED-ERR-OFF")
        time.sleep(blink_sleep)

def led_b(on):
    if on:
        if not os.path.exists(batterymon_common.GPIO_LED_B_IND):
            open(batterymon_common.GPIO_LED_B_IND, "w").close()

        print_debug("LEDB-ON")

        return

    if os.path.exists(batterymon_common.GPIO_LED_B_IND):
        os.remove(batterymon_common.GPIO_LED_B_IND)

    print_debug("LEDB-OFF")

def butt():
    if os.path.exists(batterymon_common.GPIO_BUTT_SW):
        print_debug("BUTT-ON")
        os.remove(batterymon_common.GPIO_BUTT_SW)

        return True

    return False

# init
if os.path.exists(batterymon_common.GPIO_LED_IND):
    os.remove(batterymon_common.GPIO_LED_IND)
if os.path.exists(batterymon_common.GPIO_LED_B_IND):
    os.remove(batterymon_common.GPIO_LED_B_IND)
if os.path.exists(batterymon_common.GPIO_BUTT_SW):
    os.remove(batterymon_common.GPIO_BUTT_SW)
