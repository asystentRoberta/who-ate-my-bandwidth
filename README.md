# Netgear Bandwidth Monitor

This script uses the router "undocumented" API to read flow data and update Redis for all devices connected to network.

## Features

* Uses server side events to push data to dashboard: The graphs is near realtime with no page reloads
* Uses Redis as the backend for storing bandwidth and device names data

# Dashboard Screenshot

![alt tag](https://raw.githubusercontent.com/shadyabhi/netgear_bw_monitor/master/dashboard/screenshot.jpg)

# Devices Tested

* Netgear Nighthawk X4 R7500
