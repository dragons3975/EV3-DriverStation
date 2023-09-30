#!/bin/bash

# Update lock timecode
touch robot.lock

# Read jar last modified time
jar_time=`cat version.txt 2>/dev/null`

# Read CPU load average in the last 15s with uptime
load=`uptime | sed -e 's/.*load average: //' | cut -d, -f1`

# Read battery voltage and current
cd /sys/devices/platform/battery/power_supply/lego-ev3-battery
voltage=`cat voltage_now`

# Print Robot Status
[ -z "$jar_time" ] || echo "A$jar_time"
echo "V$((voltage/1000))"
echo "L$load"
