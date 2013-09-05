#!/usr/bin/env bash

#############################################
#
#       Quickstart Agent Installer
#       Author: Stephen Hynes
#       Version: 1.0
#
#############################################

# Need root to run this script
if [ "$(id -u)" != "0" ]; then
    echo "Please run this  script as root."
    echo "Usage: sudo ./install.sh"
    exit 1
fi

LE_LOCATION="https://raw.github.com/logentries/le/master/le"

CURL="/usr/bin/env curl -O"

LOGGER_CMD="logger -t LogentriesTest Test Message Sent By LogentriesAgent"
DAEMON="com.logentries.agent.plist"
DAEMON_DL_LOC="https://raw.github.com/logentries/le/master/install/mac/$DAEMON"
DAEMON_PATH="/Library/LaunchDaemons/$DAEMON"

INSTALL_PATH="/usr/local/bin/le"
REGISTER_CMD="$INSTALL_PATH register"
LE_FOLLOW="$INSTALL_PATH follow"

printf "Welcome to the Logentries Install Script for "; hostname;

printf "Downloading dependencies...\n"
$CURL $LE_LOCATION
$CURL $DAEMON_DL_LOC

printf "Copying files...\n"
chmod +x le
chown root:wheel le
chown root:wheel $DAEMON
mv le $INSTALL_PATH
mv $DAEMON $DAEMON_PATH

printf "We will now register your machine.\n"
$REGISTER_CMD
printf "This script will guide you through following your first set of logs.\n\n"
printf "I have automatically followed these files of interest for you:\n"

LOGS=("/var/log/system.log" "/var/log/install.log" "/var/log/fsck_hfs.log" "/var/log/opendirectoryd.log" "/var/log/appfirewall.log")

for log in "${LOGS[@]}"
do
    if [ -f "${log}" ];  then
        printf "Attempting to follow ${log}... "
        $LE_FOLLOW "${LOG}"
    fi
done

printf "\nRestarting agent..."
launchctl unload $DAEMON_PATH
launchctl load $DAEMON_PATH

i="0"
while [ $i -lt 40 ]
do
    sleep 0.05
    printf "."
    i=$[$i+1]
done

logger "Logentries Test Event 1"
logger "Logentries Test Event 2"
logger "Logentries Test Event 3"
logger "Logentries Test Event 4"
logger "Logentries Test Event 5"

printf "\n\nInstall Complete!\n"

exit 0
