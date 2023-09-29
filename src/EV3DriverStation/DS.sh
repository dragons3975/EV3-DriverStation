#!/bin/bash

# Update lock timecode
touch robot.lock

# Read jar last modified time (as hex)
jar_time=`cat version.txt 2>/dev/null`

# Read battery voltage (as hex)
cd /sys/devices/platform/battery/power_supply/lego-ev3-battery
voltage=`cat voltage_now`

# Print Robot Status
[ -z "$jar_time" ] || echo "A$jar_time"
echo "V$((voltage/1000))"
