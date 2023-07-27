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
from wrappers import json_environment_parser


vars = {}
username = None
password = None
pulp_username = None
pulp_password = None
pulp_url = None
do_clean = False
parse_from = {}


def usage():
    print("Useable parameters:")
    print("-h                 : print this help")
    print("-e/--environment   : environment variables to fill in the config file, format -e [variable_name]:[variable_value]")
    print("-u/--username      : username to access remote file")
    print("-p/--password      : password to access remote file")
    print("--pulp-username    : username to access pulp with")
    print("--pulp-password    : password to access pulp with")
    print("--pulp-url         : url of the pulp instance")
    print("--json             : json files to parse from")
    print("--remote-json-file : remote files to parse from")
    print("--remote-yum-conf  : remote files to parse from")
    print("--yum-conf         : yum config files to parse from")
    print("--clean            : clean pulp repositories, remotes and distributions from pulp before creation")

if sys.argv[1:] == []:
    usage()


try:
    opts, args = getopt.getopt(sys.argv[1:], "e:u:p:h", ["environment =","username =","password =","json =", "remote-json-file =", "yum-conf =", "remote-yum-conf =", "pulp-password =", "pulp-username =", "pulp-url =", "clean"])
except getopt.GetoptError as err:
    print(err)
    usage()
    sys.exit(1)


for option, argument in opts:
    option = option.strip()
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
    elif option == "--clean":
        do_clean = True
    elif option == "--json":
        parse_from[argument] = { "json": True, "remote": False }
    elif option == "--yum-conf":
        parse_from[argument] = { "json": False, "remote": False }
    elif option == "--remote-json-file":
        parse_from[argument] = { "json": True, "remote": True }
    elif option == "--remote-yum-conf":
        parse_from[argument] = { "json": False, "remote": True }
    else:
        print("unhandled option: %s" % option)
        sys.exit(2)


pulp_mgr = pulp_manager(pulp_url, pulp_username, pulp_password)
if do_clean:
    pulp_mgr.deleter.delete_all()

# This dictionary should follow the order it is being add in, if not fix.
for file, options in parse_from.items():
    if options["json"]:
        pulp_mgr.setup_from_json(json_environment_parser(read_json(file, options["remote"], username, password), vars))
    else:
        pulp_mgr.setup_from_json(json_environment_parser(parse_yum_to_json(file, options["remote"], username, password), vars))
