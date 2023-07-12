#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 27 16:52:16 2023

@author: vandenboer
"""

import getopt, sys
from pulp_manager import pulp_manager
from fetcher import parse_yum_to_json
from fetcher import read_json

vars = {}
username = None
password = None
pulp_username = None
pulp_password = None
pulp_url = None
json_file = None
rjson_file = None
yum_file = None
ryum_file = None

def usage():
    print("Useable parameters:")
    print("-h                 : print this help")
    print("-e/--environment   : environment variables to fill in the config file, format -e [variable_name]:[variable_value]")
    print("-u/--username      : username to access remote file")
    print("-p/--password      : password to access remote file")
    print("--pulp-username    : username to access pulp with")
    print("--pulp-password    : password to access pulp with")
    print("--pulp-url         : url of the pulp instance")
    print("--json             : json file to parse from")
    print("--remote-json-file : remote file to parse from")
    print("--remote-yum-file  : remote file to parse from")
    print("--yum-conf         : yum config file to parse from")

try:
    opts, args = getopt.getopt(sys.argv[1:], "e:u:p:h", ["environment","username","password","json", "remote-json-file", "yum-conf", "yum-remote-conf", "pulp-password", "pulp-username"])
except getopt.GetoptError as err:
    print(err)
    usage()
    sys.exit(1)

for option, argument in opts:
    if option == "-h":
        usage()
        sys.exit()
    elif option in ("-e", "--environment"):
        splits = argument.split(":", 1)
        vars[splits[0]] = splits[1]
    elif option in ("-u", "--username"):
        username = argument
    elif option in ("-p", "--password"):
        password = argument
    elif option == "--pulp-username":
        pulp_username = argument
    elif option == "--pulp-password":
        pulp_password = argument
    elif option == "--pulp-url":
        pulp_url = argument
    elif option == "--json":
        json_file = argument
    elif option == "--yum-conf":
        yum_file = argument
    elif option == "--remote-json-file":
        rjson_file = argument
    elif option == "--remote-yum-file":
        ryum_file = argument
    else:
        print("unhandled option: %s" % option)
        sys.exit(2)

pulp_mgr = pulp_manager(pulp_url, pulp_username, pulp_password)

if json_file:
    pulp_mgr.setup_from_json(read_json(json_file, False, username, password))
if rjson_file:
    pulp_mgr.setup_from_json(read_json(rjson_file, True, username, password))
if yum_file:
    pulp_mgr.setup_from_json(parse_yum_to_json(yum_file, False, username, password))
if ryum_file:
    pulp_mgr.setup_from_json(parse_yum_to_json(ryum_file, True, username, password))
