#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 18 19:21:44 2023

@author: vandenboer
"""
import requests
import json

class req_wrapper():
    
    def __init__(self, username = None, password = None):
        self.username = username
        self.password = password
        self.last_request = None
        
    def do_post_request(self, url, json_data = ""):
        self.last_request = requests.request(method="POST", url=url, data=json_data, auth=(self.username, self.password), headers={'Content-type': 'application/json'})
        return self.last_request
    
    def do_post_request_multipart(self, url, json_data, file):
        data = json.loads(json_data)
        data["file"] = (file, open(file, 'rb'))        
        self.last_request = requests.request(method="POST", url=url, file=data, auth=(self.username, self.password), headers={'Content-type': 'multipart/form-data'})
        return self.last_request
    
    def do_get_request(self, url, json_data = ""):
        self.last_request = requests.request(method="GET", url=url, data=json_data, auth=(self.username, self.password))
        return self.last_request
    
    def get_request_content(self, request = None):
        if request == None:
            return self.last_request.text
        return request.text
    
    def is_request_ok(self, request = None):
        if request == None:
            return self.last_request.ok
        return request.ok

class json_wrapper():
    
    def __init__(self, json_string):
        self.data = json.loads(json_string)