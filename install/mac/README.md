Agent installer for OS X
========================

Installation
------------

To install, download `install.sh` and run:

```shell
$ curl -O https://raw.github.com/m0wfo/le/master/install/mac/install.sh
$ chmod +x install.sh
$ sudo ./install.sh
```

Removal
-------

Stop and remove the daemon:

```shell
$ sudo launchctl unload /Library/LaunchDaemons/com.logentries.agent.plist
$ sudo rm /Library/LaunchDaemons/com.logentries.agent.plist
```

Then remove the executable:

```shell
$ sudo rm /usr/local/bin/le
```
