#!/bin/bash

# Update lock timecode
touch /run/user/1000/robot.lock

# Read CPU load average in the last 15s with uptime
load=`uptime | sed -e 's/.*load average: //' | cut -d, -f1`

# Read battery voltage and current
cd /sys/devices/platform/battery/power_supply/lego-ev3-battery
voltage=`cat voltage_now`
current=`cat current_now`

# Print Robot Status
# [ -z "$jar_time" ] || echo "A$jar_time"
echo "V$((voltage/1000))"
echo "C$((current/1000))"
echo "L$load"
