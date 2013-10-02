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

VERSION="1.0.4"

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

REDHAT_REPO_CONF="/etc/yum.repos.d/logentries.repo"
REDHAT_UPDATE="yum update -y"
REDHAT_AGENT_INSTALL="yum install logentries -q -y"
REDHAT_PROCTITLE_INSTALL="yum install python-setproctitle -q -y"
REDHAT_DAEMON_INSTALL="yum install logentries-daemon -q -y"

CONFIG_DELETE_CMD="rm /etc/le/config"
REGISTER_CMD="le register"
FOLLOW_CMD="le follow"
LOGGER_CMD="logger -t LogentriesTest Test Message Sent By LogentriesAgent"
DAEMON_RESTART_CMD="service logentries restart"
FOUND=0
AGENT_NOT_FOUND="The agent was not found after installation.\n Please contact support@logentries.com\n"
SET_ACCOUNT_KEY="--account-key="

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

	printf "Updating packages...(This may take a few minutes if you have alot of updates)\n"
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

	$DAEMON_RESTART_CMD >/tmp/logentriesDebug 2>&1

	sleep 1

	printf "**** Install Complete! ****\n\n"
	printf "The Logentries agent is now monitoring /var/log/syslog by default\n"
	printf "This install script can also monitor the following files by default..\n"

	for x in "${LOGS_TO_FOLLOW[@]}"
	do
		echo $x
	done
	read -p "Would you like to monitor these also?..(y) or (n): "
	if [[ $REPLY =~ ^[Yy]$ ]];then
		for y in "${LOGS_TO_FOLLOW[@]}"
		do
			if [ -f $y ]; then
				$FOLLOW_CMD	$y >/tmp/LogentriesDebug 2>&1
				printf "Will monitor $y\n"
			fi
		done	
	fi
	echo ""	
	printf "If you would like to monitor more files, simply run this command as root, 'le follow filepath', e.g. 'le follow /var/log/auth.log'\n\n"
	printf "And be sure to restart the agent service for new files to take effect, you can do this with 'sudo service logentries restart'\n"
	printf "On some older systems, the command is: sudo /etc/init.d/logentries restart\n\n"
	printf "For a full list of commands, run 'le --help' in the terminal.\n\n"
	printf "********************************\n\n"

	printf "We will now send some sample events to your new Logentries account. This will take about 10 seconds\n\n"
	if hash logger 2>/dev/null; then
		i=1
		while [ $i -le 100 ]
		do
			$LOGGER_CMD $i of 100
			printf "."
			sleep 0.1
			i=$(( $i + 1 ))
		done
	else	
		i=1
		while [ $i -le 100 ]
		do
			echo "Logentries Agent Test Event $i of 100" >> /var/log/syslog
			printf "."
			sleep 0.1
			i=$(( $i + 1 ))
		done
	fi
	printf "\n"
else
	printf "Unknown distribution. Please contact support@logentries.com with your system details\n\n"
fi
