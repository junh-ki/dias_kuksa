"""
This script is to separate a logfile according to the CAN channel
and convert the results to the log-formatted files.

example.asc > ch1_example.log, ch2_example.log

(e.g., 'python3 asc2log_channel_separater.py example.asc vcan0')

"""

import os
import sys
import ntpath

# Target .asc file (or path) to be converted to .log
path = sys.argv[1]

# The name of the CAN interface your hardware has (e.g., can0 or vcan0 or, ...)
interface_name = sys.argv[2]

# Create an intermediate log file by using asc2log from can-utils
cmd = 'asc2log -I ' + path + ' -O logfile.log'
os.system(cmd)

# Preparation for separating the intermediate file according to the channel name: can0/can1
can0 = "can0"
can0lines = []
can1 = "can1"
can1lines = []

with open ('logfile.log', 'rt') as myfile:
    for myline in myfile:
        if can0 in myline:
            myline = myline.replace(can0, interface_name)
            can0lines.append(myline)            
        elif can1 in myline:
            myline = myline.replace(can1, interface_name)
            can1lines.append(myline)

# Remove the intermediate file
os.remove('logfile.log')

# Reproduce the result filenames from the input filename
file_name_with_format = ntpath.basename(path)
split_string = file_name_with_format.split(".",1)
file_name = split_string[0]

# Create the result .log file that only contains data from CAN channel 0 (can0)
if len(can0lines) != 0:
    with open('ch0_' + file_name + '.log', 'w') as f:
        for item in can0lines:
            f.write("%s" % item)

# Create the result .log file that only contains data from CAN channel 1 (can1)
if len(can1lines) != 0:
    with open('ch1_' + file_name + '.log', 'w') as f:
        for item in can1lines:
            f.write("%s" % item)
