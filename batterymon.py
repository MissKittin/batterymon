#!/usr/bin/env python3

import os
import shutil
import time
from datetime import datetime
from lib import batterymon_helpers

batterymon_common=batterymon_helpers.common()

def write_log(current_out, message):
    with open(current_out, "a") as f:
        f.write(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+" "+message+"\n")

if not os.path.exists(batterymon_common.WORK_DIR):
    os.makedirs(batterymon_common.WORK_DIR)
    os.chmod(batterymon_common.WORK_DIR, 0o1771)

while True:
    current_out=batterymon_common.CURRENT_OUT

    if os.path.exists(batterymon_common.LOCK_FILE):
        current_out=batterymon_common.BACKUP_OUT
    elif os.path.exists(batterymon_common.BACKUP_OUT):
        shutil.move(
            batterymon_common.BACKUP_OUT,
            current_out
        )

    if os.path.exists(batterymon_common.READ_LOCK_FILE):
        batterymon_common.on_read_lock()
        write_log(current_out, "RL")
        time.sleep(batterymon_common.SAVE_DATA_SECONDS)

        continue

    for device in batterymon_common.DEVICES:
        try:
            d, json_data=batterymon_common.get_bms_json_data(device)
            output_line="OK "+device

            if batterymon_common.DUMP_RAW_JSON:
                with open(batterymon_common.CURRENT_OUT+"-"+batterymon_helpers.sanitize_filename(device), "wb") as json_data_f:
                    json_data_f.write(json_data)

            for param in batterymon_common.LOG_PARAMS:
                if param in batterymon_common.LOG_PARAMS_IGNORE.get(device, []):
                    continue

                if param in batterymon_common.CUSTOM_LOG_PARAMS:
                    output_line+=" "+str(batterymon_common.CUSTOM_LOG_PARAMS[param](param, d.get(param, None)))
                    continue

                if isinstance(d.get(param, ""), list):
                    output_line+=" ["+" ".join(str(x) for x in d.get(param, []))+"]"
                    continue

                output_line+=" "+str(d.get(param, "-1"))

            write_log(current_out, output_line)
            batterymon_common.post_log(device, d)
        except(Exception) as e:
            write_log(current_out, ""
            +   "EX "+device+" "+str(e)
            )

    sleep_second=0
    while sleep_second < batterymon_common.SAVE_DATA_SECONDS:
        batterymon_common.on_sleep(sleep_second)
        sleep_second+=1
        time.sleep(1)
