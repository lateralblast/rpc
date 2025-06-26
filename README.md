![alt tag](rpc.gif)

RPC
===

Remote Plug Control

Version: 0.1.3

Python Script to control Tapo (and others in the future) Plugs

License
-------

This software is licensed as CC-BA (Creative Commons By Attrbution)

http://creativecommons.org/licenses/by/4.0/legalcode


Requirements
------------

To support updated firmware one of the updated forks of TapoP100 is required,
e.g. https://github.com/almottier/TapoP100

The script will try to install this, but it can be installed as follows:

```
pip install git+https://github.com/almottier/TapoP100.git@main
```

Modules required:

- terminaltables
- importlib
- argparse
- pprint
- PyP100
- json
- stat
- sys
- os
- re

Todo
----

Things to be done:

- Add more functions related to usage information from power monitoring enabled plugs
- Add more types/brands of networked power devices (e.g. APC etc)
- More querying functions

Usage
-----

Get help:

```
./rpc.py --help
usage: rpc.py [-h] [--plug PLUG] [--user USER] [--pass PASS] [--turn TURN] [--type TYPE] [--secs SECS]
              [--data DATA] [--file FILE] [--item ITEM] [--verbose] [--version] [--toggle] [--pylint]
              [--tables] [--usage] [--dump] [--mask] [--name] [--info] [--save] [--off] [--on]

options:
  -h, --help   show this help message and exit
  --plug PLUG
  --user USER
  --pass PASS
  --turn TURN
  --type TYPE
  --secs SECS
  --data DATA
  --file FILE
  --item ITEM
  --verbose
  --version
  --toggle
  --pylint
  --tables
  --usage
  --dump
  --mask
  --name
  --info
  --save
  --off
  --on
```

Turn plug on and save credentials so you don't need to enter them again:

```
./rpc.py --plug 192.168.11.63 --user TAPO_USER_EMAIL --pass TAPO_USER_PASS --turn off
```

Toggle power:

```
./rpc.py --plug 192.168.11.63 --toggle
```

Get device information and mask MACs, IDs, etc:

```
./rpc.py --plug 192.168.11.63 --data info --mask
device_id: XXXX
fw_ver: 1.3.4 Build 250403 Rel.150504
hw_ver: 1.0
type: SMART.TAPOPLUG
model: P110
mac: XXXX
hw_id: XXXX
fw_id: XXXX
oem_id: XXXX
ip: XXXX
time_diff: 600
ssid: XXXX
rssi: -34
signal_level: 3
auto_off_status: off
auto_off_remain_time: 0
longitude: XXXX
latitude: XXXX
lang: en_US
avatar: radio
region: XXXX
specs: 
nickname: XXXX
has_set_location_info: True
device_on: True
on_time: 81
default_states: {'type': 'last_states', 'state': {}}
power_protection_status: normal
overcurrent_status: normal
charging_status: normal
```

Get device information in JSON:

```
./rpc.py --plug 192.168.11.63 --data info --dump
```

Get device information in table format and mask MACs, IDs, etc:

```
./rpc.py --plug 192.168.11.63 --data info --mask --table
┌─────────────────────────┬──────────────────────────────────────┐
│ Item                    │ Value                                │
├─────────────────────────┼──────────────────────────────────────┤
│ device_id               │ XXXX                                 │
├─────────────────────────┼──────────────────────────────────────┤
│ fw_ver                  │ 1.3.4 Build 250403 Rel.150504        │
├─────────────────────────┼──────────────────────────────────────┤
│ hw_ver                  │ 1.0                                  │
├─────────────────────────┼──────────────────────────────────────┤
│ type                    │ SMART.TAPOPLUG                       │
├─────────────────────────┼──────────────────────────────────────┤
│ model                   │ P110                                 │
├─────────────────────────┼──────────────────────────────────────┤
│ mac                     │ XXXX                                 │
├─────────────────────────┼──────────────────────────────────────┤
│ hw_id                   │ XXXX                                 │
├─────────────────────────┼──────────────────────────────────────┤
│ fw_id                   │ XXXX                                 │
├─────────────────────────┼──────────────────────────────────────┤
│ oem_id                  │ XXXX                                 │
├─────────────────────────┼──────────────────────────────────────┤
│ ip                      │ XXXX                                 │
├─────────────────────────┼──────────────────────────────────────┤
│ time_diff               │ 600                                  │
├─────────────────────────┼──────────────────────────────────────┤
│ ssid                    │ XXXX                                 │
├─────────────────────────┼──────────────────────────────────────┤
│ rssi                    │ -35                                  │
├─────────────────────────┼──────────────────────────────────────┤
│ signal_level            │ 3                                    │
├─────────────────────────┼──────────────────────────────────────┤
│ auto_off_status         │ off                                  │
├─────────────────────────┼──────────────────────────────────────┤
│ auto_off_remain_time    │ 0                                    │
├─────────────────────────┼──────────────────────────────────────┤
│ longitude               │ XXXX                                 │
├─────────────────────────┼──────────────────────────────────────┤
│ latitude                │ XXXX                                 │
├─────────────────────────┼──────────────────────────────────────┤
│ lang                    │ en_US                                │
├─────────────────────────┼──────────────────────────────────────┤
│ avatar                  │ radio                                │
├─────────────────────────┼──────────────────────────────────────┤
│ region                  │ XXXX                                 │
├─────────────────────────┼──────────────────────────────────────┤
│ specs                   │                                      │
├─────────────────────────┼──────────────────────────────────────┤
│ nickname                │ XXXX                                 │
├─────────────────────────┼──────────────────────────────────────┤
│ has_set_location_info   │ True                                 │
├─────────────────────────┼──────────────────────────────────────┤
│ device_on               │ True                                 │
├─────────────────────────┼──────────────────────────────────────┤
│ on_time                 │ 338                                  │
├─────────────────────────┼──────────────────────────────────────┤
│ default_states          │ {'type': 'last_states', 'state': {}} │
├─────────────────────────┼──────────────────────────────────────┤
│ power_protection_status │ normal                               │
├─────────────────────────┼──────────────────────────────────────┤
│ overcurrent_status      │ normal                               │
├─────────────────────────┼──────────────────────────────────────┤
│ charging_status         │ normal                               │
└─────────────────────────┴──────────────────────────────────────┘
```

List items that can be queried:

```
./rpc.py --plug 192.168.11.63 --item list
device_id
fw_ver
hw_ver
type
model
mac
hw_id
fw_id
oem_id
ip
time_diff
ssid
rssi
signal_level
auto_off_status
auto_off_remain_time
longitude
latitude
lang
avatar
region
specs
nickname
has_set_location_info
device_on
on_time
default_states
power_protection_status
overcurrent_status
charging_status
```

Get specific item information:

```
./rpc.py --plug 192.168.11.63 --item model
model: P110
```