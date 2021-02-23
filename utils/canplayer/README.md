# CAN Log Modifier Scripts for `canplayer`

These Python scripts modify CAN logfiles according to the user's preference.

## Prerequisite for both scripts

* Python 3
* SocketCAN (`can-utils`)
~~~
$ sudo apt install can-utils
~~~

## asc2log_channel_separator.py

This script does two jobs:

1. Convert `.asc` to `.log` in order for the result log file(s) to be compliant with `canplayer` that is used to play CAN logfiles in the Linux environment
2. Separate the traces by CAN channel and produce result file(s) in the `.log` format.

The `.asc` format is supported by Vector Tools (i.e., CANalyzer, CANoe, etc..). Thus, this script is used when the target log file is recorded by Vector software. The input file's format shall be `.asc`. The number of result log files is equal to the number of channels the traces in the input file come from.

The script needs two arguments that need to be set to run. Please make sure the following are set correctly:
* `asc`: Name of the target `.asc` file (Example Format: `--asc example.asc`)
* `can`: Result CAN interface name (Example Format: `--can vcan0`)

To run the script, place the target `.asc` file to the directory where this script is located. In the same directory, run:
~~~
$ python3 asc2log_channel_separator.py --asc example.asc --can vcan0
~~~
As a result, `example.asc` is separated into `can0_example.log`, `can1_example.log`, `can2_example.log`. If `can0` is the only CAN channel that is present in `example.asc`, the result is only `can0_example.log`. Here, the CAN interface used in the result log file(s) is `vcan0` as it is put under the `--can` argument.

## twoCANLogsMerger.py

This script merges two different CAN log files into one based on each CAN trace's timestamp value in chronological order.

The script needs three arguments that need to be set to run. Please make sure the following are set correctly:
* `log1`: Name of the target `.log` file 1 (Example Format: `--log1 can0_example.log`)
* `log2`: Name of the target `.log` file 2 (Example Format: `--log2 can1_example.log`)
* `can`: Result CAN interface name (Example Format: `--can vcan0`)

To run the script, place the two target `.log` files to the directory where this script is located. In the same directory, run:
~~~
$ python3 twoCANLogsMerger.py --log1 can0_example.log --log2 can1_example.log --can vcan0
~~~
As a result, the two `.log` files, `can0_example.log` and `can1_example.log` are merged into `mergedCAN.log`. Here, the CAN interface used in the result log file(s) is `vcan0` as it is put under the `--can` argument.
