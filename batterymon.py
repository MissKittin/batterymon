#!/usr/bin/env python3

import os
import shutil
import time
from datetime import datetime
from batterymon_lib import batterymon_helpers

batterymon_common=batterymon_helpers.common()

def datetime_now():
    return datetime.today().strftime("%Y-%m-%d %H:%M:%S")

def write_log(current_out, message):
    with open(current_out, "a") as f:
        f.write(message+"\n")

if batterymon_common.GET_BMS_JSON_DATA_MULTIPROCESS:
    from concurrent.futures import ProcessPoolExecutor

    def get_bms_json_data_multiprocess(device):
        try:
            return (device, (
                *batterymon_common.get_bms_json_data(device),
                datetime_now()
            ))
        except(Exception) as e:
            return (device, (
                "EX", e,
                datetime_now()
            ))

if __name__ == "__main__":
    get_bms_json_data_pool=None

    if batterymon_common.GET_BMS_JSON_DATA_MULTIPROCESS:
        import signal

        def shutdown_handler(signum, frame):
            raise KeyboardInterrupt()

        signal.signal(signal.SIGTERM, shutdown_handler)
        signal.signal(signal.SIGINT, shutdown_handler)

        get_bms_json_data_pool=ProcessPoolExecutor(
            max_workers=len(batterymon_common.DEVICES)
        )

    if not os.path.exists(batterymon_common.WORK_DIR):
        os.makedirs(batterymon_common.WORK_DIR)
        os.chmod(batterymon_common.WORK_DIR, 0o1771)

    json_cache={}

    try:
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
                write_log(
                    current_out,
                    datetime_now()+" RL"
                )
                time.sleep(batterymon_common.SAVE_DATA_SECONDS)

                continue

            try:
                batterymon_common.log_start()

                if batterymon_common.GET_BMS_JSON_DATA_MULTIPROCESS:
                    json_cache=dict(get_bms_json_data_pool.map(
                        get_bms_json_data_multiprocess,
                        batterymon_common.DEVICES
                    ))
                else:
                    for device in batterymon_common.DEVICES:
                        try:
                            json_cache[device]=(
                                *batterymon_common.get_bms_json_data(device),
                                datetime_now()
                            )
                        except(Exception) as e:
                            json_cache[device]=(
                                "EX", e,
                                datetime_now()
                            )

                for device, (d, json_data, saved_date) in json_cache.items():
                    try:
                        if d == "EX":
                            write_log(current_out, saved_date
                            +   " EX "+device+" "+str(json_data).replace("\n", "\\n")
                            )
                            continue

                        batterymon_common.pre_log(device, d)

                        output_line="OK "+device
                        save_to_log=False

                        for param in batterymon_common.LOG_PARAMS:
                            if param in batterymon_common.LOG_PARAMS_IGNORE.get(device, []):
                                continue

                            save_to_log=True

                            if param in batterymon_common.CUSTOM_LOG_PARAMS:
                                output_line+=" "+str(batterymon_common.CUSTOM_LOG_PARAMS[param](
                                    param, d.get(param, None)
                                ))
                                continue

                            if isinstance(d.get(param, ""), list):
                                output_line+=" ["+" ".join(str(x) for x in d.get(param, []))+"]"
                                continue

                            output_line+=" "+str(
                                d.get(param, "-1")
                            )

                        if batterymon_common.DUMP_RAW_JSON and device not in batterymon_common.DUMP_RAW_JSON_IGNORE:
                            with open(batterymon_common.CURRENT_OUT+"-"+batterymon_helpers.sanitize_filename(device), "wb") as json_data_f:
                                json_data_f.write(json_data)

                        if save_to_log:
                            write_log(
                                current_out,
                                saved_date+" "+output_line
                            )

                        batterymon_common.post_log(device, d)
                    except(Exception) as e:
                        write_log(current_out, datetime_now()
                        +   " EX "+device+" "+str(e).replace("\n", "\\n")
                        )
            finally:
                batterymon_common.log_finish()

            json_cache={}
            sleep_second=0

            while sleep_second < batterymon_common.SAVE_DATA_SECONDS:
                batterymon_common.on_sleep(sleep_second)
                sleep_second+=1
                time.sleep(1)
    except(KeyboardInterrupt):
        if get_bms_json_data_pool is None:
            raise
    finally:
        if get_bms_json_data_pool is not None:
            get_bms_json_data_pool.shutdown(wait=False)
