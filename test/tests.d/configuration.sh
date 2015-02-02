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

