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

printf "Welcome to the Logentries Install Script\n"

printf "Downloading dependencies...\n"
$CURL $LE_LOCATION
$CURL $DAEMON_DL_LOC

printf "Copying files...\n"
chmod +x le
chown root:wheel le
chown root:wheel $DAEMON
mv le $INSTALL_PATH
mv $DAEMON $DAEMON_PATH

$REGISTER_CMD

LOGS=("/var/log/system.log" "/var/log/install.log" "/var/log/fsck_hfs.log" "/var/log/opendirectoryd.log" "/var/log/appfirewall.log")

for log in "${LOGS[@]}"
do
    if [ -f "${log}" ];  then
        $LE_FOLLOW "${LOG}"
    fi
done

printf "*** Install Complete! ****\n\n"
printf "The Logentries Agent is now monitoring the following files by default:\n"
for log in "${LOGS[@]}"
do
    if [ -f "${log}" ]; then
        printf "${LOG}\n"
    fi
done
printf "If you would like to monitor more files, simply run this command as root, 'le follow filepath', e.g. 'le follow /var/log/mylog.log'\n\n"
printf "And be sure to restart the agent service for new files to take effect, you can do this with the following two commands.\n"
printf "launchctl unload ${DAEMON_PATH}\n"
printf "launchctl load ${DAEMON_PATH}\n"
printf "For a full list of commands, run 'le --help' in the terminal.\n\n"
printf "************************************\n\n"

launchctl unload $DAEMON_PATH
launchctl load $DAEMON_PATH

i="0"
while [ $i -lt 40 ]
do
    sleep 0.05
    printf "."
    i=$[$i+1]
done

printf "We will now send some sample events to your new Logentries account. This will take about 10 seconds.\n\n"

l=1
while [ $l -le 100 ]
do
	logger "Logentries Test Event ${l}"
        printf "."
	sleep 0.1
	l=$(( $l + 1 ))
done

exit 0
