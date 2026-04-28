#!/usr/bin/env python3

import subprocess
import sys
from datetime import datetime
from lib import batterymon_common

def fstab():
    fstab_entries={}

    with open("/etc/fstab", "r") as f:
        for line in f:
            line=line.strip()

            if not line or line.startswith("#"):
                continue

            parts=line.split()

            if len(parts) < 6:
                continue

            fstab_entries[parts[1]]={
                "device": parts[0],
                "fs_type": parts[2],
                "options": parts[3].split(","),
                "dump": int(parts[4]),
                "pass": int(parts[5])
            }

    return fstab_entries

def resolve_fstab_device(device):
    if device.startswith("LABEL="):
        return "/dev/disk/by-label/"+device[6:]

    if device.startswith("UUID="):
        return "/dev/disk/by-uuid/"+device[5:]

    if device.startswith("PARTLABEL="):
        return "/dev/disk/by-partlabel/"+device[10:]

    if device.startswith("PARTUUID="):
        return "/dev/disk/by-partuuid/"+device[9:]

    return device

def write_log(message, newline=True):
    with open(batterymon_common.FSCK_LOG, "a") as log_file:
        log_file.write(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+" "+message)

        if newline:
            log_file.write("\n")

        log_file.flush()

mountpoint=batterymon_common.ARCH_MNT

if len(sys.argv) > 1 and sys.argv[1] == batterymon_common.ARCH_MNT_BACKUP:
    mountpoint=batterymon_common.ARCH_MNT_BACKUP

try:
    write_log("=== FSCK START "+mountpoint+" ===")
    arch_dev=fstab().get(mountpoint)

    if not arch_dev:
        write_log("WRAPPER ERROR: "+mountpoint+" not found in /etc/fstab")
        sys.exit(4)

    if arch_dev["fs_type"] in {
        "tmpfs", "devtmpfs", "proc", "sysfs", "devpts",
        "overlay", "squashfs", "cgroup", "cgroup2",
        "pstore", "securityfs", "configfs", "debugfs",
        "tracefs", "fusectl", "mqueue", "hugetlbfs",
        "ramfs", "aufs", "selinuxfs", "binfmt_misc"
    }:
        write_log("WRAPPER: "+arch_dev["fs_type"]+" is not fsckable, ignoring")
        write_log("=== FSCK END ===")

        sys.exit(0)

    if "bind" in arch_dev["options"]: # debugging
        write_log("WRAPPER: bind mount detected, ignoring")
        write_log("=== FSCK END ===")

        sys.exit(0)

    process=subprocess.Popen(
        [
            "fsck",
            "-f", "-y", "-v",
            resolve_fstab_device(arch_dev["device"])
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    for line in process.stdout:
        write_log(line, False)

    write_log("=== FSCK END ===")
    sys.exit(process.wait())
except(Exception) as e:
    write_log("WRAPPER EXCEPTION: "+str(e))
    write_log("=== FSCK FAILED ===")

    sys.exit(8)
