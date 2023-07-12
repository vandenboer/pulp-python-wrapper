#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 18 19:21:44 2023

@author: vandenboer
"""
import requests
import json
import re 

class req_wrapper():
    
    def __init__(self, username = None, password = None):
        self.username = username
        self.password = password
        self.last_request = None
        
    def do_post_request(self, url, json_data = ""):
        self.last_request = requests.request(method="POST", url=url, data=json_data, auth=(self.username, self.password), headers={'Content-type': 'application/json'})
        if not self.is_request_ok():
            raise Exception("Post request failed (%s): %s" % (self.last_request.status_code, self.last_request.content))
        return self.last_request
    
    def do_post_request_multipart(self, url, files_data):
        self.last_request = requests.request(method="POST", url=url, files=files_data, auth=(self.username, self.password))#, headers={'Content-type': "multipart/form-data;"}) # boundary=%s" % md5})
        if not self.is_request_ok():
            raise Exception("Post request failed (%s): %s" % (self.last_request.status_code, self.last_request.content))
        return self.last_request
    
    def do_get_request(self, url, json_data = ""):
        self.last_request = requests.request(method="GET", url=url, data=json_data, auth=(self.username, self.password))
        if not self.is_request_ok():
            raise Exception("Get request failed (%s): %s" % (self.last_request.status_code, self.last_request.content))
        if int(self.last_request.headers["content-length"]) != len(self.last_request.content):
            with requests.request(method="GET", url=url, data=json_data, auth=(self.username, self.password), stream = True) as response:
                data = bytes()
                for chunk in response.iter_content(chunk_size=1024):
                    data += chunk
                if len(data) == int(response.headers['content-length']):
                    self.last_request = response
                    return response
        return self.last_request
    
    def do_put_request(self, url, file, json_data = "", byte_data = None):
        data = json.loads(json_data)
        if byte_data == None:
            data["file"] = (file, open(file, 'rb'))
        else:
            data["file"] = (file, byte_data)
        self.last_request = requests.request(method="PUT", url=url, files=data, auth=(self.username, self.password), headers={'Content-type': 'multipart/form-data'})
        if not self.is_request_ok():
            raise Exception("Put request failed (%s): %s" % (self.last_request.status_code, self.last_request.content))
        return self.last_request
    
    def do_delete_request(self, url, json_data = ""):
        if json_data == "":
            self.last_request = requests.request(method="DELETE", url=url, auth=(self.username, self.password))
        else:
            self.last_request = requests.request(method="DELETE", url=url, data=json_data, auth=(self.username, self.password))
        if not self.is_request_ok():
            raise Exception("Delete request failed (%s): %s" % (self.last_request.status_code, self.last_request.content))
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
        if json_string == None or json_string == []:
            self.data = json.loads("{}")
        else:
            self.data = json.loads(json_string)

class regex_filter():
    
    def __init__(self, regex):
        if regex.startswith("*"):
            regex.replace("*", "", 1)
        else:
            regex = "^" + regex
        regex = regex[::-1]
        if regex.startswith("*"):
            regex.replace("*", "", 1)
        else:
            regex = "$" + regex
        regex = regex[::-1].replace("*", ".*")
        self.regex = re.compile(regex)
    
    def filter_list(self, input_list):
        return list(filter(self.regex.search, input_list))

    def invert_filter_list(self, input_list):
        n_list = self.filter_list(input_list)
        return list(set(input_list).difference(n_list))
    
class url_encoder():
    
    def __init__(self, text):
        self.encoded = requests.utils.quote(text, safe='')
