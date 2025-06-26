#!/usr/bin/env python3
"""Script to drive tapo and other plugs"""

# pylint: disable=C0103
# pylint: disable=C0301
# pylint: disable=E0401
# pylint: disable=E0606
# pylint: disable=R0912
# pylint: disable=R0915
# pylint: disable=W0311
# pylint: disable=W0611
# pylint: disable=W0621

# Name:         rpc (Remote Plug Control)
# Version:      0.1.3
# Release:      1
# License:      CC-BA (Creative Commons By Attribution)
#               http://creativecommons.org/licenses/by/4.0/legalcode
# Group:        System
# Source:       N/A
# URL:          N/A
# Distribution: UNIX
# Vendor:       Lateral Blast
# Packager:     Richard Spindler <richard@lateralblast.com.au>
# Description:  Script to drive tapo and other plugs

# import modules

import importlib
import argparse
import stat
import json
import sys
import os
import re

from os.path import expanduser
from pprint import pp
from shutil import which

# Set some defaults

script = {}

script['name'] = "rpc"
script['home'] = expanduser("~")
script['file'] = sys.argv[0]
script['path'] = os.path.dirname(script['file'])
script['work'] = f"{script['home']}/.{script['name']}"

if not os.path.exists(script['work']):
  os.mkdir(script['work'])

try:
  from pip._internal import main
except ImportError:
  os.system("easy_install pip")
  os.system("pip install --upgrade pip")

try:
  import PyP100
except ImportError:
  command = "pip install --user git+https://github.com/almottier/TapoP100.git@main"
  os.system(command)
  import PyP100

def install_and_import(package):
  """Install and import a python module"""
  try:
    importlib.import_module(package)
  except ImportError:
    command = f"python3 -m pip install --user {package}"
    os.system(command)
  finally:
    globals()[package] = importlib.import_module(package)

try:
  from terminaltables import SingleTable
except ImportError:
  install_and_import("terminaltables")
  from terminaltables import SingleTable

def print_version(file_name):
  """Print version"""
  file_array = file_to_array(file_name)
  version    = list(filter(lambda x: re.search(r"^# Version", x), file_array))[0].split(":")[1]
  version    = re.sub(r"\s+","",version)
  print(version)
  sys.exit()

def print_help(file_name):
  """Print help"""
  print("\n")
  command = f"{file_name} -h"
  os.system(command)
  print("\n")
  sys.exit()

def file_to_array(file_name):
  """Read a file into an array"""
  with open(file_name, encoding="utf-8") as file:
    file_array = file.readlines()
  return file_array

def check_credentials(options):
  """Check credentials"""
  items = [ 'plug', 'user', 'pass' ]
  for item in items:
    if not options[item]:
      string = f"{item} not specified"
      print(string)
      sys.exit()

def connect_plug(options):
  """Connect to plug"""
  check_credentials(options)
  if options['type'].lower() == "p100":
    plug = PyP100.P100(options['plug'], options['user'], options['pass'])
  if options['type'].lower() == "p110":
    plug = PyP110.P110(options['plug'], options['user'], options['pass'])
  return plug

def control_plug(options, plug):
  """Control plug"""
  if options['toggle'] is True:
    plug.toggleState()
  if options['turn'] == "on" or options['on'] is True:
    if options['secs']:
      plug.turnOnWithDelay(options['secs'])
    else:
      plug.turnOn()
  if options['turn'] == "off" or options['off'] is True:
    if options['secs']:
      plug.turnOffWithDelay(options['secs'])
    else:
      plug.turnOff()
  return plug

def query_plug(options, plug):
  """Query plug"""
  if options['verbose'] is True:
    string = f"Connecting to {options['plug']}"
    print(string)
  if options['tables'] is True:
    table_data = []
    table_row  = [ "Item", "Value" ]
    table_data.append(table_row)
  if options['data'] == "name" or options['item'] == "name":
    name = plug.getDeviceName()
    print(name)
  else:
    if options['item']:
      info = plug.getDeviceInfo()
      data = json.dumps(info)
      data = json.loads(data)
      key  = options['item'].lower()
      if key == "list":
        for key in data:
          print(key)
      try:
        value  = data[key]
        string = f"{key}: {value}"
        print(string)
      except KeyError:
        string = f"Item \"{key}\" does not exist"
        print()
        print(string)
        print()
        print("List of items:")
        for key in data:
          print(key)
  if options['data'] == "info":
    info = plug.getDeviceInfo()
    if options['dump'] is True and options['mask'] is False:
      pp(info)
    else:
      data = json.dumps(info)
      data = json.loads(data)
      for key in data:
        if options['mask'] is False:
          value  = data[key]
          string = f"{key}: {value}"
        else:
          if re.search(r"i[d,p]$|mac$|tude$|region|nickname", key):
            value  = "XXXX"
            string = f"{key}: {value}"
          else:
            value  = data[key]
            string = f"{key}: {value}"
        if options['tables'] is True:
          table_row  = [ key, value ]
          table_data.append(table_row)
        else:
          print(string)
      if options['tables'] is True:
        table = SingleTable(table_data)
        table.inner_row_border = True
        print(table.table)
  if options['data'] == "usage":
    usage = plug.getEnergyUsage()
    if options['dump'] is True:
      pp(usage)
    else:
      data = json.dumps(usage)
      data = json.loads(data)
      for key in data:
        value  = data[key]
        string = f"{key}: {value}"
        if options['tables'] is True:
          table_row  = [ key, value ]
          table_data.append(table_row)
        else:
          print(string)
      if options['tables'] is True:
        table = SingleTable(table_data)
        table.inner_row_border = True
        print(table.table)
  return plug

def check_file_perms(options):
  """Check file permissions"""
  if os.path.exists(options['file']):
    perms   = os.stat(options['file'])
    correct = "0o100600"
    actual  = oct(perms.st_mode)
    if not actual == correct:
      os.chmod(options['file'], 0o600)

def get_credentials(options):
  """Get credentials"""
  check_file_perms(options)
  if options['verbose'] is True:
    if os.path.exists(options['file']):
      string = f"Reading credentials from {options['file']}"
      print(string)
  file_array = file_to_array(options['file'])
  for line in file_array:
    if re.search(":", line):
      hostname = line.split(":")[0]
      if hostname == options['plug']:
        username = line.split(":")[1]
        password = line.split(":")[2]
        options['user'] = username
        options['pass'] = password.strip()
  return options

def save_credentials(options):
  """Save credentials"""
  new_array = []
  new_entry = False
  check_credentials(options)
  if os.path.exists(options['file']):
    file_array = file_to_array(options['file'])
    for line in file_array:
      if re.search(":", line):
        hostname = line.split(":")[0]
        if hostname == options['plug']:
          username = line.split(":")[1]
          password = line.split(":")[2]
          password = password.strip()
          if not username == options['user']:
            new_entry = True
          if not password == options['pass']:
            new_entry = True
          if new_entry is True:
            line = f"{options['plug']}:{options['user']}:{options['pass']}\n"
            new_array.append(line)
        else:
          new_array.append(line)
    if new_entry is True:
      if options['verbose'] is True:
        string = f"Saving credentials to {options['file']}"
        print(string)
      with open(options['file'], "w", encoding="utf-8") as file:
        for line in new_array:
          file.write(line)
  else:
    if options['verbose'] is True:
      string = f"Saving credentials to {options['file']}"
      print(string)
    with open(options['file'], "w", encoding="utf-8") as file:
      line = f"{options['plug']}:{options['user']}:{options['pass']}\n"
      file.write(line)
  check_file_perms(options)

def run_pylint(file_name):
  """Run pylint"""
  if which("pylint") is None:
    print("pylint is not installed")
    sys.exit()
  else:
    command = f"pylint {file_name}"
    os.system(command)
    sys.exit()

if sys.argv[-1] == sys.argv[0]:
  print_help(script['file'])
  sys.exit()

parser = argparse.ArgumentParser()
parser.add_argument("--plug",     required=False)       # Specify IP/Hostname of plug
parser.add_argument("--user",     required=False)       # Specify Username
parser.add_argument("--pass",     required=False)       # Specify Password
parser.add_argument("--turn",     required=False)       # Specify whether to turn plug off or on
parser.add_argument("--type",     required=False)       # Specify type of plug
parser.add_argument("--secs",     required=False)       # Specify time to delay on/off
parser.add_argument("--data",     required=False)       # Get data (e.g. info, name, usage)
parser.add_argument("--file",     required=False)       # Password file
parser.add_argument("--item",     required=False)       # Get spectic data item information
parser.add_argument("--verbose",  action='store_true')  # Display verbose information
parser.add_argument("--version",  action='store_true')  # Display version information
parser.add_argument("--toggle",   action='store_true')  # Toggle state
parser.add_argument("--pylint",   action='store_true')  # Run pylint
parser.add_argument("--tables",   action='store_true')  # Output data in table format
parser.add_argument("--usage",    action='store_true')  # Get usage information
parser.add_argument("--dump",     action='store_true')  # Dump JSON from plug with little processing
parser.add_argument("--mask",     action='store_true')  # Mask information like serials
parser.add_argument("--name",     action='store_true')  # Get name
parser.add_argument("--info",     action='store_true')  # Get info
parser.add_argument("--save",     action='store_true')  # Save plug IP/hostname, username and password to file
parser.add_argument("--off",      action='store_true')  # Turn off
parser.add_argument("--on",       action='store_true')  # Turn on

options = vars(parser.parse_args())

if options['version'] is True:
  print_version(script['file'])

if options['pylint'] is True:
  run_pylint(script['file'])

if options['file']:
  if not os.path.exists(options['file']):
    string = f"File {options['file']} does not exist"
    print(string)
    sys.exit()
  else:
    options = get_credentials(options)
else:
  options['file'] = f"{script['work']}/plugs"

if options['plug']:
  if not options['user'] or not options['pass']:
    options = get_credentials(options)

if not options['data']:
  if options['usage']:
    options['data'] = "usage"
    options['type'] = "p110"
  if options['info']:
    options['data'] = "info"
  if options['name']:
    options['data'] = "name"

if not options['type']:
  if options['data'] == "usage":
    options['type'] = "p110"
  else:
    options['type'] = "p100"

if options['type'].lower() == "p100":
  from PyP100 import PyP100

if options['type'].lower() == "p110":
  from PyP100 import PyP110

if options['save']:
  save_credentials(options)

if options['turn']:
  options['turn'] = options['turn'].lower()
  plug = connect_plug(options)
  plug = control_plug(options, plug)

if options['toggle'] is True:
  plug = connect_plug(options)
  plug = control_plug(options, plug)

if options['data'] or options['item']:
  plug = connect_plug(options)
  plug = query_plug(options, plug)
