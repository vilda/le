#!/usr/bin/env bash

#############################################
#
#       Quickstart Agent Installer
#       Author: Stephen Hynes, Charles Phillips
#       Version: 1.0
#
#############################################

# Need root to run this script
if [ "$(id -u)" != "0" ]; then
    echo "Please run this  script as root."
    echo "Usage: sudo ./install.sh"
    exit 1
fi

TMP_DIR=$(mktemp -d -t logentries.XXXXX)
trap "rm -rf "$TMP_DIR"" EXIT

FILES="le.py backports.py utils.py __init__.py metrics.py formats.py"
LE_PARENT="https://raw.githubusercontent.com/logentries/le/master/src/"
CURL="/usr/bin/env curl -O"

SMARTOS_INSTALL="https://raw.githubusercontent.com/logentries/le/master/install/smartos/"
INSTALL_DIR="/opt/local/lib/logentries"
LOGGER_CMD="logger -t LogentriesTest Test Message Sent By LogentriesAgent"
DAEMON="svc-logentries"
DAEMON_DL_LOC="$SMARTOS_INSTALL$DAEMON"
DAEMON_PATH_ROOT="/opt/local/lib/svc/method"
DAEMON_PATH="$DAEMON_PATH_ROOT/$DAEMON"

SMF_CONFIG="logentries.xml"
SMF_CONFIG_DL_LOC="$SMARTOS_INSTALL$SMF_CONFIG"
SMF_CONFIG_PATH_ROOT="/opt/local/lib/svc/manifest"
SMF_CONFIG_PATH="$SMF_CONFIG_PATH_ROOT/$SMF_CONFIG"

INSTALL_PATH_ROOT="/opt/local/bin"
INSTALL_PATH="$INSTALL_PATH_ROOT/le"
REGISTER_CMD="$INSTALL_PATH register"
LE_FOLLOW="$INSTALL_PATH follow"

printf "Welcome to the Logentries Install Script\n"

printf "Downloading dependencies...\n"

cd "$TMP_DIR"
for file in $FILES ; do
  echo $file
  $CURL $LE_PARENT/$file
done

$CURL $DAEMON_DL_LOC
$CURL $SMF_CONFIG_DL_LOC
sed -i -e 's/python2/python/' *.py

printf "Copying files...\n"
mkdir -p "$INSTALL_DIR"/logentries || true
mv *.py "$INSTALL_DIR"/logentries
chown -R root:root "$INSTALL_DIR"
chmod +x "$INSTALL_DIR"/logentries/le.py

chown root:root $DAEMON
mkdir -p $DAEMON_PATH_ROOT
mv $DAEMON $DAEMON_PATH
chmod +x $DAEMON_PATH

rm -f "$INSTALL_PATH" || true
mkdir -p $INSTALL_PATH_ROOT
ln -s "$INSTALL_DIR"/logentries/le.py "$INSTALL_PATH" 2>/dev/null || true

mkdir -p $SMF_CONFIG_PATH_ROOT
mv $SMF_CONFIG $SMF_CONFIG_PATH

echo "Adding logentries agent to svcadm  (Services)"
#Add logentries agent to the services
svccfg import $SMF_CONFIG_PATH

$REGISTER_CMD
$LE_FOLLOW "/var/log/syslog"

printf "\n**** Install Complete! ****\n\n"
printf "If you would like to monitor more files, simply run this command as root, 'le follow filepath', e.g. 'le follow /var/log/mylog.log'\n\n"
printf "And be sure to restart the agent service for new files to take effect, you can do this with the following two commands.\n"
printf "svcadm disable logentries\n"
printf "svcadm enable logentries\n"
printf "For a full list of commands, run 'le --help' in the terminal.\n\n"

svcadm disable logentries
svcadm enable logentries

printf "Starting agent"
i="0"
while [ $i -lt 40 ]
do
    sleep 0.05
    printf "."
    i=$[$i+1]
done

printf "DONE\n"

exit 0
