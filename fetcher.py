#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 15 16:33:06 2023

@author: vandenboer
"""

import requests
import json

def read_json(json_file, is_remote = False, username = None, password = None):
    if is_remote:
        return requests.get(json_file, auth = (username, password)).json
    with open(json_file, "r") as file:
        return json.loads(file.read())

def _parse_yum(yum_file, is_remote = False, username = None, password = None):
    if is_remote:
        result = requests.get(yum_file, auth = (username, password)).text
        return _yum_parse_lines(result.splitlines())
    else:
        with open(yum_file) as f:
            return _yum_parse_lines(f.readlines())
            
def _yum_parse_lines(lines):
    mirrors = dict()
    mirror_name = ""
    for line in lines:
        line = line.replace("\n", "")
        if line.startswith("["):
            mirror_name=line.replace("[", "").replace("]","")
            mirrors[mirror_name] = dict()
        elif line.startswith('#') or line.startswith(';'):
            continue
        elif line is not None and line !="":
            if ";" in line:
                line = line.split(";")[0]
            if "#" in line:
                line = line.split("#")[0]
            fields=line.split("=", 1)
            if fields[0] == "excludepkgs":
                fields[0] = "exclude"
            if fields[0] == "includepkgs":
                fields[0] = "include"
            mirrors[mirror_name][fields[0]] = fields[1]
    return mirrors

def parse_yum_to_json(yum_file, is_remote = False, username = None, password = None):
    parsed = _parse_yum(yum_file, is_remote, username, password)
    json_dict = dict()
    if parsed != dict():
        json_dict["repositories"] = dict()
        json_dict["remotes"] = dict()
    for repository_name, repository_values in parsed.items():
        if repository_name == "main":
            continue
        # if repository_name != "elastic-7.x":
        #     print("Skipping repository (%s) for testing" % repository_name)
        #     continue
        json_dict["repositories"][repository_name] = dict()
        if "baseurl" in repository_values.keys() or "username" in repository_values.keys() or "password" in repository_values.keys():
            remote_name = repository_name
            json_dict["repositories"][repository_name]["remote"] = remote_name
            json_dict["remotes"][remote_name] = dict()
        for key, value in repository_values.items():
            if key in ("exclude", "excludepkgs"):
                value = value.replace(",", " ")
                json_dict["repositories"][repository_name]["exclude"] = value.split(" ")
            elif key in ("include", "includepkgs"):
                value = value.replace(",", " ")
                json_dict["repositories"][repository_name]["include"] = value.split(" ")
            elif key == "baseurl":
                json_dict["remotes"][remote_name]["url"] = value
            elif key == "username":
                json_dict["remotes"][remote_name]["username"] = value
            elif key == "password":
                json_dict["remotes"][remote_name]["password"] = value
    return json_dict
        
        