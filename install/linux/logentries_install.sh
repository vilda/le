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
DEBIAN_UPDATE="apt-get update"
DEBIAN_AGENT_INSTALL="apt-get install logentries -qq -y"
DEBIAN_PROCTITLE_INSTALL="apt-get install python-setproctitle -qq -y"
DEBIAN_DAEMON_INSTALL="apt-get install logentries-daemon -qq -y"
DEBIAN_CURL_INSTALL="apt-get install curl -y"

REDHAT_REPO_CONF="/etc/yum.repos.d/logentries.repo"
REDHAT_AGENT_INSTALL="yum install logentries -q -y"
REDHAT_PROCTITLE_INSTALL="yum install python-setproctitle -q -y"
REDHAT_DAEMON_INSTALL="yum install logentries-daemon -q -y"
REDHAT_CURL_INSTALL="yum install curl curl-devel -y"

GENTOO_PORTAGE="/usr/portage/local"
GENTOO_OVERLAY="app-admin/le"
GENTOO_REPO="http://rep.logentries.com/gentoo/portage/app-admin/le"
GENTOO_AGENT_INSTALL="emerge ${GENTOO_OVERLAY}"

CONFIG_DELETE_CMD="rm /etc/le/config"
REGISTER_CMD="le register"
FOLLOW_CMD="le follow"
LOGGER_CMD="logger -t LogentriesTest Test Message Sent By LogentriesAgent"
DAEMON_RESTART_CMD="if which service &>/dev/null ; then service logentries restart ; else /etc/init.d/logentries restart ; fi"
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

WGET="wget --quiet -r -np -nd"

declare -a LOGS_TO_FOLLOW=(
/var/log/syslog
/var/log/auth.log
/var/log/messages
/var/log/secure
/var/log/dmesg
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
/var/log/wtmp
/var/log/faillog);

SYSLOG=messages
LOGFILE=/tmp/LogentriesDebug

if [ -f /etc/le/config ]; then
	printf "\n***** WARNING *****\n"
	printf "It looks like you already have the Logentries agent registered on this machine\n"
	read -p "Are you sure you want to clear your existing settings and continue with the installation? (y) or (n): "
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		$CONFIG_DELETE_CMD
		printf "OK\n"
	else
		echo ""
		printf "Exiting install script\n"
		exit 0
	fi
fi

printf "\n"

# Check if curl is installed, if not, mark it for installation
if hash curl 2>/dev/null;then
	INSTALL_CURL=0
else
	INSTALL_CURL=1
fi

printf "***** Step 1 of 4 - Beginning Logentries Installation *****\n"

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

	printf "Installing logentries package...\n"
	$REDHAT_AGENT_INSTALL >$LOGFILE 2>&1

	# try and install python-setproctitle
	$REDHAT_PROCTITLE_INSTALL >$LOGFILE 2>&1

	# Check for agent executable
	if [ ! -f /usr/bin/le ];then
		echo $AGENT_NOT_FOUND
		exit 1
	fi

	# Check if curl is marked for install
	if [ $INSTALL_CURL == "1" ]; then
		$REDHAT_CURL_INSTALL
	fi


	echo ""
	printf "***** Step 2 of 4 - Login *****\n"

	# Prompt the user for their Logentries credentials and register the agent
	if [[ -z "$LE_ACCOUNT_KEY" ]];then
		$REGISTER_CMD
	else
		printf "Account Key found, registering automatically...\n"
		$REGISTER_CMD $SET_ACCOUNT_KEY$LE_ACCOUNT_KEY
	fi


	printf "Installing logentries daemon package...\n"
	$REDHAT_DAEMON_INSTALL >$LOGFILE 2>&1

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

	$KEY_CMD_MIT >$LOGFILE 2>&1

	if [ "$?" != "0" ]; then
		echo "MIT keyserver not working, fall back to ubuntu keyserver" >>$LOGFILE
		# Try different keyserver
		$KEY_CMD_UBUNTU >$LOGFILE 2>&1
	fi

	$KEY_CMD_EXPORT >/tmp/le.key
	$KEY_CMD_COMPLETE >$LOGFILE 2>&1
	$KEY_CMD_CLEAN

	printf "Updating packages...(This may take a few minutes if you have a lot of updates)\n"
	$DEBIAN_UPDATE >$LOGFILE 2>&1

	printf "Installing logentries package...\n"
	$DEBIAN_AGENT_INSTALL >$LOGFILE 2>&1
	# Try and install the python-setproctitle package on certain distro's
	$DEBIAN_PROCTITLE_INSTALL >$LOGFILE 2>&1

	# Check if agent executable exists before trying to register
	if [ ! -f /usr/bin/le ];then
		echo $AGENT_NOT_FOUND
		exit 1
	fi

	# Check if curl is marked for install
	if [ $INSTALL_CURL == "1" ]; then
		$DEBIAN_CURL_INSTALL
	fi

	printf "\n\n"
	printf "***** Step 2 of 4 - Login *****\n"

	# Prompt the user for their Logentries credentials and register the agent
	if [[ -z "$LE_ACCOUNT_KEY" ]];then
		$REGISTER_CMD
	else
		printf "Account Key found, registering automatically...\n"
		$REGISTER_CMD $SET_ACCOUNT_KEY$LE_ACCOUNT_KEY
	fi

	printf "Installing logentries daemon package...\n"
	$DEBIAN_DAEMON_INSTALL >$LOGFILE 2>&1

	FOUND=1
        SYSLOG=syslog

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

	printf "Installing logentries package...\n"
	$REDHAT_AGENT_INSTALL >$LOGFILE 2>&1

	# try and install python-setproctitle
	$REDHAT_PROCTITLE_INSTALL >$LOGFILE 2>&1

	# Check that agent executable exists before trying to register
	if [ ! -f /usr/bin/le ];then
		echo $AGENT_NOT_FOUND
	fi

	echo "\n"
	printf "***** Step 2 of 4 - Login *****\n"

	# Prompt the user for their Logentries credentials and register the agent
	if [[ -z "$LE_ACCOUNT_KEY" ]];then
		$REGISTER_CMD
	else
		printf "Account Key found, registering automatically...\n"
		$REGISTER_CMD $SET_ACCOUNT_KEY$LE_ACCOUNT_KEY
	fi

	printf "Installing logentries daemon package...\n"
	$REDHAT_DAEMON_INSTALL >$LOGFILE 2>&1

	FOUND=1

elif [ -f /etc/gentoo-release ] ; then

        if [ -d ${GENTOO_PORTAGE} ] ; then
            rm -fr ${GENTOO_PORTAGE}
        fi
        mkdir -p ${GENTOO_PORTAGE}/profiles ${GENTOO_PORTAGE}/${GENTOO_OVERLAY}

        echo 'le' > ${GENTOO_PORTAGE}/profiles/repo_name
        $WGET -A "*.ebuild","Manifest","logentries" -P ${GENTOO_PORTAGE}/${GENTOO_OVERLAY} ${GENTOO_REPO}

        for makeconf in /etc/portage/make.conf /etc/make.conf ; do
            if [ -f $makeconf ] && [ -z "`grep \"${GENTOO_PORTAGE}\" $makeconf`" ] ; then
                echo "PORTDIR_OVERLAY=\"\${PORTDIR_OVERLAY} ${GENTOO_PORTAGE}\"" >> $makeconf
                break
            fi
        done

	printf "Installing logentries package...\n"
	$GENTOO_AGENT_INSTALL &> $LOGFILE

	# Check that agent executable exists before trying to register
	if [ ! -f /usr/bin/le ] ; then
		echo $AGENT_NOT_FOUND
	fi

	echo "\n"
	printf "***** Step 2 of 4 - Login *****\n"

	# Prompt the user for their Logentries credentials and register the agent
	if [[ -z "$LE_ACCOUNT_KEY" ]];then
		$REGISTER_CMD
	else
		printf "Account Key found, registering automatically...\n"
		$REGISTER_CMD $SET_ACCOUNT_KEY$LE_ACCOUNT_KEY
	fi

	FOUND=1
fi

if [ $FOUND == "1" ]; then
	printf "Logentries Install Complete\n\n"

        logfile=/var/log/${SYSLOG}

	if [ -f $logfile ]; then
		$FOLLOW_CMD $logfile >$LOGFILE 2>&1
		printf "The Logentries agent is now monitoring $logfile\n"
	fi

	printf "\n\n"

	printf "***** Step 3 of 4 - Additional Logs *****\n"

	FILES_FOUND=0

	for x in "${LOGS_TO_FOLLOW[@]}"
	do
		if [ -f $x ]; then
			let FILES_FOUND=FILES_FOUND+1
		fi
	done

	printf "$FILES_FOUND additional logs found.\n"
	read -p "Would you like to monitor all of these too? (n) allows you to choose individual logs...(y) or (n): "
	printf "\n\n"
	if [[ $REPLY =~ ^[Yy]$ ]];then
		printf "Monitoring all logs\n"
		for j in "${LOGS_TO_FOLLOW[@]}"
		do
			$FOLLOW_CMD $j >$LOGFILE 2>&1
			printf "."
		done
		printf "\n"
	else	
		for j in "${LOGS_TO_FOLLOW[@]}"
		do
			if [ -f $j ]; then
				read -p "Would you like to monitor $j ?..(y) or (n): "
				if [[ $REPLY =~ ^[Yy]$ ]]; then
					$FOLLOW_CMD $j >$LOGFILE 2>&1
				fi
			fi
		done
	fi
	eval $DAEMON_RESTART_CMD >$LOGFILE 2>&1
	printf "\n\n"

	printf "***** Step 4 of 4 - Sample Data *****\n"
	read -p "Would you like us to seed some default log entries, Tags & Graphs in your ${SYSLOG} log?..(y) or (n): "
	printf "\n"
	if [[ $REPLY =~ ^[Yy]$ ]];then

		printf "We will now send some sample events to your new Logentries account. This will take about 10 seconds\n\n"
		if [ ! -f /etc/le/config ];then
			printf "Logentries config not found, unable to continue with seeding data.\n"
			exit 0
		fi
		USER_KEY_LINE=$(sed -n '2p' /etc/le/config)
		USER_KEY=${USER_KEY_LINE#*= }
		LE_COMMAND=$(le ls /hosts/`python -c "import socket; print socket.getfqdn().split('.')[0]"`/${SYSLOG} | grep key)
		LOG_KEY=${LE_COMMAND#key = }

		printf "Creating Events & Tags \n"
		$CURL -O "https://raw.github.com/logentries/le/master/install/linux/seeding.py"
		TAG_ID=$(python seeding.py createEvent $USER_KEY $LOG_KEY)

		echo "Seeding data, this can take up to 15 seconds"
		if hash logger 2>/dev/null; then

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

		else
			echo "Logentries Test Event: CRON[29258]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)" >> $logfile
			echo "Logentries Test Event: CRON[29261]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)" >> $logfile
			echo "Logentries Test Event: CRON[29252]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)" >> $logfile
			echo "Logentries Test Event: CRON[29222]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)" >> $logfile
			echo "Logentries Test Event: CRON[12345]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)" >> $logfile
			echo "Logentries Test Event: dhclient: bound to x.3x.18.1x -- renewal in 41975 seconds."  >> $logfile
			echo "Logentries Test Event: mongodb main process (127x) terminated with status 100)" >> $logfile
			echo "Logentries Test Event: Out of Memory: Killed process 2592 (oracle)" >> $logfile
			echo "Logentries Test Event: CRON[29258]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)" >> $logfile
			echo "Logentries Test Event: CRON[29261]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)" >> $logfile
			echo "Logentries Test Event: kernel: imklog 5.8.6, log source = /proc/kmsg started." >> $logfile

			echo "Logentries Test Event: kernel: Kernel logging (proc) stopped." >> $logfile
			echo "Logentries Test Event: CRON[29258]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)" >> $logfile
			echo "Logentries Test Event: CRON[29261]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)" >> $logfile
			echo "Logentries Test Event: CRON[29252]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)" >> $logfile
			echo "Logentries Test Event: CRON[29222]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)" >> $logfile
			echo "Logentries Test Event: CRON[12345]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)" >> $logfile
			echo "Logentries Test Event: sshd[562x]: Invalid user ubuntu1 from 5x.x.x.5x " >> $logfile
			echo "Logentries Test Event: sshd[562x]: Invalid user ubuntu2 from 5x.x.x.5x" >> $logfile
			echo "Logentries Test Event: sshd[562x]: Invalid user root from 5x.x.x.5x" >> $logfile
			echo "Logentries Test Event: sshd[562x]: Invalid user admin from 5x.x.x.5x" >> $logfile
			echo "Logentries Test Event: CRON[29258]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)" >> $logfile
			echo "Logentries Test Event: CRON[29261]: (root) CMD (   cd / && run-parts -le -report /etc/cron.hourly)" >> $logfile
			echo "Logentries Test Event: CRON[29252]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)" >> $logfile
			echo "Logentries Test Event: sshd[564x]: Accepted publickey for ubuntu from 50.x.x.x port 22xxx ssh2" >> $logfile
			echo "Logentries Test Event: kernel: [    1.351600] rtc_cmos: probe of rtc_cmos failed with error -38" >> $logfile

		fi

		printf "Creating Graphs.\n\n"
		$CURL -s $HEADER $CONTENT_HEADER $DATA "request=set_dashboard&log_key="$LOG_KEY"&dashboard=%7B%22widgets%22%3A%5B%7B%22descriptor_id%22%3A%22le.plot-pie-descriptor%22%2C%22options%22%3A%7B%22title%22%3A%22Process+Activity%22%2C%22tags_to_show%22%3A%5B%22Kernel+-+Process+Killed%22%2C%22Kernel+-+Process+Started%22%2C%22Kernel+-+Process+Terminated%22%5D%2C%22position%22%3A%7B%22width%22%3A%222%22%2C%22height%22%3A%222%22%2C%22row%22%3A%222%22%2C%22column%22%3A%221%22%7D%7D%7D%2C%7B%22descriptor_id%22%3A%22le.event-text-widget%22%2C%22options%22%3A%7B%22title%22%3A%22Failed+Login+Attempts%22%2C%22event%22%3A%22Error%22%2C%22text%22%3A%22%22%2C%22value_display%22%3A%22Total+Events%22%2C%22position%22%3A%7B%22width%22%3A%222%22%2C%22height%22%3A%222%22%2C%22row%22%3A%222%22%2C%22column%22%3A%223%22%7D%7D%7D%2C%7B%22descriptor_id%22%3A%22le.plot-timeline%22%2C%22options%22%3A%7B%22title%22%3A%22User+Logins+Vs+Failed+Logins%22%2C%22tags_to_show%22%3A%5B%22Invalid+User+Login+attempt%22%2C%22User+Logged+In%22%5D%2C%22style%22%3A%5B%5D%2C%22position%22%3A%7B%22width%22%3A%224%22%2C%22height%22%3A%221%22%2C%22row%22%3A%221%22%2C%22column%22%3A%221%22%7D%7D%7D%5D%2C%22custom_widget_descriptors%22%3A%7B%7D%7D" $API >$LOGFILE 2>&1
		$CURL -s $HEADER $CONTENT_HEADER $DATA "request=set_dashboard&log_key="$LOG_KEY"&dashboard=%7B%22widgets%22%3A%5B%7B%22descriptor_id%22%3A%22le.plot-pie-descriptor%22%2C%22options%22%3A%7B%22title%22%3A%22Process+Activity%22%2C%22tags_to_show%22%3A%5B%22Kernel+-+Process+Killed%22%2C%22Kernel+-+Process+Started%22%2C%22Kernel+-+Process+Terminated%22%5D%2C%22position%22%3A%7B%22width%22%3A%222%22%2C%22height%22%3A%222%22%2C%22row%22%3A%222%22%2C%22column%22%3A%221%22%7D%7D%7D%2C%7B%22descriptor_id%22%3A%22le.event-text-widget%22%2C%22options%22%3A%7B%22title%22%3A%22Failed+Login+Attempts%22%2C%22event%22%3A%22Error%22%2C%22text%22%3A%22%22%2C%22value_display%22%3A%22Total+Events%22%2C%22position%22%3A%7B%22width%22%3A%222%22%2C%22height%22%3A%222%22%2C%22row%22%3A%222%22%2C%22column%22%3A%223%22%7D%7D%7D%2C%7B%22descriptor_id%22%3A%22le.plot-timeline%22%2C%22options%22%3A%7B%22title%22%3A%22User+Logins+Vs+Failed+Logins%22%2C%22tags_to_show%22%3A%5B%22Invalid+User+Login+attempt%22%2C%22User+Logged+In%22%5D%2C%22style%22%3A%5B%5D%2C%22position%22%3A%7B%22width%22%3A%224%22%2C%22height%22%3A%221%22%2C%22row%22%3A%221%22%2C%22column%22%3A%221%22%7D%7D%7D%5D%2C%22custom_widget_descriptors%22%3A%7B%7D%7D" $API >$LOGFILE 2>&1
		$CURL -s $HEADER $CONTENT_HEADER $DATA "request=set_dashboard&log_key="$LOG_KEY"&dashboard=%7B%22widgets%22%3A%5B%7B%22descriptor_id%22%3A%22le.plot-pie-descriptor%22%2C%22options%22%3A%7B%22title%22%3A%22Process+Activity%22%2C%22tags_to_show%22%3A%5B%22Kernel+-+Process+Killed%22%2C%22Kernel+-+Process+Started%22%2C%22Kernel+-+Process+Terminated%22%5D%2C%22position%22%3A%7B%22width%22%3A%222%22%2C%22height%22%3A%222%22%2C%22row%22%3A%222%22%2C%22column%22%3A%221%22%7D%7D%7D%2C%7B%22descriptor_id%22%3A%22le.event-text-widget%22%2C%22options%22%3A%7B%22title%22%3A%22Failed+Login+Attempts%22%2C%22event%22%3A%22Error%22%2C%22text%22%3A%22%22%2C%22value_display%22%3A%22Total+Events%22%2C%22position%22%3A%7B%22width%22%3A%222%22%2C%22height%22%3A%222%22%2C%22row%22%3A%222%22%2C%22column%22%3A%223%22%7D%7D%7D%2C%7B%22descriptor_id%22%3A%22le.plot-timeline%22%2C%22options%22%3A%7B%22title%22%3A%22User+Logins+Vs+Failed+Logins%22%2C%22tags_to_show%22%3A%5B%22Invalid+User+Login+attempt%22%2C%22User+Logged+In%22%5D%2C%22style%22%3A%5B%5D%2C%22position%22%3A%7B%22width%22%3A%224%22%2C%22height%22%3A%221%22%2C%22row%22%3A%221%22%2C%22column%22%3A%221%22%7D%7D%7D%5D%2C%22custom_widget_descriptors%22%3A%7B%7D%7D" $API >$LOGFILE 2>&1
		printf "\n"
		printf "Finished creating default data.\n\n"
		printf "***** Install Complete! *****\n"
		printf "Please note that it may take a few moments for the log data to show in your account.\n\n"
		printf "This will be automatically detected within 60 seconds.\n"
	else
		printf "***** Install Complete! *****\n"
		printf "Please note that it may take a few moments for the log data to show in your account.\n\n"
	fi


else
	printf "Unknown distribution. Please contact support@logentries.com with your system details\n\n"
fi
