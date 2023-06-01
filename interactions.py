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
        #self.uploader = upload_interactions(pulp_url, username, password)
        self.functions = function_interactions(pulp_url, username, password)
        self.deleter = delete_interactions(pulp_url, username, password)



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
            if var_name == "":
                result.append(i)
            else:
                result.append(i[var_name])  
        return result
    
    def post_pulp_var(self, sub_url, json_data):
        self.req_wrapper.do_post_request("%s%s" % (self.pulp_url, sub_url), json_data)
        json = json_wrapper(self.req_wrapper.get_request_content())
        return json.data
    
    def show_href(self, href):
        self.req_wrapper.do_get_request("%s%s" % (self.pulp_url, href))
        json = json_wrapper(self.req_wrapper.get_request_content())
        return json.data
    
    def is_task_completed(self, task_href):
        self.req_wrapper.do_get_request("%s%s" % (self.pulp_url, task_href))
        json = json_wrapper(self.req_wrapper.get_request_content())
        state = json.data["state"]
        if state == "completed":
            return True
        elif state == "running":
            return False
        else:
            raise Exception("Unknown state %s" % state)
        
    
    def wait_for_task(self, task_href):
        task_json = self.show_href(task_href)
        print("Waiting for task: %s" % task_json["name"])
        while not self.is_task_completed(task_href):
            print('.', end='')
            time.sleep(1)
        print()
    
    def wait_for_all_task_type(self, task_type):
        self.get_pulp_var("pulp_href", "/pulp/api/v3/tasks/?state=completed&name=%s" % task_type, "{}")
        json = json_wrapper(self.req_wrapper.get_request_content())
        do_loop = True
        while do_loop:
            do_loop = False
            for i in json.data["results"]:
                if i["name"] is task_type:
                    if self.is_task_completed(i["pulp_href"]):
                        do_loop = True
                        break
    
    def wait_for_all_tasks(self):
        self.get_pulp_var("pulp_href", "/pulp/api/v3/tasks/?state=running", "{}")
        json = json_wrapper(self.req_wrapper.get_request_content())
        do_loop = True
        
        while do_loop:
            do_loop = False
            for i in json.data["results"]:
                if self.is_task_completed(i["pulp_href"]):
                    do_loop = True
                    break



class get_interactions(base_interactions):
    
    def get_repo_href(self, name):
        result = self.get_pulp_var("pulp_href", "/pulp/api/v3/repositories/rpm/rpm/", "{\"name\": \"%s\"}" % name)
        if len(result) != 0:
            return result[0]
    
    def get_all_repositories(self):
        return self.get_pulp_var("pulp_href", "/pulp/api/v3/repositories/rpm/rpm/", "{}")
        
    def get_repo_version_href(self, name):
        result =  self.get_pulp_var("latest_version_href", "/pulp/api/v3/repositories/rpm/rpm/", "\{\"name\": \"%s\"}" % name)
        if len(result) != 0:
            return result[0]
        
    def get_remote_href(self, name):
        result =  self.get_pulp_var("pulp_href", "/pulp/api/v3/remotes/rpm/rpm/", "{\"name\": \"%s\"}" % name)
        if len(result) != 0:
            return result[0]
        
    def get_all_remotes(self):
        return self.get_pulp_var("pulp_href", "/pulp/api/v3/remotes/rpm/rpm/", "{}")
        
    def get_distribution_href(self, name):
        result =  self.get_pulp_var("pulp_href", "/pulp/api/v3/distributions/rpm/rpm/", "{\"name\": \"%s\"}" % name)
        if len(result) != 0:
            return result[0]
        
    def get_all_distributions(self):
        return self.get_pulp_var("pulp_href", "/pulp/api/v3/distributions/rpm/rpm/", "{}")
        
    def get_package_href(self, name):
        result =  self.get_pulp_var("pulp_href", "/pulp/api/v3/content/rpm/packages/", "{\"name\": \"%s\"}" % name)
        if len(result) != 0:
            return result[0]



class create_interactions(base_interactions):
    
    def create_repo(self, name, remote = None, wait_for_task = True):
        append = ""
        if remote != None:
            append = ", \"remote\":\"%s\"" % remote
        json_data = "{\"name\": \"%s\" %s}" % (name, append)
        return self.post_pulp_var("/pulp/api/v3/repositories/rpm/rpm/", json_data)['pulp_href']
        
    def create_remote(self, name, remote_url, policy = "on_demand", username = None, password = None, wait_for_task = True):
        append = ""
        if username != None and password != None:
            append = ", \"username\": \"%s\", \"password\": \"%s\""
        json_data = "{\"name\": \"%s\", \"url\": \"%s\", \"policy\": \"%s\" %s }" % (name, remote_url, policy, append)
        return self.post_pulp_var("/pulp/api/v3/remotes/rpm/rpm/", json_data)['pulp_href']
        
    def create_publication(self, repository, metadata_checksum_type="sha256", wait_for_task = True):
        json_data = "{ \"repository\": \"%s\", \"metadata_checksum_type\": \"%s\"}" % (repository, metadata_checksum_type)
        task_href = self.post_pulp_var("/pulp/api/v3/publications/rpm/rpm/", json_data)["task"]
        if wait_for_task:
            self.wait_for_task(task_href)
        json = self.show_href(task_href)
        return json["created_resources"][0]
        
    
    def create_distribution(self, name, base_path, publication_href, wait_for_task = True):
        json_data = "{\"name\": \"%s\", \"base_path\":\"%s\", \"publication\": \"%s\"}" % (name, base_path, publication_href)
        task_href = self.post_pulp_var("/pulp/api/v3/distributions/rpm/rpm/", json_data)["task"]
        json = self.show_href(task_href)
        return json["created_resources"][0] 
        
        
# class upload_interactions(base_interactions):
    
#     def upload_package(self, package_file, relative_path = "/", repository = None):
#         upload_href = self.create_upload(package_file)
#         append = ""
#         if repository != None:
#             append = ", \"repository\": \"%s\"" % repository
#         json_data = "{ \"file\":\"%s\" , \"relative_path\":\"%s\", \"upload\":\"%s\" %s }" % (package_file, relative_path, upload_href, append)
        
#         self.req_wrapper.do_post_request_multipart("%s/pulp/api/v3/content/rpm/packages/" % self.pulp_url, json_data, package_file)
#         json = json_wrapper(self.req_wrapper.get_request_content())
        
#         # TODO: create upload, use PUT method
#         self.do_upload(package_file)
        
    
#     def do_upload(self, package_file):
#         buffer_size = 1024
#         count = 0
#         with io.open(package_file, 'rb') as fp:
#             while (chunk := fp.read(buffer_size)):
#                 length = len(chunk)
#                 json_data = "{ \"Content-Range\":\"bytes %s-%s/*\"" % (count, count - 1 + length)
#                 self.do_put_chunk(chunk, count, count -1 + length)
#                 count = count + length
            
#     def do_put_chunk(self, bytes, start_byte, length, sha256 = None):
#         self.req_wrapper.do_put_request("url", file)
    
#     def create_upload(self, package_file):
#         file_size = os.path.getsize(package_file)
#         json_data = self.post_pulp_var("/pulp/api/v3/uploads", "{ \"size\":\"%s\" }" % file_size)
#         return json_data["pulp_href"]
    
    

class function_interactions(base_interactions):
    
    def __init__(self, pulp_url, username, password):
        super(function_interactions, self).__init__(pulp_url, username, password)
        self.getter = get_interactions(pulp_url, username, password)
        
    def sync_repository_with_remote(self, repository, remote = None, sync_policy = "mirror_complete", wait_for_task = True):
        append = ""
        if remote != None:
            append = ", \"remote\": \"%s\"" % remote
        json_data = "{ \"sync_policy\": \"%s\" %s}" % (sync_policy, append)
        task_href = self.post_pulp_var("%ssync/" % repository, json_data)["task"]
        if wait_for_task:
            self.wait_for_task(task_href)
    
    def copy(self, source_repository_name, destination_repository_name, package_list = [], dependency_list = []):
        src_href = self.getter.get_repo_version_href(source_repository_name)
        dst_href = self.getter.get_repo_href(destination_repository_name)
        json_data = "{ \"config\": [ { \"source_repo_version\":\"%s\", \"dest_repo\":\"%s\"" % (src_href, dst_href)
        if len(package_list) > 0:
            pkg_list = ", \"content\": %s" % package_list
            json_data += (", %s" % pkg_list)
        response = self.post_pulp_var("/pulp/api/v3/rpm/copy/", json_data + "} ], \"dependency_solving\": true }")
        print('Waiting for task %s' % response)
        self.wait_for_task(response)
        for i in dependency_list:
            dep_href = self.getter.get_repo_version_href(i)
            t_json = json_data + "} , { \"source_repo_version\":\"%s\", \"dest_repo\":\"%s\", \"content\": [] } ], \"dependency_solving\": true }" % (dep_href, dst_href)
            response = self.post_pulp_var("/pulp/api/v3/rpm/copy/", t_json)
            print('Waiting for task %s' % response)
            self.wait_for_task(response)
            
            
class delete_interactions(base_interactions):
    
    def __init__(self, pulp_url, username, password):
        super(delete_interactions, self).__init__(pulp_url, username, password)
        self.getter = get_interactions(pulp_url, username, password)
    
    def delete_href(self, href):
        self.req_wrapper.do_delete_request("%s%s" % (self.pulp_url, href))
        
    def delete_repository(self, name):
        self.delete_href(self.getter.get_repo_href(name))
        
    def delete_remote(self, name):
        self.delete_href(self.getter.get_remote_href(name))
        
    def delete_distribution(self, name):
        self.delete_href(self.getter.get_distribution_href(name))
        
    def delete_all(self):
        repos = self.getter.get_all_repositories()
        distros = self.getter.get_all_distributions()
        remotes = self.getter.get_all_remotes()
        
        for i in repos:
            self.delete_href(i)
        for i in distros:
            self.delete_href(i)
        for i in remotes:
            self.delete_href(i)
            
        print("Cleaning all repositories, remotes and distributions")
        while self.getter.get_all_repositories() != [] or self.getter.get_all_remotes() != [] or self.getter.get_all_distributions() != []:
            print('.', end='')
            time.sleep(1)
        print()
            
        
        
        
        
        
        
        
