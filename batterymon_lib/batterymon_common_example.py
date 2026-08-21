import subprocess
import os
import json
import sys
import time
import shutil

from . import batterymon_helpers

# settings - CUSTOM_LOG_PARAMS
def _custom_log_params(name, value):
    # this is a function for CUSTOM_LOG_PARAMS
    # it allows you to add external values to the log
    # e.g. from a thermometer, and log the ambient temperature
    # the name argument is the name of the parameter
    # and the value is the value of the parameter
    # read from get_bms_json_data or None (you can create wrapper functions)
    # this function must return some value so that batterymon.py writes it to the log

    #if name == "ExternalTemperature":
    #    return 25

    #if name == "Voltage": # wrapper functions
    #    return value*100

    return "_custom_log_params_NA_"

# settings
GET_BMS_JSON_DATA_MULTIPROCESS=False # start reading parameters of all devices in parallel (at the same time), batterymon.py
SAVE_DATA_SECONDS=30 # read data every 30 seconds, batterymon.py
AUTOARCHIVE_SECONDS=86400 # archive data every 24 hours, batterymon-arch.py
ARCH_GENERATE_CHECKSUM=True # save sha512 checksum in .sha512 file next to archived file, batterymon-arch.py
GPIO_DRIVER="rpi" # rpi or dummy, you can add your drivers (batterymon_gpio_drv_* and batterymon_gpio_drv_*.py), this file and batterymon-arch.py
GPIO_BUTT=17 # "archive" button, disabled if None, batterymon_gpio_rpi.py
GPIO_LED=27 # "archiving in progress" light, disabled if None, batterymon_gpio_rpi.py
GPIO_LED_B=23 # "attention required" light, disabled if None, batterymon_gpio_rpi.py
ARCH_MNT=os.path.realpath("/media/batterymon") # defined in /etc/fstab
ARCH_MNT_BACKUP=os.path.realpath("/media/batterymon-backup") # backup disk, defined in /etc/fstab, disabled if None, _do_rsync()
ARCH_DIR=ARCH_MNT+"/batterymon" # directory for the program on the disk containing the archive
ARCH_JOURNAL_DIR=ARCH_DIR+"/journal" # directory for rotated CURRENT_OUT
ARCH_LOG_DIR=ARCH_DIR+"/logs" # directory for rotated ARCH_LOG, ARCH_ERR and FSCK_LOG
ARCH_LOG_MAX_SIZE=31457280 # 30MB; ARCH_LOG, FSCK_LOG and ARCH_ERR in ARCH_LOG_DIR; batterymon_helpers.gzip_file_if_big()
DEVICES=[ # batterymon.py
    # define your BMS addresses here
    #"bt:00:11:22:33:44:55",
    #"bt:01:23:45:67:89:AB"
]
LOG_PARAMS=[ # batterymon.py
    # define here what parameters from jbdtool you want to write to the log

    "Voltage",
    "Current",
    "RemainingCapacity",
    "PercentCapacity",
    "CycleCount",
    "Temps", # arr
    "Cells", # arr
    "Balance", # string of 0 and 1
    "CellTotal",
    "CellMin",
    "CellMax",
    "CellDiff",
    "CellAvg",
    "FET",
    #"ExternalTemperature" # custom log param (can be anywhere in the array)
]
LOG_PARAMS_IGNORE={ # batterymon.py
    # if you do not want to log some parameters
    # from LOG_PARAMS for specific devices, add them here

    #"bt:01:23:45:67:89:AB": ["Temps", "Balance"]
}
CUSTOM_LOG_PARAMS={ # batterymon.py
    # here you define callbacks for external parameters
    # it's important that the dict value is callable

    #"Voltage": _custom_log_params, # wrapper functions
    #"ExternalTemperature": _custom_log_params
}

# internal settings
WORK_DIR="/tmp/.batterymon"
CURRENT_OUT=WORK_DIR+"/pending.txt"
BACKUP_OUT=WORK_DIR+"/pending-tmp.txt" # batterymon.py, writes to this file during log rotation
DUMP_RAW_JSON=False # batterymon.py, dumps the read json to CURRENT_OUT+"-"+device
DUMP_RAW_JSON_IGNORE=[ # batterymon.py
    # define the devices for which the DUMP_RAW_JSON option should be set to False
    # applies when DUMP_RAW_JSON is True

    #"bt:01:23:45:67:89:AB"
]
LOCK_FILE=WORK_DIR+"/arch.lock" # created by batterymon-arch.py
READ_LOCK_FILE=WORK_DIR+"/bmsread.lock" # if you create this file, you will block reading data from BMS in batterymon.py
ARCH_LOG=WORK_DIR+"/arch-log.txt" # batterymon-arch.py
ARCH_ERR=WORK_DIR+"/arch-err.txt" # batterymon-arch.py
FSCK_LOG=WORK_DIR+"/fsck.log" # batterymon-fsck.py
GPIO_LED_IND=WORK_DIR+"/GPIO_LED_ON" # gpio drivers
GPIO_LED_B_IND=WORK_DIR+"/GPIO_LED_B_ON" # gpio drivers
GPIO_BUTT_SW=WORK_DIR+"/GPIO_BUTT_ON" # gpio drivers

# settings - helpers
def _do_rsync(): # umount_arch()
    if ARCH_MNT_BACKUP is None:
        return

    os.sync()

    # batterymon-fsck.py
    process=subprocess.Popen(["sudo", os.path.dirname(os.path.realpath(sys.argv[0]))+"/batterymon-fsck.py", ARCH_MNT_BACKUP])
    if process.wait() > 2:
        return 1

    process=subprocess.Popen(["mount", ARCH_MNT_BACKUP])
    if process.wait() != 0:
        return 1

    subprocess.run(["rsync", "-a", "--delete", "--ignore-existing", ARCH_MNT+"/", ARCH_MNT_BACKUP])

    process=subprocess.Popen(["umount", ARCH_MNT_BACKUP])

    return process.wait()

# settings - functions
def get_bms_json_data(device): # batterymon.py
    # define how to read data from BMS

    json_data=b"<no data>"

    try:
        json_data=subprocess.check_output(
            [
                os.path.dirname(os.path.realpath(sys.argv[0]))+"/jbdtool/jbdtool",
                "-t", device,
                "-j"
            ],
            stderr=subprocess.STDOUT
        )

        return(
            json.loads(json_data.decode("utf-8")),
            json_data
        )
    except(subprocess.CalledProcessError) as e:
        raise Exception("CPE "+str(e))
    except(json.JSONDecodeError) as e:
        raise Exception(""
        +   "JDE "+str(e)+" | "
        +   json_data.decode("utf-8", errors="replace").strip()
        )
    except(UnicodeDecodeError) as e:
        raise Exception(""
        +   "UDE "+str(e)+" | "
        +   repr(json_data)
        )
    except(ValueError) as e:
        raise Exception(""
        +   "VE "+str(e)+" | "
        +   json_data.strip()
        )

def on_read_lock(): # batterymon.py
    # do something if you block reading data from BMS
    pass

def log_start(): # batterymon.py
    # execute before starting a series of readings (before all pre_log)
    pass

def pre_log(device, data): # batterymon.py
    # execute after reading data from BMS and before writing to the log
    # this function will not be run if get_bms_json_data throws an exception
    pass

def post_log(device, data): # batterymon.py
    # execute after writing data to the log (light up the GPIO_LED_B)
    # this function will not be run if get_bms_json_data throws an exception

    batterymon_gpio=batterymon_helpers.gpio()
    cell_diff=data.get("CellDiff", 0)

    if not cell_diff:
        return

    if device == DEVICES[0]:
        batterymon_gpio.led_b(False)

    if cell_diff >= 0.05:
        batterymon_gpio.led_b(True)

def log_finish(): # batterymon.py
    # execute after completing a series of readings (after all post_log)
    pass

def on_sleep(sleep_second): # batterymon.py
    # this function is run every second for SAVE_DATA_SECONDS times after data is saved (sleep with callback)
    # the sleep_second argument is the current sleep second (seconds are counted from 0)

    pass

def arch_trigger(last_archive_time, now_time): # batterymon-arch.py
    # automatically start archiving when an event occurs
    # (returns True if archiving is to be invoked)

    return False

def block_archive(archive_type): # batterymon-arch.py
    # block archiving (returns True if archiving is to be canceled)
    # archive_type: Manual, Triggered, Retry or Automatic

    return False

def mount_arch(): # batterymon-arch.py
    # a function that mounts the disk containing the archive

    batterymon_gpio=batterymon_helpers.gpio()

    while True:
        process=subprocess.Popen(["mountpoint", "-q", ARCH_MNT])

        if process.wait() != 0:
            break

        if os.getenv("BATTERYMON_DEBUG", "").lower() == "true":
            print("mount_arch mountpoint wait")

        time.sleep(10)

    # batterymon-fsck.py
    batterymon_gpio.led_b(False)
    open(FSCK_LOG, "w").close()
    process=subprocess.Popen(["sudo", os.path.dirname(os.path.realpath(sys.argv[0]))+"/batterymon-fsck.py"])
    if process.wait() > 2: # EMERGENCY!!!
        batterymon_gpio.led_b(True)
        return 1

    process=subprocess.Popen(["mount", ARCH_MNT])
    if process.wait() != 0:
        return 1

    # reject mounting if disk is full
    if shutil.disk_usage(ARCH_MNT).free < 5242880: # 5MB
        umount_arch(False)
        return 1

    if not os.path.exists(ARCH_DIR):
        os.makedirs(ARCH_DIR)
    if not os.path.exists(ARCH_JOURNAL_DIR):
        os.makedirs(ARCH_JOURNAL_DIR)
    if not os.path.exists(ARCH_LOG_DIR):
        os.makedirs(ARCH_LOG_DIR)

    return 0

def umount_arch(do_rsync=True): # batterymon-arch.py
    # a function that unmounts the disk containing the archive

    process=subprocess.Popen(["mountpoint", "-q", ARCH_MNT])
    if process.wait() != 0:
        return 0

    if do_rsync:
        _do_rsync()

    # batterymon-fsck.py
    if do_rsync:
        fsck_log_basename=os.path.basename(FSCK_LOG)

        batterymon_helpers.merge_file(
            FSCK_LOG,
            ARCH_LOG_DIR+"/"+fsck_log_basename
        )

        batterymon_helpers.gzip_file_if_big(ARCH_LOG_DIR+"/"+fsck_log_basename)

    os.sync()

    for i in range(300):
        process=subprocess.Popen(["umount", ARCH_MNT])
        process_result=process.wait()

        if process_result == 0:
            return 0

        time.sleep(1)

    return process_result
