#!/usr/bin/env python3

API_ADDR = "http://webserver:5000"
API_LOGIN = "admin@local.domain"
API_PASSWORD = "SuperPass"
API_headers = {'Content-Type': 'application/json'}


# https://docs.python.org/3.5/library/argparse.html
import argparse

import json
import requests


parser = argparse.ArgumentParser(description='http://www.dlink.ru/r/faq/62/193.html')
parser.add_argument('-s', '--hex_string', help='D-Link MAC Notification hex-string', required=True)
parser.add_argument('-t', '--type', choices=["action", "mac_addr", "port", "unit"])

parser.add_argument("-a", "--add-to-db", help="Add full row in DB", action='store_true')
parser.add_argument("--host", help="Address of the device. Required if -a/--add-to-db set")



hex_string = parser.parse_args().hex_string
arg_type = parser.parse_args().type


action = hex_string.split()[0]
if action == "01":
	action = "added"

elif action == "02":
	action = "removed"

elif action == "03":
	action = "moved"

mac_addr = ":".join( hex_string.split()[1:-3] ).lower()
port = int(hex_string.split()[-2], 16)
unit = int(hex_string.split()[-1], 16)



def pgrest_get_token(login=API_LOGIN, password=API_PASSWORD, addr=API_ADDR, headers=API_headers):

	res = requests.post( "{0}/rpc/login".format(addr), headers=headers, json={ "email": login, "pass": password} )
	
	if res.status_code == 200:
		result =  json.loads(res.content.decode('utf-8'))
	else:
		result = None

	token = result[0]["token"]

	return token



if parser.parse_args().add_to_db:
	
	token = pgrest_get_token()
	headers = API_headers
	headers["Authorization"] = "Bearer {0}".format(token)
	data = { "mac": mac_addr, "host": parser.parse_args().host, "unit": unit, "port": port}
	
	check_req_str = "{0}/macs?mac=eq.{1}&host=eq.{2}&unit=eq.{3}&port=eq.{4}".format(API_ADDR, data["mac"], data["host"], data["unit"], data["port"])
	check = requests.get(check_req_str, headers=headers)

	if check.status_code == 200 and len(check.json()) == 0:
		result = requests.post( "{0}/macs".format(API_ADDR), headers=headers, json=data )



# Main output for SNMPTT:
if arg_type:
	res = eval(arg_type)
	print(res)

