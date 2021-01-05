"""
This script is to convert a .asc file to a .log file
and separate the result by CAN channel (up to three channels)

Since the script uses the can-utils library,
the following command should be run first prior to running this script:

    $ sudo apt install can-utils

example.asc > can0_example.log, can1_example.log, can2_example.log

(e.g., 'python3 asc2log_channel_separator.py --asc example.asc --can vcan0')

"""

import os
import ntpath
import argparse

def getConfig():
    parser = argparse.ArgumentParser()
    parser.add_argument("--asc", metavar='\b', help="Target asc file", type=str)
    parser.add_argument("--can", metavar='\b', help="Result CAN interface name", type=str)
    args = parser.parse_args()
    return args

args = getConfig()

# Target .asc file to be converted to .log
asc = args.asc

# The name of the CAN interface your hardware has (e.g., can0 or vcan0 or, ...)
interface = args.can

# Create an intermediary log string by using asc2log from can-utils
cmd = 'asc2log -I ' + asc
data = os.popen(cmd).read()

# Preparation for separating the intermediate file according to the channel name: can0/can1
can0 = "can0"
can0lines = []
can1 = "can1"
can1lines = []
can2 = "can2"
can2lines = []

for myline in data.splitlines():
    if can0 in myline:
        myline = myline.replace(can0, interface)
        can0lines.append(myline)
    elif can1 in myline:
        myline = myline.replace(can1, interface)
        can1lines.append(myline)
    elif can2 in myline:
        myline = myline.replace(can2, interface)
        can2lines.append(myline)

# Reproduce the result filenames from the input filename
file_name_with_format = ntpath.basename(asc)
split_string = file_name_with_format.split(".",1)
file_name = split_string[0]

# Create the result .log file that only contains data from CAN channel 0 (can0)
if len(can0lines) != 0:
    with open('can0_' + file_name + '.log', 'w') as f:
        for item in can0lines:
            f.write("%s\n" % item)
        f.close()

# Create the result .log file that only contains data from CAN channel 1 (can1)
if len(can1lines) != 0:
    with open('can1_' + file_name + '.log', 'w') as f:
        for item in can1lines:
            f.write("%s\n" % item)
        f.close()

# Create the result .log file that only contains data from CAN channel 2 (can2)
if len(can2lines) != 0:
    with open('can2_' + file_name + '.log', 'w') as f:
        for item in can2lines:
            f.write("%s\n" % item)
        f.close()

print("Successfully done.")
