# Who-Ate-My-Bandwidth (Netgear Bandwidth Monitor)

This tool uses the router "undocumented" API to read flow data and update Redis for all devices connected to network. Later, this data is used to serve a fancy realtime dashboard. 

## Features

* Uses server side events to push data to dashboard: The graphs is near realtime with no page reloads
* Uses Redis as the backend for storing bandwidth and device names data

## Developer Notes

This app consists of two components:-

* **router_bw_stats.py**: This python script calls the Netgear API and parses response data. After finding the bandwidth rate for all devices, it sends that data to redis with the keys with names in the format "mac_upload|download". Also, it calls the API to get device names from mac address and sends the same to Redis.
* **Web server under ./dashboards**:- This Go code reads all values from Redis and uses server side events to send data to the client. 

# Dashboard Screenshot

![alt tag](https://raw.githubusercontent.com/shadyabhi/netgear_bw_monitor/master/dashboard/screenshot.jpg)

# Devices Tested

* Netgear Nighthawk X4 R7500
