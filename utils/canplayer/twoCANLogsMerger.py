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

# Merge with the name of the given interface
with open('mergedCAN.log', 'w') as f:
    with open(log1) as f1, open(log2) as f2:
        enum1 = enumerate(f1)
        enum2 = enumerate(f2)
        try:
            l1 = repCANInterface(next(enum1)[1], interface)
            l2 = repCANInterface(next(enum2)[1], interface)
            while True:
                tf1 = float(l1.split()[0][1:-1])
                tf2 = float(l2.split()[0][1:-1])
                if tf1 < tf2:
                    f.write(l1)
                    print(l1)
                    l1 = repCANInterface(next(enum1)[1], interface)
                else:
                    f.write(l2)
                    print(l2)
                    l2 = repCANInterface(next(enum2)[1], interface)

        except StopIteration:
            f.close()

print("Successfully done.")
