#!/bin/bash

. vars

Scenario 'Listings'

$LE init --account-key=$ACCOUNT_KEY --host-key=$HOST_KEY
#e Initialized

Testcase 'List basic components'

$LE ls
#o apps
#o clusters
#o hostnames
#o hosts
#o logs
#o logtypes
#e Connecting to 127.0.0.1:8000
#e Domain request: GET /f720fe54-879a-11e4-81ac-277d856f873e/ None {}
#e List response: {"object": "rootlist", "list": [{"name": "logs", "key": ""}, {"name": "hosts", "key": ""}, {"name": "hostnames", "key": ""}, {"name": "apps", "key": ""}, {"name": "clusters", "key": ""}, {"name": "logtypes", "key": ""}], "response": "ok"}
#e 6 items


Testcase 'List hosts'
$LE ls hosts
#o Name1
#o Name2
#e Connecting to 127.0.0.1:8000
#e Domain request: GET /f720fe54-879a-11e4-81ac-277d856f873e/hosts None {}
#e List response: {"object": "hostlist", "list": [{"distver": "wheezy", "c": 1315863111149, "hostname": "0.example.com", "name": "Name1", "distname": "Debian", "object": "host", "key": "41ae887a-284a-4d78-91fe-56485b076148"}, {"distver": "jessie", "c": 1385398282448, "hostname": "1.example.com", "name": "Name2", "distname": "Debian", "object": "host", "key": "86707421-6a05-4c70-9034-e5e30b6a1a44"}], "response": "ok"}
#e 2 hosts

Testcase 'List host'
$LE ls hosts/Name1
#o name = Name1
#o hostname = 0.example.com
#o key = 41ae887a-284a-4d78-91fe-56485b076148
#o distribution = Debian
#o distver = wheezy
#e Connecting to 127.0.0.1:8000
#e Domain request: GET /f720fe54-879a-11e4-81ac-277d856f873e/hosts/Name1 None {}
#e List response: {"distver": "wheezy", "c": 1315863111149, "object": "host", "name": "Name1", "distname": "Debian", "hostname": "0.example.com", "key": "41ae887a-284a-4d78-91fe-56485b076148", "response": "ok"}

Testcase 'List logs in a host'
$LE ls hosts/Name1/
#o Log name 0
#o Log name 1
#e Connecting to 127.0.0.1:8000
#e Domain request: GET /f720fe54-879a-11e4-81ac-277d856f873e/hosts/Name1/ None {}
#e List response: {"object": "loglist", "list": [{"name": "Log name 0", "key": "400da462-36fa-48f4-bb4e-87f96ad34e8a", "created": 1414611930412, "retention": -1, "follow": "true", "object": "log", "type": "agent", "filename": "$TMP/example.log"}, {"token": "120fb800-94c0-446a-be28-cfbbc36b52eb", "name": "Log name 1", "key": "ee0489cc-41ce-41cf-9bb6-4cdf5e5acf32", "created": 1418775058756, "retention": -1, "follow": "false", "object": "log", "type": "token", "filename": "$TMP/example2.log"}], "response": "ok"}
#e 2 logs

Testcase 'List log in a host'
$LE ls hosts/Name1/Log\ name\ 0
#o name = Log name 0
#o filename = $TMP/example.log
#o key = 400da462-36fa-48f4-bb4e-87f96ad34e8a
#o type = agent
#o follow = true
#e Connecting to 127.0.0.1:8000
#e Domain request: GET /f720fe54-879a-11e4-81ac-277d856f873e/hosts/Name1/Log%20name%200 None {}
#e List response: {"name": "Log name 0", "created": 1414611930412, "object": "log", "filename": "$TMP/example.log", "key": "400da462-36fa-48f4-bb4e-87f96ad34e8a", "follow": "true", "type": "agent", "response": "ok", "retention": -1}

