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

VERSION="1.0.0"

# Need root to run this script
if [ "$(id -u)" != "0" ] 
then
	echo "Please run this install script as root."
	echo "Usage: sudo bash install.sh"
	exit 1
fi

KEY_CMD="gpg --homedir /root/.gnupg --keyserver pgp.mit.edu --recv-keys C43C79AD && gpg -a --export C43C79AD | apt-key add -"

DEBIAN_REPO_CONF="/etc/apt/sources.list.d/logentries.list"
DEBIAN_UPDATE="apt-get update -qq -y"
DEBIAN_AGENT_INSTALL="apt-get install logentries -qq -y"
DEBIAN_PROCTITLE_INSTALL="apt-get install python-setproctitle -qq -y"
DEBIAN_DAEMON_INSTALL="apt-get install logentries-daemon -qq -y"

REDHAT_REPO_CONF="/etc/yum.repos.d/logentries.repo"
REDHAT_UPDATE="yum update -q -y"
REDHAT_AGENT_INSTALL="yum install logentries -q -y"
REDHAT_PROCTITLE_INSTALL="yum install python-setproctitle -q -y"
REDHAT_DAEMON_INSTALL="yum install logentries-daemon -q -y"

if hash lsb_release 2>/dev/null; then
	CODENAME=$(lsb_release -c | sed 's/Codename://' | tr -d '[:space:]')
	RELEASE=$(lsb_release -r | sed 's/Release://' | tr -d '[:space:]')
fi

REGISTER_CMD="le register"
FOUND=0

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

	# Prompt the user for their Logentries credentials and register the agent
	$REGISTER_CMD

	printf "Installing logentries daemon package...\n"
	$REDHAT_DAEMON_INSTALL

	FOUND=1

elif [ -f /etc/debian_version ]; then
	# Debian/Ubuntu
	echo "deb http://rep.logentries.com/ ${CODENAME} main" > $DEBIAN_REPO_CONF

	$KEY_CMD >/tmp/logentriesDebug 2>&1

	printf "Updating packages...(This may take a few minutes if you have alot of updates)\n"
	$DEBIAN_UPDATE >/tmp/logentriesDebug 2>&1

	printf "Installing logentries package...\n"
	$DEBIAN_AGENT_INSTALL 
	# Try and install the python-setproctitle package on certain distro's
	$DEBIAN_PROCTITLE_INSTALL >/tmp/logentriesDebug 2>&1
	# Prompt the user for their Logentries credentials and register the agent
	$REGISTER_CMD

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

	# Prompt the user for their Logentries credentials and register the agent
	$REGISTER_CMD
	
	printf "Installing logentries daemon package...\n"
	$REDHAT_DAEMON_INSTALL

	FOUND=1
fi

if [ $FOUND == "1" ]; then 
	printf "Install Complete!\n"
	printf "Tell the agent to follow files with the 'le follow' command, e.g.  'le follow /var/log/syslog'\n"
	printf "After you tell the agent to follow new files, you must restart the logentries service: service logentries restart\n"
else
	printf "Unknown distribution. Please contact support@logentries.com with your system details\n"
fi
