#!/bin/bash

. vars

Scenario 'V1 metrics are deprecated'

Testcase 'After the init command V1 metrics are set to False'

$LE init --account-key=$ACCOUNT_KEY --host-key=$HOST_KEY --hostname myhost
#e Initialized

cat "$CONFIG"
#o [Main]
#o user-key = f720fe54-879a-11e4-81ac-277d856f873e
#o agent-key = 41ae887a-284a-4d78-91fe-56485b076148
#o v1_metrics = False
#o hostname = myhost
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

Testcase 'When v1_metrics is set to False, V1 metrics are not collected'


echo 'pull-server-side-config = False' >>"$CONFIG" # Disable preconfigured logs, not needed
$LE --local --debug monitor &
LE_PID=$!
#e Configuration files loaded: sandbox_config
#e V1 metrics disabled

sleep 1s
kill $LE_PID
wait $LE_PID 2>/dev/null || true


Testcase 'When v1_metrics is set to True, V1 metrics are collected'


echo 'v1_metrics = True' >>"$CONFIG"

$LE --local --debug monitor &
LE_PID=$!
#e Configuration files loaded: sandbox_config
#e Enabling V1 metrics

sleep 1s
kill $LE_PID
wait $LE_PID 2>/dev/null || true


Testcase 'When v1_metrics is missing, V1 metrics are collected'

# Remove all occurrences of v1_metrics
sed -i 's/v1_metrics.*//g' "$CONFIG"

$LE --local --debug monitor &
LE_PID=$!
#e Configuration files loaded: sandbox_config
#e Enabling V1 metrics

sleep 1s
kill $LE_PID
wait $LE_PID 2>/dev/null || true


Scenario 'Explicitly enabling V1 metrics as a part of init command'


Testcase 'After the init command with --legacy_v1_metrics V1 metrics are set to True'

$LE init --legacy_v1_metrics --account-key=$ACCOUNT_KEY --host-key=$HOST_KEY --hostname myhost
#e Initialized

cat "$CONFIG"
#o [Main]
#o user-key = f720fe54-879a-11e4-81ac-277d856f873e
#o agent-key = 41ae887a-284a-4d78-91fe-56485b076148
#o v1_metrics = True
#o hostname = myhost
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
