#!/bin/bash

#############################################
#
#	Logentries Agent Installer
#
#	Supported Distro's:
#		Debian 5 and newer
#		Ubuntu 9.10 and newer
#		Fedora 14 and newer
#		CentOS 5/6  (RedHat 6)
#		Amazon AMI
#
#############################################

VERSION="1.0.6"

# Need root to run this script
if [ "$(id -u)" != "0" ]
then
	echo "Please run this install script as root."
	echo "Usage: sudo bash install.sh"
	exit 1
fi

KEY_CMD_MIT="gpg --homedir /root/.gnupg --keyserver pgp.mit.edu --recv-keys C43C79AD"
KEY_CMD_UBUNTU="gpg --homedir /root/.gnupg --keyserver keyserver.ubuntu.com --recv-keys C43C79AD"
KEY_CMD_EXPORT="gpg --homedir /root/.gnupg -a --export C43C79AD"
KEY_CMD_COMPLETE="apt-key add /tmp/le.key"
KEY_CMD_CLEAN="rm /tmp/le.key"

DEBIAN_REPO_CONF="/etc/apt/sources.list.d/logentries.list"
DEBIAN_UPDATE="apt-get update -y"
DEBIAN_AGENT_INSTALL="apt-get install logentries -qq -y"
DEBIAN_PROCTITLE_INSTALL="apt-get install python-setproctitle -qq -y"
DEBIAN_DAEMON_INSTALL="apt-get install logentries-daemon -qq -y"
DEBIAN_CURL_INSTALL="apt-get install curl -y"

REDHAT_REPO_CONF="/etc/yum.repos.d/logentries.repo"
REDHAT_UPDATE="yum update -y"
REDHAT_AGENT_INSTALL="yum install logentries -q -y"
REDHAT_PROCTITLE_INSTALL="yum install python-setproctitle -q -y"
REDHAT_DAEMON_INSTALL="yum install logentries-daemon -q -y"
REDHAT_CURL_INSTALL="yum install curl curl-devel -y"

CONFIG_DELETE_CMD="rm /etc/le/config"
REGISTER_CMD="le register"
FOLLOW_CMD="le follow"
LOGGER_CMD="logger -t LogentriesTest Test Message Sent By LogentriesAgent"
DAEMON_RESTART_CMD="service logentries restart"
FOUND=0
AGENT_NOT_FOUND="The agent was not found after installation.\n Please contact support@logentries.com\n"
SET_ACCOUNT_KEY="--account-key="

TAG_NAMES=("Kernel - Process Terminated" "Kernel - Process Killed" "Kernel - Process Started" "Kernel - Process Stopped" "User Logged In" "Invalid User Login attempt" "POSSIBLE BREAK-IN ATTEMPT" "Error")
TAG_PATTERNS=("/terminated with status 100/" "/Killed process/" "/\/proc\/kmsg started/" "/Kernel logging (proc) stopped/" "/Accepted publickey for/" "/Invalid user/" "/POSSIBLE BREAK-IN ATTEMPT/" "/Invalid user admin/")
EVENT_COLOR=("66ff00" "6699ff" "009900" "ff6633" "ff0066" "9999ff" "000099" "999966")

CURL="curl"
CONTENT_HEADER="\"Content-Type: application/json\""
HEADER="-H"
DATA="--data"
API="api.logentries.com"

declare -a LOGS_TO_FOLLOW=(
/var/log/messages
/var/log/dmesg
/var/log/auth.log
/var/log/boot.log
/var/log/daemon.log
/var/log/dkpg.log
/var/log/kern.log
/var/log/lastlog
/var/log/mail.log
/var/log/user.log
/var/log/Xorg.x.log
/var/log/alternatives.log
/var/log/btmp
/var/log/cups
/var/log/anaconda.log
/var/log/cron
/var/log/secure
/var/log/wtmp
/var/log/faillog);

if [ -f /etc/le/config ]; then
	printf "******WARNING******\n"
	printf "It looks like you already have the Logentries agent registered on this machine\n"
	read -p "Are you sure you want to wipe your existing settings and continue with the installation? (y) or (n): "
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		$CONFIG_DELETE_CMD
	else
		echo ""
		printf "Exiting install script\n"
		exit 0
	fi
fi

printf "*****Beginning Logentries Installation*****\n"

if [ -f /etc/issue ] && grep "Amazon Linux AMI" /etc/issue -q; then
	# Amazon Linux AMI
cat << EOL >> $REDHAT_REPO_CONF
[logentries]
name=Logentries repo
enabled=1
metadata_expire=1d
baseurl=http://rep.logentries.com/rh/\$basearch
gpgkey=http://rep.logentries.com/RPM-GPG-KEY-logentries
EOL

	printf "Updating packages...(This may take a few minutes if you have a lot of updates)\n"
	$REDHAT_UPDATE >/tmp/logentriesDebug 2>&1

	printf "Installing logentries package...\n"
	$REDHAT_AGENT_INSTALL >/tmp/logentriesDebug 2>&1

	# try and install python-setproctitle
	$REDHAT_PROCTITLE_INSTALL >/tmp/logentriesDebug 2>&1

	# Check for agent executable
	if [ ! -f /usr/bin/le ];then
		echo $AGENT_NOT_FOUND
		exit 1
	fi

	# Check if curl is installed, if not install it
	if  hash curl 2>/dev/null;then
       echo "curl already installed"
	else
	    REDHAT_CURL_INSTALL
	fi

	# Prompt the user for their Logentries credentials and register the agent
	if [[ -z "$LE_ACCOUNT_KEY" ]];then
		$REGISTER_CMD
	else
		$REGISTER_CMD $SET_ACCOUNT_KEY$LE_ACCOUNT_KEY
	fi


	printf "Installing logentries daemon package...\n"
	$REDHAT_DAEMON_INSTALL

	FOUND=1

elif [ -f /etc/debian_version ]; then

	if hash lsb_release 2>/dev/null; then
		CODENAME=$(lsb_release -c | sed 's/Codename://' | tr -d '[:space:]')
	else
		release=$(cat /etc/debian_version)
		IFS='.' read -a array <<< "$release"

		case "${array[0]}" in
		# Debian
		7) CODENAME="wheezy"
		   ;;
		6) CODENAME="squeeze"
		   ;;
		5) CODENAME="lenny"
		   ;;
		*) CODENAME="UNKNOWN"
		   ;;
		esac
	fi

	if [ "$CODENAME" == "UNKNOWN" ]; then
		printf "Unknown distribution, please contact support@logentries.com\n"
		exit 1
	fi

	# Debian/Ubuntu
	echo "deb http://rep.logentries.com/ ${CODENAME} main" > $DEBIAN_REPO_CONF

	$KEY_CMD_MIT >/tmp/logentriesDebug 2>&1

	if [ "$?" != "0" ]; then
		echo "MIT keyserver not working, fall back to ubuntu keyserver" >>/tmp/logentriesDebug
		# Try different keyserver
		$KEY_CMD_UBUNTU >/tmp/logentriesDebug 2>&1
	fi

	$KEY_CMD_EXPORT >/tmp/le.key
	$KEY_CMD_COMPLETE
	$KEY_CMD_CLEAN

	printf "Updating packages...(This may take a few minutes if you have alot of updates)\n"
	$DEBIAN_UPDATE >/tmp/logentriesDebug 2>&1

	printf "Installing logentries package...\n"
	$DEBIAN_AGENT_INSTALL
	# Try and install the python-setproctitle package on certain distro's
	$DEBIAN_PROCTITLE_INSTALL >/tmp/logentriesDebug 2>&1

	# Check if agent executable exists before trying to register
	if [ ! -f /usr/bin/le ];then
		echo $AGENT_NO_FOUND
		exit 1
	fi

	# Check if curl is installed, if not install it
	if  hash curl 2>/dev/null;then
       echo "curl already installed"
	else
	    DEBIAN_CURL_INSTALL
	fi

	# Prompt the user for their Logentries credentials and register the agent
	if [[ -z "$LE_ACCOUNT_KEY" ]];then
		$REGISTER_CMD
	else
		$REGISTER_CMD $SET_ACCOUNT_KEY$LE_ACCOUNT_KEY
	fi

	printf "Installing logentries daemon package...\n"
	$DEBIAN_DAEMON_INSTALL

	FOUND=1

elif [ -f /etc/redhat-release ]; then
	# CentOS 6  /  RHEL 6 / Fedora / Amazon Linux AMI
DIST=centos5
GPG="gpgcheck=0"

if [ -f /etc/centos-release ] || [ -f /etc/fedora-release ]; then
	# Not CentOS 5, use redhat baseurl and gpgcheck
	DIST=rh
	GPG="gpgkey=http://rep.logentries.com/RPM-GPG-KEY-logentries"
fi

cat << EOL >> $REDHAT_REPO_CONF
[logentries]
name=Logentries repo
enabled=1
metadata_expire=1d
baseurl=http://rep.logentries.com/$DIST/\$basearch
$GPG
EOL

	printf "Updating packages...(This may take a few minutes if you have alot of updates)\n"
	$REDHAT_UPDATE >/tmp/logentriesDebug 2>&1

	printf "Installing logentries package...\n"
	$REDHAT_AGENT_INSTALL >/tmp/logentriesDebug 2>&1

	# try and install python-setproctitle
	$REDHAT_PROCTITLE_INSTALL >/tmp/logentriesDebug 2>&1

	# Check that agent executable exists before trying to register
	if [ ! -f /usr/bin/le ];then
		echo $AGENT_NOT_FOUND
	fi

	# Prompt the user for their Logentries credentials and register the agent
	if [[ -z "$LE_ACCOUNT_KEY" ]];then
		$REGISTER_CMD
	else
		$REGISTER_CMD $SET_ACCOUNT_KEY$LE_ACCOUNT_KEY
	fi

	printf "Installing logentries daemon package...\n"
	$REDHAT_DAEMON_INSTALL

	FOUND=1
fi

if [ $FOUND == "1" ]; then
	if [ -f /var/log/syslog ]; then
		$FOLLOW_CMD /var/log/syslog >/tmp/logentriesDebug 2>&1
	fi

	printf "**** Install Complete! ****\n\n"
	printf "The Logentries agent is now monitoring /var/log/syslog by default\n"
	printf "This install script can also monitor the following files by default..\n"

	for x in "${LOGS_TO_FOLLOW[@]}"
	do
		echo $x
	done
	read -p "Would you like to monitor these also, you can choose certain logs?..(y) or (n): "
	printf "\n"
	if [[ $REPLY =~ ^[Yy]$ ]];then
		for j in "${LOGS_TO_FOLLOW[@]}"
		do
			if [ -f $j ]; then
				read -p "Would you like to follow $j ?..(y) or (n): "
				if [[ $REPLY =~ ^[Yy]$ ]]; then
					$FOLLOW_CMD $j >/tmp/LogentriesDebug 2>&1
					printf "Will monitor $j\n"
				fi
			fi
		done
		$DAEMON_RESTART_CMD >/tmp/logentriesDebug 2>&1
	fi
	echo ""
	CUSTOM_LOOP=0
	while [ $CUSTOM_LOOP -lt 1 ]
	do
		read -p "Would you like to monitor another log by entering the filepath?..(y) or (n): "
		if [[ $REPLY =~ ^[Yy]$ ]];then
			read -p "Enter the full filepath for the log: "
			if [ ! -f $REPLY ];then
				printf "The filepath: $REPLY does not exist\n"
				continue
			fi
			$FOLLOW_CMD $REPLY >/tmp/logentriesDebug 2>&1
			printf "Will monitor: $REPLY\n"
		else
			CUSTOM_LOOP=1
			printf "\n"
		fi
	done

	$DAEMON_RESTART_CMD >/tmp/logentriesDebug 2>&1

	sleep 1

	printf "If you would like to monitor more files, simply run this command as root, 'le follow filepath', e.g. 'le follow /var/log/auth.log'\n\n"
	printf "And be sure to restart the agent service for new files to take effect, you can do this with 'sudo service logentries restart'\n"
	printf "On some older systems, the command is: sudo /etc/init.d/logentries restart\n\n"
	printf "For a full list of commands, run 'le --help' in the terminal.\n\n"
	printf "********************************\n\n"

	printf "We will now send some sample events to your new Logentries account. This will take about 10 seconds\n\n"
	USER_KEY_LINE=$(sed -n '2p' /etc/le/config)
	USER_KEY=${USER_KEY_LINE#*= }
	LE_COMMAND=$(le ls /hosts/`python -c "import socket; print socket.getfqdn().split('.')[0]"`/syslog | grep key)
	LOG_KEY=${LE_COMMAND#key = }

	echo "Creating Events & Tags \n"
	$CURL -O "https://raw.github.com/StephenHynes7/le/master/install/linux/seeding.py"
	chmod +x seeding.py
	TAG_ID=$(python seeding.py createEvent $USER_KEY $LOG_KEY)

	echo "Seeding data, this can take up to 15 seconds"
	if hash logger 2>/dev/null; then

		i=1
		while [ $i -le 2 ]
		do

			$LOGGER_CMD "CRON[29258]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)"
			$LOGGER_CMD "CRON[29261]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)"
			$LOGGER_CMD "CRON[29252]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)"
			$LOGGER_CMD "CRON[29222]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)"
			$LOGGER_CMD "CRON[12345]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)"
			$LOGGER_CMD "dhclient: bound to x.3x.18.1x -- renewal in 41975 seconds."
			$LOGGER_CMD "mongodb main process (127x) terminated with status 100)"
			$LOGGER_CMD "Out of Memory: Killed process 2592 (oracle)"
			$LOGGER_CMD "CRON[29258]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)"
			$LOGGER_CMD "CRON[29261]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)"
			$LOGGER_CMD "kernel: imklog 5.8.6, log source = /proc/kmsg started."

			$LOGGER_CMD "kernel: Kernel logging (proc) stopped."
			$LOGGER_CMD "CRON[29258]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)"
			$LOGGER_CMD "CRON[29261]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)"
			$LOGGER_CMD "CRON[29252]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)"
			$LOGGER_CMD "CRON[29222]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)"
			$LOGGER_CMD "CRON[12345]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)"
			$LOGGER_CMD "sshd[562x]: Invalid user ubuntu1 from 5x.x.x.5x "
			$LOGGER_CMD "sshd[562x]: Invalid user ubuntu2 from 5x.x.x.5x"
			$LOGGER_CMD "sshd[562x]: Invalid user root from 5x.x.x.5x"
			$LOGGER_CMD "sshd[562x]: Invalid user admin from 5x.x.x.5x"
			$LOGGER_CMD "CRON[29258]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)"
			$LOGGER_CMD "CRON[29261]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)"
			$LOGGER_CMD "CRON[29252]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)"
			$LOGGER_CMD "sshd[564x]: Accepted publickey for ubuntu from 50.x.x.x port 22xxx ssh2"
			$LOGGER_CMD "kernel: [    1.351600] rtc_cmos: probe of rtc_cmos failed with error -38"

			sleep 0.1
			i=$(( $i + 1 ))
		done
	else
		i=1
		while [ $i -le 2 ]
		do

			echo "Logentries Test Event: CRON[29258]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)" >> /var/log/syslog
			echo "Logentries Test Event: CRON[29261]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)" >> /var/log/syslog
			echo "Logentries Test Event: CRON[29252]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)" >> /var/log/syslog
			echo "Logentries Test Event: CRON[29222]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)" >> /var/log/syslog
			echo "Logentries Test Event: CRON[12345]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)" >> /var/log/syslog
			echo "Logentries Test Event: dhclient: bound to x.3x.18.1x -- renewal in 41975 seconds."  >> /var/log/syslog
			echo "Logentries Test Event: mongodb main process (127x) terminated with status 100)" >> /var/log/syslog
			echo "Logentries Test Event: Out of Memory: Killed process 2592 (oracle)" >> /var/log/syslog
			echo "Logentries Test Event: CRON[29258]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)" >> /var/log/syslog
			echo "Logentries Test Event: CRON[29261]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)" >> /var/log/syslog
			echo "Logentries Test Event: kernel: imklog 5.8.6, log source = /proc/kmsg started." >> /var/log/syslog

			echo "Logentries Test Event: kernel: Kernel logging (proc) stopped." >> /var/log/syslog
			echo "Logentries Test Event: CRON[29258]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)" >> /var/log/syslog
			echo "Logentries Test Event: CRON[29261]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)" >> /var/log/syslog
			echo "Logentries Test Event: CRON[29252]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)" >> /var/log/syslog
			echo "Logentries Test Event: CRON[29222]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)" >> /var/log/syslog
			echo "Logentries Test Event: CRON[12345]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)" >> /var/log/syslog
			echo "Logentries Test Event: sshd[562x]: Invalid user ubuntu1 from 5x.x.x.5x " >> /var/log/syslog
			echo "Logentries Test Event: sshd[562x]: Invalid user ubuntu2 from 5x.x.x.5x" >> /var/log/syslog
			echo "Logentries Test Event: sshd[562x]: Invalid user root from 5x.x.x.5x" >> /var/log/syslog
			echo "Logentries Test Event: sshd[562x]: Invalid user admin from 5x.x.x.5x" >> /var/log/syslog
			echo "Logentries Test Event: CRON[29258]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)" >> /var/log/syslog
			echo "Logentries Test Event: CRON[29261]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)" >> /var/log/syslog
			echo "Logentries Test Event: CRON[29252]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)" >> /var/log/syslog
			echo "Logentries Test Event: sshd[564x]: Accepted publickey for ubuntu from 50.x.x.x port 22xxx ssh2" >> /var/log/syslog
			echo "Logentries Test Event: kernel: [    1.351600] rtc_cmos: probe of rtc_cmos failed with error -38" >> /var/log/syslog

			sleep 0.1
			i=$(( $i + 1 ))
		done
	fi

	printf "Creating Graphs.\n\n"
	$CURL -s $HEADER $CONTENT_HEADER $DATA "request=set_dashboard&log_key="$LOG_KEY"&dashboard=%7B%22widgets%22%3A%5B%7B%22descriptor_id%22%3A%22le.plot-pie-descriptor%22%2C%22options%22%3A%7B%22title%22%3A%22Process+Activity%22%2C%22tags_to_show%22%3A%5B%22Kernel+-+Process+Killed%22%2C%22Kernel+-+Process+Started%22%2C%22Kernel+-+Process+Stopped%22%2C%22Kernel+-+Process+Terminated%22%5D%2C%22position%22%3A%7B%22width%22%3A%221%22%2C%22height%22%3A%221%22%2C%22row%22%3A%221%22%2C%22column%22%3A%221%22%7D%7D%7D%5D%2C%22custom_widget_descriptors%22%3A%7B%7D%7D" $API
	$CURL -s $HEADER $CONTENT_HEADER $DATA "request=set_dashboard&log_key="$LOG_KEY"&dashboard=%7B%22widgets%22%3A%5B%7B%22descriptor_id%22%3A%22le.plot-pie-descriptor%22%2C%22options%22%3A%7B%22title%22%3A%22Process+Activity%22%2C%22tags_to_show%22%3A%5B%22Kernel+-+Process+Killed%22%2C%22Kernel+-+Process+Started%22%2C%22Kernel+-+Process+Stopped%22%2C%22Kernel+-+Process+Terminated%22%5D%2C%22position%22%3A%7B%22width%22%3A%221%22%2C%22height%22%3A%221%22%2C%22row%22%3A%221%22%2C%22column%22%3A%221%22%7D%7D%7D%2C%7B%22descriptor_id%22%3A%22le.plot-bars%22%2C%22options%22%3A%7B%22title%22%3A%22SSH+Access%22%2C%22tags_to_show%22%3A%5B%22User+Logged+In%22%2C%22Error%22%5D%2C%22position%22%3A%7B%22width%22%3A%221%22%2C%22height%22%3A%221%22%2C%22row%22%3A%221%22%2C%22column%22%3A%222%22%7D%7D%7D%5D%2C%22custom_widget_descriptors%22%3A%7B%7D%7D" $API
	$CURL -s $HEADER $CONTENT_HEADER $DATA "request=set_dashboard&log_key="$LOG_KEY"&dashboard=%7B%22widgets%22%3A%5B%7B%22descriptor_id%22%3A%22le.plot-pie-descriptor%22%2C%22options%22%3A%7B%22title%22%3A%22Process+Activity%22%2C%22tags_to_show%22%3A%5B%22Kernel+-+Process+Killed%22%2C%22Kernel+-+Process+Started%22%2C%22Kernel+-+Process+Stopped%22%2C%22Kernel+-+Process+Terminated%22%5D%2C%22position%22%3A%7B%22width%22%3A%221%22%2C%22height%22%3A%221%22%2C%22row%22%3A%221%22%2C%22column%22%3A%221%22%7D%7D%7D%2C%7B%22descriptor_id%22%3A%22le.plot-bars%22%2C%22options%22%3A%7B%22title%22%3A%22SSH+Access%22%2C%22tags_to_show%22%3A%5B%22User+Logged+In%22%2C%22Error%22%5D%2C%22position%22%3A%7B%22width%22%3A%221%22%2C%22height%22%3A%221%22%2C%22row%22%3A%221%22%2C%22column%22%3A%222%22%7D%7D%7D%2C%7B%22descriptor_id%22%3A%22le.event-text-widget%22%2C%22options%22%3A%7B%22title%22%3A%22Failed+Login+Attempts%22%2C%22event%22%3A%22Error%22%2C%22text%22%3A%22%22%2C%22value_display%22%3A%22Total+Events%22%2C%22position%22%3A%7B%22width%22%3A%221%22%2C%22height%22%3A%221%22%2C%22row%22%3A%221%22%2C%22column%22%3A%223%22%7D%7D%7D%5D%2C%22custom_widget_descriptors%22%3A%7B%7D%7D" $API
	printf "Finished creating default data.\n\n"
else
	printf "Unknown distribution. Please contact support@logentries.com with your system details\n\n"
fi
