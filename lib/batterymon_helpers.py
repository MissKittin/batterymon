import os
import shutil
import gzip
import hashlib
import re
import importlib
from datetime import datetime

def merge_file(src, dest): # batterymon_common.mount_arch() and batterymon-arch.py
    if not os.path.exists(src):
        return

    try:
        with open(dest, "a") as f_dest:
            with open(src, "r") as f_src:
                f_dest.write(f_src.read())

        os.remove(src)
    except(Exception):
        return False

    return True

def gzip_file_if_big(file): # batterymon_common.mount_arch() and batterymon-arch.py
    if not os.path.exists(file):
        return

    try:
        if os.path.getsize(file) < common().ARCH_LOG_MAX_SIZE:
            return

        base, ext=os.path.splitext(file)
        current_date=datetime.today().strftime("%Y-%m-%d_%H-%M-%S")

        shutil.move(
            file,
            base+"_"+current_date+ext
        )

        gzip_file(file+"_"+current_date)
    except(Exception):
        return False

def gzip_file(file, compress_level=8): # gzip_file_if_big()
    try:
        with open(file, "rb") as f_in, gzip.open(file+".gz", "wb", compresslevel=compress_level) as f_out:
            f_out.writelines(f_in)

        os.remove(file)
    except(Exception):
        if os.path.exists(file+".gz"):
            os.remove(file+".gz")

def gzip_file_move(src, dest, compress_level=8, chunk_size=524288): # batterymon-arch.py
    src_hasher=hashlib.sha512()

    try:
        with open(src, "rb") as f_in, open(dest, "wb") as f_out:
            class hashing_writer:
                def __init__(self, stream, hasher):
                    self.stream=stream
                    self.hasher=hasher

                def write(self, data):
                    self.hasher.update(data)
                    return self.stream.write(data)

                def flush(self):
                    return self.stream.flush()

                def close(self):
                    return self.stream.close()

            with gzip.GzipFile(fileobj=hashing_writer(f_out, src_hasher), mode="wb", compresslevel=compress_level) as gz_out:
                for chunk in iter(lambda: f_in.read(chunk_size), b''):
                    gz_out.write(chunk)

            f_out.flush()
            os.fsync(f_out.fileno())
    except(Exception):
        if os.path.exists(dest):
            os.remove(dest)

        return False

    src_digest=src_hasher.hexdigest()
    dest_hasher=hashlib.sha512()

    try:
        with open(dest, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b''):
                dest_hasher.update(chunk)
    except(Exception):
        if os.path.exists(dest):
            os.remove(dest)

        return False

    if src_digest == dest_hasher.hexdigest():
        os.remove(src)
        return src_digest

    if os.path.exists(dest):
        os.remove(dest)

    return False

def gzip_file_move_old(src, dest, compress_level=8): # formerly used in batterymon-arch.py - now a free bird
    try:
        with open(src, "rb") as f_in, gzip.open(dest, "wb", compresslevel=compress_level) as f_out:
            f_out.writelines(f_in)

        os.remove(src)
    except(Exception):
        if os.path.exists(dest):
            os.remove(dest)

def extract_bt_macs(macs): # formerly used in batterymon_common.py - now a free bird
    extracted_macs=[]

    for mac in macs:
        match=re.search(r"bt:([0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5})", mac)

        if match:
            extracted_macs.append(match.group(1))

    return extracted_macs

def parse_log_line(line): # batterymon_common._check_battery_voltage()
    parsed_line=[]
    use_subarray=False
    subarray=[]

    if line[-1:] == "\n":
        line=line[:-1]

    for item in line.split(" "):
        if item.startswith("["):
            if item.endswith("]"):
                parsed_line.append([item.strip("[]")])
                continue

            use_subarray=True
            subarray.append(item.lstrip("["))

            continue

        if item.endswith("]"):
            use_subarray=False
            subarray.append(item.rstrip("]"))
            parsed_line.append(subarray)
            subarray=[]

            continue

        if use_subarray:
            subarray.append(item)
            continue

        parsed_line.append(item)

    return parsed_line

def sha512sum(file_path): # formerly used in batterymon-arch.py - now a free bird
    hasher=hashlib.sha512()

    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
    except(Exception):
        return None

    return hasher.hexdigest()

def sanitize_filename(filename, placeholder="_"): # batterymon.py
    return re.sub(r'[\\/:*?"<>|]', placeholder, filename)

# imports
def common():
    global _batterymon_common

    if not _batterymon_common is None:
        return _batterymon_common

    from . import batterymon_common as common

    _batterymon_common=common

    return common

def gpio(callback=None):
    global _batterymon_gpio

    if not _batterymon_gpio is None:
        return _batterymon_gpio

    try:
        gpio=importlib.import_module(
            ".batterymon_gpio_"+common().GPIO_DRIVER,
            package=__package__
        )
    except(ImportError):
        if not callback is None:
            callback()

        from . import batterymon_gpio_dummy as gpio

    _batterymon_gpio=gpio

    return gpio

# init
_batterymon_common=None
_batterymon_gpio=None
