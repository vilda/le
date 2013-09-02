#!/bin/sh

echo "Logentries Agent Installer for Joyent SmartOS\n"

if [ ! -x "/opt/local/bin/python2.7" ]; then
	echo "You need to install python2.7 package to run this agent, Try using 'pkgin install python27'.\n"
  exit 0
fi

#Create directories
mkdir -p /opt/local/lib/svc/method
mkdir -p /opt/local/lib/svc/manifest/system

echo "Downloading files..."
#Download files
wget --no-check-certificate -q -O /opt/local/bin/le https://raw.github.com/logentries/le/master/le
wget --no-check-certificate -q -O /opt/local/lib/svc/method/svc-logentries https://raw.github.com/logentries/le/master/install/smartos/svc-logentries
wget --no-check-certificate -q -O /opt/local/lib/svc/manifest/system/logentries.xml https://raw.github.com/logentries/le/master/install/smartos/logentries.xml

#Make executables
chmod +x /opt/local/bin/le
chmod +x /opt/local/lib/svc/method/svc-logentries

echo "Adding logentries agent to svcadm  (Services)"
#Add logentries agent to the services
svccfg import /opt/local/lib/svc/manifest/system/logentries.xml

echo "Installation Complete\n"
