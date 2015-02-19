#!/bin/bash

. vars

Scenario 'Configuration with basic options'

$LE init --account-key=$ACCOUNT_KEY --host-key=$HOST_KEY
#e Initialized

cat $CONFIG
#o [Main]
#o user-key = f720fe54-879a-11e4-81ac-277d856f873e
#o agent-key = 41ae887a-284a-4d78-91fe-56485b076148
#o metrics-mem = system
#o metrics-token = 
#o metrics-disk = sum
#o metrics-swap = system
#o metrics-space = /
#o metrics-vcpu = 
#o metrics-net = sum
#o metrics-interval = 5s
#o metrics-cpu = system
#o


Scenario 'Configuration with other options'

$LE init --account-key=$ACCOUNT_KEY --host-key=$HOST_KEY --suppress-ssl --datahub "localhost:5000" --hostname "abarakedabra"
#e Initialized

cat $CONFIG
#o [Main]
#o user-key = f720fe54-879a-11e4-81ac-277d856f873e
#o agent-key = 41ae887a-284a-4d78-91fe-56485b076148
#o hostname = abarakedabra
#o suppress_ssl = True
#o datahub = localhost:5000
#o metrics-mem = system
#o metrics-token = 
#o metrics-disk = sum
#o metrics-swap = system
#o metrics-space = /
#o metrics-vcpu = 
#o metrics-net = sum
#o metrics-interval = 5s
#o metrics-cpu = system
#o

Scenario 'Re-init with lcoally configured log'

$LE reinit --pull-server-side-config=False --suppress-ssl --datahub="127.0.0.1:10000" --hostname "abarakedabra"
#e Reinitialized

tee >>$CONFIG <<EOF
[syslog]
path=/var/log/syslog
token=629cc7e9-3344-4cef-b364-7fb6baeb74f2
EOF

$LE reinit --pull-server-side-config=False --suppress-ssl --datahub="127.0.0.1:10000"
#e Reinitialized

cat $CONFIG
#o [Main]
#o hostname = abarakedabra
#o suppress_ssl = True
#o pull-server-side-config = False
#o datahub = 127.0.0.1:10000
#o metrics-mem = system
#o metrics-token = 
#o metrics-disk = sum
#o metrics-swap = system
#o metrics-space = /
#o metrics-vcpu = 
#o metrics-net = sum
#o metrics-interval = 5s
#o metrics-cpu = system
#o
#o [syslog]
#o token = 629cc7e9-3344-4cef-b364-7fb6baeb74f2
#o path = /var/log/syslog
#o

