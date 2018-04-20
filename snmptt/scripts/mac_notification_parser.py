#!/usr/bin/env python3

API_ADDR = "http://webserver:5000"
API_LOGIN = "admin@local.domain"
API_PASSWORD = "SuperPass"
API_headers = {'Content-Type': 'application/json'}

SNMPWALK = "/usr/bin/snmpwalk"
SNMP_PASS = "public"


# https://docs.python.org/3.5/library/argparse.html
import argparse

import json
import requests

import subprocess


parser = argparse.ArgumentParser(description='http://www.dlink.ru/r/faq/62/193.html')
parser.add_argument('-s', '--hex_string', help='MAC Notification HEX-string', required=True)
parser.add_argument('-t', '--type', choices=["action", "mac_addr", "port", "vlan"])
parser.add_argument('-v', '--vendor', choices=["dlink", "cisco"], help="Switch vendor")

parser.add_argument("-a", "--add-to-db", help="Add full row in DB", action='store_true')
parser.add_argument("--host", help="Address of the device. Required if -a/--add-to-db set or if vendor is Cisco.")


host = None
host_vendor = None
action = None
vlan = None
mac_addr = None
port = None 
add_to_db = parser.parse_args().add_to_db


hex_string = parser.parse_args().hex_string
arg_type = parser.parse_args().type
host_vendor = parser.parse_args().vendor

if parser.parse_args().host:
	host = parser.parse_args().host


hex_string_splited = hex_string.split()



# Must be rewrited under "if venod == ..." when differences between vendors are seen:
action = hex_string_splited[0]
if action == "01":
	action = "added"

elif action == "02":
	action = "removed"

elif action == "03":
	action = "moved"


if host_vendor == "dlink":
	mac_addr = ":".join( hex_string_splited[1:-3] ).lower()
	port = "{0}/{1}".format(int(hex_string_splited[-1], 16), int(hex_string_splited[-2], 16))
	
elif host_vendor == "cisco":
	vlan = int("".join(hex_string_splited[1:3]), 16)
	mac_addr = ":".join( hex_string_splited[3:9] ).lower()

	if arg_type == "port" or add_to_db:
		dot1dBasePort = int("".join(hex_string_splited[9:11]), 16)

		cmd = "{0} -c {1}@{2} -v 2c {3} 1.3.6.1.2.1.17.1.4.1.2.{4}".format(SNMPWALK, SNMP_PASS, vlan, host, dot1dBasePort)
		r = subprocess.Popen( cmd.split(), stdout=subprocess.PIPE )
		r = r.stdout.read()
		IfIndex = int(r.split()[-1])

		cmd = "{0} -c {1}@{2} -v 2c {3} 1.3.6.1.2.1.31.1.1.1.1.{4}".format(SNMPWALK, SNMP_PASS, vlan, host, IfIndex)
		r = subprocess.Popen( cmd.split(), stdout=subprocess.PIPE )
		r = r.stdout.read()
		ifName = r.split()[-1]
		port = ifName.decode("utf-8").replace('"','')



def pgrest_get_token(login=API_LOGIN, password=API_PASSWORD, addr=API_ADDR, headers=API_headers):

	res = requests.post( "{0}/rpc/login".format(addr), headers=headers, json={ "email": login, "pass": password} )

	if res.status_code == 200:
		result =  json.loads(res.content.decode('utf-8'))
	else:
		result = None

	token = result[0]["token"]

	return token



if add_to_db:
	
	token = pgrest_get_token()
	headers = API_headers
	headers["Authorization"] = "Bearer {0}".format(token)
	data = { "mac": mac_addr, "host": host, "port": port, "host_vendor": host_vendor, "vlan": vlan}
		
	check_req_str = "{0}/macs?mac=eq.{1}&host=eq.{2}&port=eq.{3}".format(API_ADDR, data["mac"], data["host"], data["port"])
	check = requests.get(check_req_str, headers=headers)
	
	if check.status_code == 200 and len(check.json()) == 0:
		result = requests.post( "{0}/macs".format(API_ADDR), headers=headers, json=data )



# Main output for SNMPTT:
if arg_type:
	res = eval(arg_type)
	print(res)

