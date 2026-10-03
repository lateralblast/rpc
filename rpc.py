#!/usr/bin/env python3
"""Script to drive tapo and other plugs"""

# Name:         rpc (Remote Plug Control)
# Version:      0.2.8
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

import argparse
import base64
import importlib
import json
import os
import re
import select
import socket
import struct
import subprocess
import sys
import time
import zlib

from pprint import pp
from shutil import which

__version__ = "0.2.8"

DEBUG = int(os.getenv("DEBUG") or "0")
PKT_ONBOARD_REQUEST = b'\x11\x00'
SCAN_PORT = 20002
TAPO_FORK = "git+https://github.com/almottier/TapoP100.git@main"
MASK_PATTERN = re.compile(r"i[d,p]$|mac$|tude$|region|nickname")
DEFAULT_CREDENTIALS = os.path.join(os.path.expanduser("~"), ".rpc", "plugs")


def eprint(*args, **kwargs):
    """Print to stderr when DEBUG is set"""
    if DEBUG:
        print(*args, **kwargs, file=sys.stderr)


def load_module(name, package=None):
    """Import a module, pip installing it for the user if it is missing"""
    try:
        return importlib.import_module(name)
    except ImportError:
        command = [sys.executable, "-m", "pip", "install", "--user", package or name]
        subprocess.run(command, check=False)
        importlib.invalidate_caches()
        return importlib.import_module(name)


def pkcs7_pad(input_str, block_len=16):
    """Pad pkcs7"""
    pad_len = block_len - len(input_str) % block_len
    return input_str + chr(pad_len) * pad_len


def pkcs7_unpad(ct):
    """Unpad pkcs7"""
    return ct[:-ord(ct[-1])]


class TpLinkCipher:
    """TpLink Cipher class"""

    def __init__(self, key, iv):
        self.iv = iv
        self.key = key
        self.aes = load_module("Crypto.Cipher.AES", "pycryptodome")

    def encrypt(self, data):
        """Encrypt"""
        data = pkcs7_pad(data)
        cipher = self.aes.new(bytes(self.key), self.aes.MODE_CBC, bytes(self.iv))
        encrypted = cipher.encrypt(data.encode())
        return base64.b64encode(encrypted).decode().replace("\r\n", "")

    def decrypt(self, data: str):
        """Decrypt"""
        cipher = self.aes.new(bytes(self.key), self.aes.MODE_CBC, bytes(self.iv))
        pad_text = cipher.decrypt(base64.b64decode(data.encode())).decode()
        return pkcs7_unpad(pad_text)


def extract_payload_from_package_json(packet):
    """Extract payload from package JSON"""
    return json.loads(packet[16:])


def build_packet_for_payload(payload, pkt_type, pkt_id=b"\x01\x02\x03\x04"):
    """Build packet for payload"""
    len_bytes = struct.pack(">h", len(payload))
    skeleton = b'\x02\x00\x00\x01' + len_bytes + pkt_type + pkt_id + b'\x5A\x6B\x7C\x8D' + payload
    crc32_bytes = struct.pack(">I", zlib.crc32(skeleton) & 0xffffffff)
    return skeleton[0:12] + crc32_bytes + skeleton[16:]


def build_packet_for_payload_json(payload, pkt_type, pkt_id=b"\x01\x02\x03\x04"):
    """Build packet for payload JSON"""
    return build_packet_for_payload(json.dumps(payload).encode(), pkt_type, pkt_id)


def process_encrypted_handshake(response, rsa_cipher):
    """Process encrypted handshake"""
    encrypted_key = base64.b64decode(response["result"]["encrypt_info"]["key"].encode())
    clear_key = rsa_cipher.decrypt(encrypted_key)
    if not clear_key:
        raise ValueError("Decryption failed!")
    cipher = TpLinkCipher(bytearray(clear_key[:16]), bytearray(clear_key[16:32]))
    cleartext = cipher.decrypt(response["result"]["encrypt_info"]["data"])
    eprint("handshake payload decrypted as", cleartext)
    return json.loads(cleartext)


def find_tapo_devices(timeout=3):
    """Find Tapo devices by UDP broadcast"""
    rsa = load_module("Crypto.PublicKey.RSA", "pycryptodome")
    key = rsa.generate(2048)
    public_key = key.public_key().export_key('PEM').decode()
    packet = build_packet_for_payload_json({"params": {"rsa_key": public_key}}, PKT_ONBOARD_REQUEST)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, 5)
        sock.settimeout(2)
        sock.sendto(packet, ("255.255.255.255", SCAN_PORT))
        eprint("packet sent", packet)
        poller = select.poll()
        poller.register(sock, select.POLLIN)
        before = time.time()
        while time.time() - before <= timeout:
            if not poller.poll(100):
                continue
            handshake_packet, addr = sock.recvfrom(2048)
            eprint("received", addr, handshake_packet)
            try:
                handshake_json = extract_payload_from_package_json(handshake_packet)
                if handshake_json["error_code"]:
                    continue
                yield handshake_json["result"]
            except (ValueError, KeyError):
                pass


def check_credentials(options):
    """Exit if plug, user or pass is missing"""
    for item in ('plug', 'user', 'pass'):
        if not options[item]:
            sys.exit(f"{item} not specified")


def connect_plug(options):
    """Connect to plug"""
    check_credentials(options)
    plug_type = options['type'].lower()
    if plug_type not in ("p100", "p110"):
        sys.exit(f"Unsupported plug type: {options['type']}")
    load_module("PyP100", TAPO_FORK)
    module = importlib.import_module(f"PyP100.Py{plug_type.upper()}")
    plug_class = getattr(module, plug_type.upper())
    return plug_class(options['plug'], options['user'], options['pass'])


def control_plug(options, plug):
    """Control plug"""
    if options['toggle']:
        plug.toggleState()
    if options['turn'] == "on" or options['on']:
        if options['secs']:
            plug.turnOnWithDelay(int(options['secs']))
        else:
            plug.turnOn()
    if options['turn'] == "off" or options['off']:
        if options['secs']:
            plug.turnOffWithDelay(int(options['secs']))
        else:
            plug.turnOff()
    return plug


def print_data(data, options, mask=False):
    """Print a dict as key: value lines or as a table"""
    rows = []
    for key, value in data.items():
        if mask and MASK_PATTERN.search(key):
            value = "XXXX"
        rows.append([key, value])
    if options['tables']:
        single_table = load_module("terminaltables").SingleTable
        table = single_table([["Item", "Value"]] + rows)
        table.inner_row_border = True
        print(table.table)
    else:
        for key, value in rows:
            print(f"{key}: {value}")


def query_plug(options, plug):
    """Query plug"""
    if options['verbose']:
        print(f"Connecting to {options['plug']}")
    if options['data'] == "name" or options['item'] == "name":
        print(plug.getDeviceName())
    elif options['item']:
        data = json.loads(json.dumps(plug.getDeviceInfo()))
        key = options['item'].lower()
        if key == "list":
            print("\n".join(data))
        elif key in data:
            print(f"{key}: {data[key]}")
        else:
            print(f"\nItem \"{key}\" does not exist\n\nList of items:")
            print("\n".join(data))
    if options['data'] == "info":
        info = plug.getDeviceInfo()
        if options['dump'] and not options['mask']:
            pp(info)
        else:
            print_data(json.loads(json.dumps(info)), options, options['mask'])
    if options['data'] == "usage":
        usage = plug.getEnergyUsage()
        if options['dump']:
            pp(usage)
        else:
            print_data(json.loads(json.dumps(usage)), options)
    return plug


def check_file_perms(file_name):
    """Restrict the credentials file to its owner"""
    if os.path.exists(file_name) and os.stat(file_name).st_mode & 0o777 != 0o600:
        os.chmod(file_name, 0o600)


def read_credentials(file_name):
    """Read host:user:pass lines from the credentials file"""
    if not os.path.exists(file_name):
        return []
    with open(file_name, encoding="utf-8") as file:
        lines = file.read().splitlines()
    return [line.split(":", 2) for line in lines if line.count(":") >= 2]


def get_credentials(options):
    """Fill in user and pass for the plug from the credentials file"""
    check_file_perms(options['file'])
    if options['verbose'] and os.path.exists(options['file']):
        print(f"Reading credentials from {options['file']}")
    for hostname, username, password in read_credentials(options['file']):
        if hostname == options['plug']:
            options['user'] = username
            options['pass'] = password
    return options


def save_credentials(options):
    """Save or update the plug entry in the credentials file"""
    check_credentials(options)
    entries = read_credentials(options['file'])
    new_entry = [options['plug'], options['user'], options['pass']]
    others = [entry for entry in entries if entry[0] != options['plug']]
    if new_entry in entries:
        return
    if options['verbose']:
        print(f"Saving credentials to {options['file']}")
    os.makedirs(os.path.dirname(options['file']), exist_ok=True)
    with open(options['file'], "w", encoding="utf-8") as file:
        for entry in others + [new_entry]:
            file.write(":".join(entry) + "\n")
    check_file_perms(options['file'])


def scan_for_tapo_devices(options):
    """Scan for Tapo devices"""
    for device in find_tapo_devices():
        if options['dump']:
            print(json.dumps(device, indent=2))
        elif "PLUG" in device['device_type']:
            model = device['device_model'].split('(')[0]
            print(f"Plug: {device['ip']} [{model}]")


def run_pylint(file_name):
    """Run pylint"""
    if which("pylint") is None:
        sys.exit("pylint is not installed")
    sys.exit(subprocess.run(["pylint", file_name], check=False).returncode)


def build_parser():
    """Build the argument parser"""
    parser = argparse.ArgumentParser(description="Remote Plug Control")
    parser.add_argument("--plug", help="IP/Hostname of plug")
    parser.add_argument("--user", help="Username")
    parser.add_argument("--pass", help="Password")
    parser.add_argument("--turn", help="Turn plug on or off")
    parser.add_argument("--type", help="Type of plug (p100 or p110)")
    parser.add_argument("--secs", help="Seconds to delay on/off")
    parser.add_argument("--data", help="Get data (e.g. info, name, usage)")
    parser.add_argument("--file", help="Credentials file")
    parser.add_argument("--item", help="Get specific data item (or list)")
    parser.add_argument("--verbose", action='store_true', help="Display verbose information")
    parser.add_argument("--version", action='store_true', help="Display version information")
    parser.add_argument("--toggle", action='store_true', help="Toggle state")
    parser.add_argument("--pylint", action='store_true', help="Run pylint")
    parser.add_argument("--tables", action='store_true', help="Output data in table format")
    parser.add_argument("--usage", action='store_true', help="Get usage information")
    parser.add_argument("--dump", action='store_true', help="Dump data with little processing")
    parser.add_argument("--info", action='store_true', help="Get info")
    parser.add_argument("--mask", action='store_true', help="Mask information like serials")
    parser.add_argument("--name", action='store_true', help="Get name")
    parser.add_argument("--save", action='store_true', help="Save plug credentials to file")
    parser.add_argument("--scan", action='store_true', help="Scan for Tapo devices")
    parser.add_argument("--off", action='store_true', help="Turn off")
    parser.add_argument("--on", action='store_true', help="Turn on")
    return parser


def main(argv=None):
    """Entry point"""
    parser = build_parser()
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        parser.print_help()
        return
    options = vars(parser.parse_args(argv))
    if options['version']:
        print(__version__)
        return
    if options['pylint']:
        run_pylint(__file__)
    if options['scan']:
        scan_for_tapo_devices(options)
        return
    if options['file']:
        if not os.path.exists(options['file']):
            sys.exit(f"File {options['file']} does not exist")
    else:
        options['file'] = DEFAULT_CREDENTIALS
    if options['plug'] and (not options['user'] or not options['pass']):
        options = get_credentials(options)
    if not options['data']:
        if options['usage']:
            options['data'] = "usage"
        elif options['info']:
            options['data'] = "info"
        elif options['name']:
            options['data'] = "name"
    if not options['type']:
        options['type'] = "p110" if options['data'] == "usage" else "p100"
    if options['save']:
        save_credentials(options)
    if options['turn']:
        options['turn'] = options['turn'].lower()
    plug = None
    if options['turn'] or options['on'] or options['off'] or options['toggle']:
        plug = control_plug(options, connect_plug(options))
    if options['data'] or options['item']:
        query_plug(options, plug or connect_plug(options))


if __name__ == "__main__":
    main()
