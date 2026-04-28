# DO NOT IMPORT THIS LIBRARY
# always use the parse_log_line function
# from the batterymon_helpers library

def parse_log_line(line): # batterymon_common._check_battery_voltage()
    # Usage:
    #  log_line=<line read from pending.txt>
    #  parsed_log_line=batterymon_helpers.parse_log_line(
    #      log_line
    #  )

    # Output list format:
    #  [
    #   "YYYY-MM-DD",
    #   "HH:MM:SS",
    #   "RL"
    #  ]
    #  [
    #   "YYYY-MM-DD",
    #   "HH:MM:SS",
    #   "EX",
    #   "DEVICE",
    #   "Exception", "message", "because", "this", "parser", "is", "dumb"
    #  ]
    #  [
    #   "YYYY-MM-DD",
    #   "HH:MM:SS",
    #   "OK",
    #   "DEVICE",
    #   "first_value",
    #   "second_value",
    #   ["third_value_list_a", "third_value_list_b" ...]
    #   ...
    #   "last_value"
    #  ]

    parsed_line=[]
    use_subarray=False
    subarray=[]

    if line[-1:] == "\n":
        line=line.rstrip("\n")

    for item in line.split():
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
