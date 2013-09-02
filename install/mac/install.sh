#!/usr/bin/env bash

#############################################
#
#       Quickstart Agent Installer
#       Author: Stephen Hynes
#       Version: 1.0
#
#
#
#############################################

# Need root to run this script
if [ "$(id -u)" != "0" ] 
then
echo "Please run this  script as root."
echo "Usage: sudo bash quickstart.sh"
exit 1
fi   

REGISTER_CMD="./le register"
LE_LOCATION="https://raw.github.com/logentries/le/master/le"
CURL="/usr/bin/curl"
CURL_TAGS="-O"
LOGGER_CMD="logger -t LogentriesTest Test Message Sent By LogentriesAgent"
AGENT_DAEMON_DL_LOC="https://raw.github.com/logentries/le/master/install/mac/com.logentries.agent.plist"
AGENT_DAEMON_DIR="/Library/LaunchDaemons/"
AGENT_DAEMON="com.logentries.agent.plist"
LE_AGENT_INSTAL_DIR="/Usr/local/bin"
LE_FOLLOW="./le follow"
LE_MONITOR="./le monitor"
USER=whoami

printf "Welcome to the Logentries Install Script for "; hostname;
$CURL $CURL_TAGS $LE_LOCATION
$CURL $CURL_TAGS $AGENT_DAEMON_DL_LOC
chmod +x le
mv le $LE_AGENT_INSTAL_DIR
mv $AGENT_DAEMON $AGENT_DAEMON_DIR
cd $LE_AGENT_INSTAL_DIR
printf "We will now register your machine.\n"
printf "\n"
$REGISTER_CMD
printf "\n"
printf "This script will guide you through following your first set of logs. \n"
printf "I have automatically followed these files of interest for you.\n"


if [ -f /var/log/system.log ];  then
printf "/var/log/system.log - System logs.\n"
$LE_FOLLOW /var/log/system.log
fi
printf "\n"
if [ -f /var/log/install.log ]; then
printf "/var/log/install.log - Install logs.\n"
$LE_FOLLOW /var/log/install.log
fi
printf "\n"
if [ -f /var/log/fsck_hfs.log ]; then
printf "/var/log/fsck_hfs.log - FSCK log file.\n"
$LE_FOLLOW /var/log/fsck_hfs.log
fi
printf "\n"
if [ -f /var/log/opendirectoryd.log ]; then
printf "/var/log/opendirectoryd.log - Open Directoryd log.\n"
$LE_FOLLOW /var/log/opendirectoryd.log
fi
printf "\n"
if [ -f /var/log/appfirewall.log ]; then
printf "/var/log/appfirewall.log - App firewall log.\n"
$LE_FOLLOW /var/log/appfirewall.log
fi
printf "\n"

logger "Logentries Test Event 1"
logger "Logentries Test Event 2"
logger "Logentries Test Event 3"
logger "Logentries Test Event 4"
logger "Logentries Test Event 5"

printf "Restarting agent..\n"
launchctl load /Library/LaunchDaemons/$AGENT_DAEMON
printf "Install Complete!\n\n"
printf "Will now monitor logs from terminal"

exit 0


