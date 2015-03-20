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


Scenario 'Re-init with locally configured logset'

$LE init --account-key=$ACCOUNT_KEY
#e Initialized

cat $CONFIG
#o [Main]
#o user-key = f720fe54-879a-11e4-81ac-277d856f873e
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

tee >>$CONFIG <<EOF
[syslog]
path=/var/log/syslog
token=629cc7e9-3344-4cef-b364-7fb6baeb74f2

[Log name 1]
path=/var/log/messages
logset=Name2
EOF

$LE reinit --pull-server-side-config=False
#e Connecting to 127.0.0.1:8081
#e Domain request: POST / user_key=f720fe54-879a-11e4-81ac-277d856f873e&load_hosts=true&request=get_user&load_logs=true {'Content-Type': 'application/x-www-form-urlencoded'}
#e Domain response: "{"hosts": [{"distver": "wheezy", "c": 1315863111149, "hostname": "0.example.com", "name": "Name1", "distname": "Debian", "object": "host", "key": "41ae887a-284a-4d78-91fe-56485b076148", "logs": [{"name": "Log name 0", "key": "400da462-36fa-48f4-bb4e-87f96ad34e8a", "created": 1414611930412, "retention": -1, "follow": "true", "object": "log", "type": "agent", "filename": "%CWD%/example.log"}]}, {"distver": "jessie", "c": 1385398282448, "hostname": "1.example.com", "name": "Name2", "distname": "Debian", "object": "host", "key": "86707421-6a05-4c70-9034-e5e30b6a1a44", "logs": [{"token": "120fb800-94c0-446a-be28-cfbbc36b52eb", "name": "Log name 1", "key": "ee0489cc-41ce-41cf-9bb6-4cdf5e5acf32", "created": 1418775058756, "retention": -1, "follow": "false", "object": "log", "type": "token", "filename": "%CWD%/example2.log"}]}], "response": "ok"}"
#e Reinitialized

cat $CONFIG
#o [Main]
#o user-key = f720fe54-879a-11e4-81ac-277d856f873e
#o pull-server-side-config = False
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
#o [Log name 1]
#o token = 120fb800-94c0-446a-be28-cfbbc36b52eb
#o path = /var/log/messages
#o logset = Name2
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
