import os
from . import batterymon_common

def is_led_on():
    if os.path.exists(batterymon_common.GPIO_LED_IND):
        return True

    return False

def is_led_b_on():
    if os.path.exists(batterymon_common.GPIO_LED_B_IND):
        return True

    return False

def is_butt_pressed():
    if os.path.exists(batterymon_common.GPIO_BUTT_SW):
        return True

    return False

def led(on):
    if on:
        open(batterymon_common.GPIO_LED_IND, "w").close()
        return

    if is_led_on():
        os.remove(batterymon_common.GPIO_LED_IND)


def led_b(on):
    if on:
        open(batterymon_common.GPIO_LED_B_IND, "w").close()
        return

    if is_led_b_on():
        os.remove(batterymon_common.GPIO_LED_B_IND)

def butt():
    if is_butt_pressed():
        os.remove(batterymon_common.GPIO_BUTT_SW)
        return True

    return False

def butt_press(chmod=True):
    open(batterymon_common.GPIO_BUTT_SW, "w").close()

    if chmod:
        os.chmod(batterymon_common.GPIO_BUTT_SW, 0o660)

# warning: this function is only for batterymon_gpio_drv_*
# never use it except in this one place
def setup():
    for path in (
        batterymon_common.GPIO_LED_IND,
        batterymon_common.GPIO_LED_B_IND,
        batterymon_common.GPIO_BUTT_SW
    ):
        if os.path.exists(path):
            os.remove(path)
