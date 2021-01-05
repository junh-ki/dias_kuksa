"""
This script is to merge two different CAN log files into one with the passed CAN interface.

Since the script uses the can-utils library,
the following command should be run first prior to running this script:

    $ sudo apt install can-utils

can0_example.log + can1_example.log = mergedCAN.log

(e.g., 'python3 twoCANLogsMerger.py --log1 can0_example.log --log2 can1_example.log --can vcan0')

"""

import os
import argparse

def getConfig():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log1", metavar='\b', help="Target log file 1", type=str)
    parser.add_argument("--log2", metavar='\b', help="Target log file 2", type=str)
    parser.add_argument("--can", metavar='\b', help="Result CAN interface name", type=str, default="vcan0")
    args = parser.parse_args()
    return args

def repCANInterface(pstr, interface):
    if not "vcan0" in pstr:
        if "can0" in pstr:
            pstr = pstr.replace("can0", interface)
        elif "can1" in pstr:
            pstr = pstr.replace("can1", interface)
        elif "can2" in pstr:
            pstr = pstr.replace("can2", interface)
    return pstr

args = getConfig()

# Target .log files to be merged
log1 = args.log1
log2 = args.log2

# The name of the CAN interface your hardware has (e.g., can0 or vcan0 or, ...)
interface = args.can

# Create intermediary log strings by using asc2log from can-utils
cmd = 'cat ' + log1
logstr1 = os.popen(cmd).read()
cmd = 'cat ' + log2
logstr2 = os.popen(cmd).read()

# Merge two lists of log strings based on timestamp with the interface, vcan0.
mergedLines = []
index = 0
sl1 = logstr1.splitlines()
sl2 = logstr2.splitlines()
while index < len(sl1):
    l1 = sl1[index]
    ts1 = float(l1.split()[0][1:-1])
    l2 = sl2[0]
    ts2 = float(l2.split()[0][1:-1])
    l1 = repCANInterface(l1, interface)
    l2 = repCANInterface(l2, interface)
    if ts1 < ts2:
        mergedLines.append(l1)
        index += 1
    elif ts1 == ts2:
        mergedLines.append(l1)
        mergedLines.append(l2)
        sl2.remove(l2)
        index += 1
    else:
        mergedLines.append(l2)
        sl2.remove(l2)

# Append the rest of the remaining log string list (if there are)
if len(sl2) > 0:
    for line in sl2:
        line = repCANInterface(line, interface)
        mergedLines.append(line)

# Create the merged logfile with the interface, vcan0.
if len(mergedLines) != 0:
    with open('mergedCAN.log', 'w') as f:
        for item in mergedLines:
            f.write("%s\n" % item)
        f.close()
    print("Successfully done.")
