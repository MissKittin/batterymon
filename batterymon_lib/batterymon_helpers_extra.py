import os
import gzip
import hashlib
import re

def gzip_file_move_old( # formerly used in batterymon-arch.py - now a free bird
    src, dest,
    compress_level=8
):
    try:
        with open(src, "rb") as f_in, gzip.open(dest, "wb", compresslevel=compress_level) as f_out:
            f_out.writelines(f_in)

        os.remove(src)
    except(Exception):
        if os.path.exists(dest):
            os.remove(dest)

def extract_bt_macs(macs, prefix="bt:"): # formerly used in batterymon_common.py - now a free bird
    extracted_macs=[]
    pattern=re.compile(
        re.escape(prefix)+r"([0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5})"
    )

    for mac in macs:
        match=pattern.search(mac)

        if match:
            extracted_macs.append(match.group(1))

    return extracted_macs

def sha512sum(file_path): # formerly used in batterymon-arch.py - now a free bird
    hasher=hashlib.sha512()

    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
    except(Exception):
        return None

    return hasher.hexdigest()

def log_line_dict_flatten(items): # log_line_dict()
    for item in items:
        if isinstance(item, list):
            for elem in item:
                yield elem
        else:
            yield item

def log_line_dict_cache( # log_line_dict()
    device,
    batterymon_common,
    prefix="_bm_",
    rebuild=False
):
    global _log_line_dict_key_cache

    keys=_log_line_dict_key_cache.get(device, None)

    if rebuild or keys is None:
        keys=[prefix+"date", prefix+"time", prefix+"status", prefix+"device"]+[
            p for p in batterymon_common.LOG_PARAMS if p not in batterymon_common.LOG_PARAMS_IGNORE.get(
                device,
                []
            )
        ]

        _log_line_dict_key_cache[device]=keys

    return keys

def log_line_dict( # for batterymon-extras project
    parsed_line,
    batterymon_common,
    prefix="_bm_",
    build_cache=False
):
    # Usage:
    #  log_line=<line read from pending.txt>
    #  try:
    #      parsed_log_dict=batterymon_helpers_extra.log_line_dict(
    #          batterymon_helpers.parse_log_line(log_line),
    #          batterymon_common
    #      )
    #  except(IndexError, TypeError) as e:
    #      # handle exception

    # Output dict format:
    #  {
    #   "_bm_date": "YYYY-MM-DD",
    #   "_bm_time": "HH:MM:SS",
    #   "_bm_status": "RL"
    #  }
    #  {
    #   "_bm_date": "YYYY-MM-DD",
    #   "_bm_time": "HH:MM:SS",
    #   "_bm_status": "EX",
    #   "_bm_device": "DEVICE",
    #   "_bm_ex_msg": "Exception message"
    #  }
    #  {
    #   "_bm_date": "YYYY-MM-DD",
    #   "_bm_time": "HH:MM:SS",
    #   "_bm_status": "OK",
    #   "_bm_device": "DEVICE",
    #   "FirstParamFromDEVICES": "value",
    #   "SecondParamFromDEVICES": "value",
    #   "ThirdParamFromDEVICES": ["third_value_list_a", "third_value_list_b" ...],
    #   ...
    #   "LastParamFromDEVICES": "value"
    #  }

    if build_cache:
        for device in get_log_devices(batterymon_common):
            log_line_dict_cache(device, batterymon_common, prefix)

        return

    if parsed_line[2] == "RL":
        return {
            prefix+"date": parsed_line[0],
            prefix+"time": parsed_line[1],
            prefix+"status": parsed_line[2]
        }

    if parsed_line[2] == "EX":
        return {
            prefix+"date": parsed_line[0],
            prefix+"time": parsed_line[1],
            prefix+"status": parsed_line[2],
            prefix+"device": parsed_line[3],
            prefix+"ex_msg": " ".join(
                str(x) for x in log_line_dict_flatten(parsed_line[4:])
            )
        }

    return dict(zip(
        log_line_dict_cache(parsed_line[3], batterymon_common, prefix),
        parsed_line
    ))

def get_current_out_path(batterymon_common): # for batterymon-extras project
    current_out=batterymon_common.CURRENT_OUT

    if os.path.exists(batterymon_common.LOCK_FILE):
        current_out=batterymon_common.BACKUP_OUT

    return current_out

def get_log_devices(batterymon_common): # for log_line_dict() and batterymon-extras project
    return [
        device
        for device in batterymon_common.DEVICES
        if any(
            param not in batterymon_common.LOG_PARAMS_IGNORE.get(device, [])
            for param in batterymon_common.LOG_PARAMS
        )
    ]

def get_log_devices_len(batterymon_common): # for batterymon-extras project
    return sum(
        any(param not in batterymon_common.LOG_PARAMS_IGNORE.get(device, []) for param in batterymon_common.LOG_PARAMS)
        for device in batterymon_common.DEVICES
    )

# init
_log_line_dict_key_cache={}
