# BatteryMon
Collect data from your off-grid PV  
Tested on Raspberry Pi Zero W and AZO Digital LP12-150 LiFePO4 12V 150Ah

### Hardware requirements
* Raspberry Pi  
	or other computer, GPIO is optional
* SD card for OS
* thumb drive or SD card for collected data  
	two pieces if you want to have backup via `rsync`
* 2x LED, 2 resistors  
	requires GPIO
* button  
	requires GPIO

### Software requirements
* compiled jbdtool
* python 3
* sudo
* bluez  
	if you use Bluetooth
* rsync  
	if you want to have backup

### Optional components
* `RPi.GPIO` package  
	LEDs and button, for `rpi` GPIO driver

### OS configuration
* `batterymon` user and group
* user `batterymon` added to appropriate groups
* an `/etc/fstab` entry that allows `batterymon` to mount `/media/batterymon`  
	and `/media/batterymon-backup` if you want to have backup
* entry in `/etc/sudoers` allowing `batterymon-fsck.py` with the `NOPASSWD` option

### Setup
Open the `batterymon_lib` directory. You can configure the program in two ways:  
you can patch the `batterymon_common_example.py` - you gain the ability to update the code that you will not edit.  
Create a file `batterymon_common.py` and enter the settings you want to change into it, e.g.:
```
# import sample configuration
from .batterymon_common_example import *

# settings - your own CUSTOM_LOG_PARAMS
def _custom_log_params(name, value):
    if name == "ExternalTemperature":
        return 22

    return "_custom_log_params_NA_"

# enter your own settings
DEVICES=[
    "bt:00:11:22:33:44:55",
    "bt:01:23:45:67:89:AB"
]
LOG_PARAMS_IGNORE={}
CUSTOM_LOG_PARAMS={
    "ExternalTemperature": _custom_log_params
}

# overwrite function
def on_read_lock():
	# do something

# wrap function
_original_umount_arch=umount_arch
def umount_arch(do_rsync=True):
    process_result=_original_umount_arch(do_rsync)

    if process_result == 0:
        # do something if unmounting was successful

    return process_result

# replace internal function
def _do_rsync():
    from . import batterymon_common_example as _example

    def _do_rsync():
        # function body

    _example._do_rsync=_do_rsync
_do_rsync()
```
or method 2: rename `batterymon_common_example.py` to `batterymon_common.py` and edit this file.

Create user `batterymon`:
```
useradd --no-create-home --shell /usr/sbin/nologin batterymon && passwd -l batterymon
```

Add the `batterymon` user to the appropriate groups:
```
usermod -aG bluetooth batterymon # if jbdtool works without adding to groups, skip this step
usermod -aG gpio batterymon
```

Now run `ls -la /dev/disk/by-uuid` and copy the UUIDs of the drives that are intended for data storage (UUIDs are more predictable than `/dev/sdXY`).  
Create directories `/media/batterymon` and `/media/batterymon-backup`, set the group `batterymon` for them (`chown root:batterymon /media/batterymon; chown root:batterymon /media/batterymon-backup`) and add to `/etc/fstab` (example for FAT32 - if you want to use EXT4, remove the `fmask` and `dmask` options):
```
UUID=0123-ABCD /media/batterymon vfat noauto,user,nosuid,nodev,noexec,noatime,nodiratime,async,fmask=133,dmask=022 0 0
UUID=0011-22BB /media/batterymon-backup vfat noauto,user,nosuid,nodev,noexec,noatime,nodiratime,async,fmask=133,dmask=022 0 0
```
**Note:** always set the pass option (last) to `0`.

Link the ready sudo config from the repository (must be in `/usr/local/share/batterymon`):
```
chmod 440 /usr/local/share/batterymon/sudoers.d/batterymon
ln -s /usr/local/share/batterymon/sudoers.d/batterymon /etc/sudoers.d/batterymon
```
or add this entry to `/etc/sudoers.d/batterymon` (where the repository is located in `/usr/local/share/batterymon`):
```
batterymon ALL=(ALL) !ALL
batterymon ALL=NOPASSWD: /usr/local/share/batterymon/batterymon-fsck.py
```

Install systemd units or sysvinit scripts.  

If you use Bluetooth, add BMS to your device list:
```
bluetoothctl --timeout=10 scan on

bluetoothctl connect 00:11:22:33:44:55
bluetoothctl trust 00:11:22:33:44:55

bluetoothctl connect 01:23:45:67:89:AB
bluetoothctl trust 01:23:45:67:89:AB
```
where the first command will print the MAC addresses of found devices (e.g. `[CHG] Device 00:11:22:33:44:55 RSSI: -37`)  
and `01:23:45:67:89:AB` and `01:23:45:67:89:AB` are the MAC addresses of the BMSes.

### How to compile jbdtool
Tested on Raspbian Bookworm  
**Note:** clone this repository with the `--recursive` option
```
cd jbdtool
apt-get update
apt-get install build-essential libglib2.0-dev libpaho-mqtt-dev
apt-get clean
make
strip jbdtool
```

### How it works
`batterymon.py` reads JSON data from `jbdtool` (data from your BMSes) and writes it to a log in `/tmp/.batterymon/pending.txt`.  
`batterymon-arch.py` periodically transfers data to external storage: mounts the disk, moves the log file and compresses it.  
While the log is being transferred, the LED connected to GPIO lights up (it flashes when an error occurs), and the button is used to manually start the data archiving process.  
When transferring a file, a SHA512 checksum is generated - you can check whether the archived log is corrupted or not. You can change this by setting the `ARCH_GENERATE_CHECKSUM` variable to `False` in `batterymon_common.py`.  
Additionally, if one of the batteries requires attention (e.g. the cells need to be balanced) or there is a problem with the external disk, a second LED will light up.  
External memory is designed to protect data from loss due to power outages. Therefore, current data is stored in tmpfs, and the memory containing the operating system is mounted in read-only mode.  
Therefore, there's no need to turn off the system. Simply unplug the cable (or turn off the DC-AC inverter unless the LED is on - then wait until it turns off).  
**Note:** automatic archiving will not be activated if any BMS reports a voltage lower than 12V (you can change this in the settings).  
You can also add a second drive - it will serve as a backup in case your primary drive fails. This option is enabled by default – set `ARCH_MNT_BACKUP` to `None` to disable this feature.  
`batterymon-fsck.py` is run from `batterymon-arch.py` via `sudo` - the filesystem is checked before each external storage mount.  
In this configuration, you can also check if the AC side is working by pinging the SBC. If it doesn't respond, the inverter is off (you've used up all the battery power, the battery fuse has blown or the inverter is burned out).

### Virtual devices
You can define virtual devices, i.e. devices whose data is read by BatteryMon but is not written to the main log.  
It works like this: in the `batterymon_common.py`, the `LOG_PARAMS_IGNORE[virtual_device_name]` list is the same as the `LOG_PARAMS` list:
```
from datetime import datetime

LOG_PARAMS=[
    "Voltage",
    "Current",
    "RemainingCapacity",
    "PercentCapacity",
    "CycleCount",
    "Temps",
    "Cells",
    "Balance",
    "CellTotal",
    "CellMin",
    "CellMax",
    "CellDiff",
    "CellAvg",
    "FET"
]
DEVICES=[
    "bt:00:11:22:33:44:55",
    "bt:01:23:45:67:89:AB",
    "vdev:name"
]
LOG_PARAMS_IGNORE={
    "vdev:name": LOG_PARAMS
}

def get_bms_json_data(device):
    if device.startswith("vdev:"):
        # return data from virtual device (remember to catch exceptions)
        try:
            return ({
                "paramA": "valueA",
                "paramB": "valueB"
            }, "string-for-dump-raw-json")
        except(Exception):
            return ({}, "")

    # continuation of the original code

def post_log(device, data):
    # save data to file here (remember to catch exceptions)
    try:
        with open("/tmp/vdev.log", "a") as log:
            try:
                output_line="OK "+device

                for param in ["paramA", "paramB"]:
                    output_line+=" "+str(
                        data.get(param, "-1")
                    )

                log.write(datetime.today().strftime("%Y-%m-%d %H:%M:%S")
                +   " "+output_line+"\n"
                )
            except(Exception) as e:
                log.write(datetime.today().strftime("%Y-%m-%d %H:%M:%S")
                +   " EX "+device+" "+str(e).replace("\n", "\\n")+"\n"
                )
    except(Exception):
        pass

# you can optionally exclude the device from the DUMP_RAW_JSON function
DUMP_RAW_JSON_IGNORE=["vdev:name"]
```

### Scripts
`batterymon.py` - reads data from the BMS and writes it to the log  
`batterymon-arch.py` - archives the log to an external disk  
`batterymon-fsck.py` - a helper that allows you to check the external disk before mounting

### GPIO drivers
* `rpi` - driver for Raspberry Pi
* `dummy` - fallback (debug) driver

When the LED indicating archiving is lit, the file `/tmp/.batterymon/GPIO_LED_ON` will be created.  
When the LED indicating the need for intervention is lit, the file `/tmp/.batterymon/GPIO_LED_B_ON` will be created.  
You can also programmatically press the GPIO button by creating an empty `/tmp/.batterymon/GPIO_BUTT_ON` file.  
If you want to write your own driver, use the code of the above drivers as a reference code.  
The project provides an interface for easy interaction - see the functions in the `batterymon_lib/batterymon_gpio_files.py` library.

### Log format
The format of the `/tmp/.batterymon/pending.txt` file looks like this:
```
YYYY-mm-dd HH:MM:SS OK bt:device-mac,desc data read in order from the LOG_PARAMS table
YYYY-mm-dd HH:MM:SS EX bt:device-mac,desc Exception message
YYYY-mm-dd HH:MM:SS RL
```
where `RL` means "reading locked".

#### Log parsing
The project provides log parsing functions so that you don't have to waste time on it.  
You can parse the log into a list or into a dict. The `log_line_dict` function gives you a good starting point.  
**Warning:** the `parse_log_line` function is a dumb parser - the exception message can be split.  
This is what sample code that handles parsing looks like:
```
from collections import deque

sys.path.insert(1, "/usr/local/share/batterymon")

from batterymon_lib import batterymon_helpers
from batterymon_lib import batterymon_helpers_extra
batterymon_common=batterymon_helpers.common()

# get log path
current_out=batterymon_helpers_extra.get_current_out_path(
    batterymon_common
)

# get as many lines from the log as there are defined devices
# note: if you need a list of devices, use batterymon_helpers_extra.get_log_devices(batterymon_common)
with open(current_out, "r") as f:
    logs=list(deque(
        f,
        maxlen=batterymon_helpers_extra.get_log_devices_len(batterymon_common)
	))
    
for log_line in logs:
    parsed_log_line=batterymon_helpers.parse_log_line(log_line)
    # you will get a list of strings like ["2026-04-24", "15:50:00", "OK", "bt:00:11:22:33:44:55", "13.3333", "1.034", ["3.23", "3.24", "3.23"] ...]

    dict_log_line=batterymon_helpers_extra.log_line_dict(
        parsed_log_line,
        batterymon_common
    )
    # you will get a string dict like {"_bm_date": "2026-04-24", "_bm_time": "15:50:00", "_bm_status": "OK", "_bm_device": "bt:00:11:22:33:44:55", "Voltage": "13.3333", "Current": "1.034", "Cells": ["3.23", "3.24", "3.23"] ...}
```
The formats are better described in the files `batterymon_lib/batterymon_helpers_parse_log_line.py` and `batterymon_lib/batterymon_helpers_extra.py`.

### Debugging
For the `batterymon-arch.py` to work, create the directories `/tmp/batterymon-mnt`, `/tmp/batterymon-mnt-backup` and add to `/etc/fstab`:
```
/tmp/batterymon-mnt /media/batterymon auto user,bind 0 0
/tmp/batterymon-mnt-backup /media/batterymon-backup auto user,bind 0 0
```
