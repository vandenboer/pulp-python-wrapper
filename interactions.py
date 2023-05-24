#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 18 19:21:30 2023

@author: vandenboer
"""
import time
from wrappers import req_wrapper, json_wrapper

class pulp_manager():
    
    def __init__(self, pulp_url, username, password):
        self.getter = get_interactions(pulp_url, username, password)
        self.creator = create_interactions(pulp_url, username, password)
        self.uploader = upload_interactions(pulp_url, username, password)

class base_interactions():
    def __init__(self, pulp_url, username, password):
        self.pulp_url = pulp_url
        self.username = username
        self.password = password
        self.req_wrapper = req_wrapper(username, password)
        
    def get_pulp_var(self, var_name, sub_url, json_data):
        self.req_wrapper.do_get_request("%s%s" % (self.pulp_url, sub_url), json_data)
        json = json_wrapper(self.req_wrapper.get_request_content())
        result = []
        for i in json.data['results']:
            result.append(i[var_name])
        return result
    
    def post_pulp_var(self, sub_url, json_data):
        self.req_wrapper.do_post_request("%s%s" % (self.pulp_url, sub_url), json_data)
        json = json_wrapper(self.req_wrapper.get_request_content())
        return json.data
    
    def show_href(self, href):
        self.req_wrapper.do_get_request("%s%s" % (self.pulp_url, href))
        json = json_wrapper(self.req_wrapper.get_request_content())
        return json.data[0]
    
    def is_task_completed(self, task_href):
        self.req_wrapper.do_get_request("%s%s" % (self.pulp_url, task_href))
        json = json_wrapper(self.req_wrapper.get_request_content())
        return json.data["state"] == "completed"
    
    def wait_for_task(self, task_href):
        while self.is_task_completed(task_href):
            time.sleep(1)
            
    def wait_for_all_tasks(self):
        self.get_pulp_var("pulp_href", "/pulp/api/v3/tasks")
        json = json_wrapper(self.req_wrapper.get_request_content())
        do_loop = True
        while do_loop:
            do_loop = False
            for i in json.data:
                if self.is_task_completed(i["pulp_href"]):
                    do_loop = True
                    break



class get_interactions(base_interactions):
    
    def get_repo_href(self, name):
        return self.get_pulp_var("pulp_href", "/pulp/api/v3/repositories/rpm/rpm/", "{\"name\": \"%s\"}" % name)[0]
        
    def get_repo_version_href(self, name):
        return self.get_pulp_var("latest_version_href", "/pulp/api/v3/repositories/rpm/rpm/", "\{\"name\": \"%s\"}" % name)[0]
        
    def get_remote_href(self, name):
        return self.get_pulp_var("pulp_href", "/pulp/api/v3/remote/rpm/rpm/", "{\"name\": \"%s\"}" % name)[0]
        
    def get_distribution_href(self, name):
        return self.get_pulp_var("pulp_href", "/pulp/api/v3/distribution/rpm/rpm/", "{\"name\": \"%s\"}" % name)[0]
        
    def get_package_href(self, name):
        return self.get_pulp_var("pulp_href", "/pulp/api/v3/content/rpm/packages/", "{\"name\": \"%s\"}" % name)[0]



class create_interactions(base_interactions):
    
    def create_repo(self, name, remote = None, wait_for_task = True):
        append = ""
        if remote != None:
            append = ", \"remote\":\"%s\"" % remote
        json_data = "{\"name\": \"%s\" %s}" % (name, append)
        self.post_pulp_var("/pulp/api/v3/repositories/rpm/rpm/", json_data)
        
    def create_remote(self, name, remote_url, policy = "on_demand", username = "", password = "", wait_for_task = True):
        json_data = "{\"name\": \"%s\", \"url\": \"%s\", \"policy\": \"%s\", \"username\": \"%s\", \"password\": \"%s\" }" % (name, remote_url, policy, username, password)
        self.post_pulp_var("/pulp/api/v3/remote/rpm/rpm/", json_data)
        
    def create_publication(self, repostory, metadata_checksum_type="sha256"):
        json_data = "{\"repostory\": \"%s\", \"metadata_checksum_type\": \"%s\"}" % (repostory, metadata_checksum_type)
        self.post_pulp_var("/pulp/api/v3/publications/rpm/rpm/", json_data)
    
    def create_distribution(self, name, publication_href, wait_for_task = True):
        json_data = "{\"name\": \"%s\"}" % name
        self.post_pulp_var("/pulp/api/v3/distribution/rpm/rpm/", json_data)
        
        
class upload_interactions(base_interactions):
    
    def upload_package(self, package_file, repository = None):
        json_data = "{}"
        if repository != None:
            json_data = "{ \"repository\": \"%s\"}" % repository
        self.req_wrapper.do_post_request_multipart("%s/pulp/api/v3/content/rpm/packages/" % self.pulp_url, json_data, package_file)
        json = json_wrapper(self.req_wrapper.get_request_content())
        return json.data
    