#!/bin/bash

# VirtualCAN Configuration
# $ sudo chmod +x confvcan.sh    # should be done first

sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0
