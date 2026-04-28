#!/usr/bin/env python3

import time
import os
import sys
import signal
from datetime import datetime
from lib import batterymon_helpers

def write_log(message, error=False):
    file=batterymon_common.ARCH_LOG

    if error:
        file=batterymon_common.ARCH_ERR

    with open(file, "a") as f:
        f.write(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+" "+message+"\n")

batterymon_common=batterymon_helpers.common()
batterymon_gpio=batterymon_helpers.gpio(lambda: write_log("Warning: The batterymon_gpio_dummy driver is used!", True))

if os.getenv("BATTERYMON_DEBUG", "").lower() == "true":
    def print_debug(c):
        sys.stdout.write(c)
        sys.stdout.flush()
else:
    def print_debug(c):
        return

def archive_file(type):
    global arch_retry

    if batterymon_common.block_archive(type):
        write_log("Archiving is blocked - batterymon_common.block_archive() returned True", True)
        batterymon_gpio.led_err()
        print_debug("B")

        if type != "Manual":
            arch_retry=True

        return

    batterymon_gpio.led(True)
    time.sleep(1)

    if not os.path.exists(batterymon_common.CURRENT_OUT):
        write_log(type+" archive: "+batterymon_common.CURRENT_OUT+" does not exist", True)
        print_debug("e")
        time.sleep(1)
        batterymon_gpio.led(False)

        return

    if os.path.getsize(batterymon_common.CURRENT_OUT) == 0:
        write_log(type+" archive: "+batterymon_common.CURRENT_OUT+" is empty", True)
        print_debug("m")
        time.sleep(1)
        batterymon_gpio.led(False)

        return

    if batterymon_common.mount_arch() != 0:
        batterymon_common.umount_arch()
        write_log("Cannot mount archive disk", True)
        batterymon_gpio.led(False)
        batterymon_gpio.led_err(10)
        print_debug("E")

        if type != "Manual":
            arch_retry=True

        return

    write_log(type+" archive")

    if type == "Manual":
        print_debug("!")
    elif type == "Triggered":
        print_debug("T")
    elif type == "Retry":
        print_debug("R")
    else:
        print_debug(".")

    # LOCK START
    open(batterymon_common.LOCK_FILE, "w").close()

    moved_file_path=batterymon_common.ARCH_JOURNAL_DIR+"/"+datetime.today().strftime("%Y-%m-%d_%H-%M-%S")+current_out_extension+".gz"

    moved_file_checksum=batterymon_helpers.gzip_file_move(
        batterymon_common.CURRENT_OUT,
        moved_file_path
    )

    if os.path.exists(batterymon_common.LOCK_FILE):
        os.remove(batterymon_common.LOCK_FILE)
    # LOCK END

    if moved_file_checksum is False:
        write_log("Cannot archive log ("+moved_file_path+")")

    if batterymon_common.ARCH_GENERATE_CHECKSUM:
        with open(moved_file_path+".sha512", "w") as f_checksum:
            f_checksum.write(moved_file_checksum)

    # compress ARCH_LOG
    batterymon_helpers.gzip_file_if_big(batterymon_common.ARCH_DIR+"/"+arch_log_basename)

    # append and compress rotated ARCH_ERR
    batterymon_helpers.merge_file(
        batterymon_common.ARCH_ERR,
        batterymon_common.ARCH_LOG_DIR+"/"+arch_err_basename
    )
    batterymon_helpers.gzip_file_if_big(batterymon_common.ARCH_LOG_DIR+"/"+arch_err_basename)

    if batterymon_common.umount_arch() != 0:
        write_log("Cannot umount archive disk", True)
        batterymon_gpio.led(False)
        batterymon_gpio.led_err(3)
        print_debug("X")

        return

    time.sleep(1)
    batterymon_gpio.led(False)

def cleanup(signum, frame):
    print("\nSignal "+str(signum)+", exiting with error")

    if os.path.exists(batterymon_common.LOCK_FILE):
        os.remove(batterymon_common.LOCK_FILE)
        print(batterymon_common.LOCK_FILE+" removed")

    print("Exiting with error")
    sys.exit(1)

def main():
    global arch_retry

    while not os.path.exists(batterymon_common.WORK_DIR):
        time.sleep(1)

    if os.path.exists(batterymon_common.LOCK_FILE):
        os.remove(batterymon_common.LOCK_FILE)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    last_archive_time=time.time()
    while True:
        now=time.time()

        if batterymon_gpio.butt():
            archive_file("Manual")
            last_archive_time=now
            time.sleep(1)

            continue

        if batterymon_common.arch_trigger(last_archive_time, now):
            archive_file("Triggered")
            last_archive_time=now
            time.sleep(1)

            continue

        if arch_retry:
            time.sleep(60)
            arch_retry=False
            archive_file("Retry")
            last_archive_time=now
            time.sleep(1)

            continue

        if now-last_archive_time >= batterymon_common.AUTOARCHIVE_SECONDS:
            archive_file("Automatic")
            last_archive_time=now
            time.sleep(1)

        time.sleep(2)

# init
current_out_extension=os.path.splitext(batterymon_common.CURRENT_OUT)[1] # archive_file()
arch_log_basename=os.path.basename(batterymon_common.ARCH_LOG)
arch_err_basename=os.path.basename(batterymon_common.ARCH_ERR)
arch_retry=False
main()
