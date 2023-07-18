#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 18 19:21:30 2023

@author: vandenboer
"""
import time

from wrappers import req_wrapper, json_wrapper, regex_filter
from pathlib import Path

class base_interactions():
    def __init__(self, pulp_url, username, password):
        self.pulp_url = pulp_url
        self.username = username
        self.password = password
        self.req_wrapper = req_wrapper(username, password)
        
    def get_pulp_var(self, var_name, sub_url, json_data):
        req = self.req_wrapper.do_get_request("%s%s" % (self.pulp_url, sub_url), json_data)
        json = req.json() #json_wrapper(self.req_wrapper.get_request_content(req))
        result = []
        for i in json['results']:
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
        elif state == "running" or state == "waiting":
            return False
        else:
            raise Exception("Unknown state: %s" % state)
        
    def is_subtask_completed(self, task_href, subtask_name):
        task_json = self.show_href(task_href)
        for i in task_json["progress_reports"]:
            if i["code"] == subtask_name:
                state = i["state"]
                if state == "completed":
                    return True
                elif state == "running" or state == "waiting":
                    return False
                else:
                    raise Exception("Unknown state: %s" % state)
        
    def wait_for_task(self, task_href):
        while self.show_href(task_href)["state"] == "waiting":
            time.sleep(0.1)
        task_json = self.show_href(task_href)
        print("Waiting for task: %s" % task_json["name"])
        if task_json["progress_reports"] == []:
            while not self.is_task_completed(task_href):
                print('.', end='')
                time.sleep(1)
            print(".done")
        else:
            for i in task_json["progress_reports"]:
                print("Waiting for subtask: %s" % i["code"], end='')
                while not self.is_subtask_completed(task_href, i["code"]):
                    print('.', end='')
                    time.sleep(1)
                print(".done")
    
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
    
    def _get_wrap(self, var_name, url, json):
        result = self.get_pulp_var(var_name, url, json)
        if len(result) != 0:
            return result[0]
        
    def _get_wrap_no_limit(self, var_name, url, json):
        limit = 100
        offset = 0
        data = self.get_pulp_var(var_name, "%s&limit=%s" % (url, limit), json)
        result = data
        while len(data) == limit:
            offset += limit
            data = self.get_pulp_var(var_name, "%s&limit=%s&offset=%s" % (url, limit, offset), json)
            result += data
        return result
        
    def get_repository_name(self, href):
        return self.show_href(href)['name']
    
    def get_repository_href(self, name):
        return self._get_wrap("pulp_href", "/pulp/api/v3/repositories/rpm/rpm/?name=%s&offset=0&limit=1" % name, "{}")
    
    def get_all_repositories(self):
        return self.get_pulp_var("pulp_href", "/pulp/api/v3/repositories/rpm/rpm/", "{}")
        
    def get_repository_version_href(self, name):
        return self._get_wrap("latest_version_href", "/pulp/api/v3/repositories/rpm/rpm/?name=%s&offset=0&limit=1" % name, "{}")
        
    def get_remote_href(self, name):
        return self._get_wrap("pulp_href", "/pulp/api/v3/remotes/rpm/rpm/?name=%s&offset=0&limit=1" % name, "{}")
    
    def get_remote_name(self, href):
        return self.show_href(href)['name']

    def get_all_remotes(self):
        return self.get_pulp_var("pulp_href", "/pulp/api/v3/remotes/rpm/rpm/", "{}")
        
    def get_distribution_href(self, name):
        return self._get_wrap("pulp_href", "/pulp/api/v3/distributions/rpm/rpm/?name=%s&offset=0&limit=1" % name, "{}")
    
    def get_distribution_name(self, href):
        return self.show_href(href)['name']

    def get_all_distributions(self):
        return self.get_pulp_var("pulp_href", "/pulp/api/v3/distributions/rpm/rpm/", "{}")
        
    def get_package_href(self, name):
        return self._get_wrap("pulp_href", "/pulp/api/v3/content/rpm/packages/?name=%s&offset=0&limit=1" % name, "{}")
    
    def get_all_repository_package_names(self, repository_name):
        data = self._get_wrap_no_limit("name", "/pulp/api/v3/content/rpm/packages/?fields=name&repository_version=%s" % self.get_repository_version_href(repository_name), "{}")
        return data
        
    def get_all_repository_non_package_href(self, repository_name):
        list = []
        types = ["advisories","distribution_trees","modulemd_defaults","modulemds","packagecategories","packageenvironments","packagegroups","packagelangpacks","repo_metadata_files"]
        for t in types:
            data = self._get_wrap_no_limit("pulp_href", "/pulp/api/v3/content/rpm/%s/?fields=pulp_href&repository_version=%s" % (t, self.get_repository_version_href(repository_name)), "{}")
            list += data
        return list
    
    def get_status(self):
        req = self.req_wrapper.do_get_request("%s/pulp/api/v3/status/" % self.pulp_url)
        json = json_wrapper(self.req_wrapper.get_request_content(req))
        return json.data



class create_interactions(base_interactions):
    
    def create_repository(self, name, remote = None, wait_for_task = True):
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
        
    
        
class upload_interactions(base_interactions):
  
    def upload_comps(self, comps_file, repository = None, replace = False, wait_for_task = True):
        data = {}
        if repository != None:
            data["repository"] = (None, repository)
        data["replace"] = (None, replace)
        data["file"] = ("file" , Path(comps_file).read_bytes(), "application/octet-stream")
        json = json_wrapper(self.req_wrapper.do_post_request_multipart("%s/pulp/api/v3/rpm/comps/" % self.pulp_url, data).content.decode())
        task_href = json.data["task"]
        if wait_for_task:
            self.wait_for_task(task_href)
        return task_href
        
    # def upload_package(self, package_file, relative_path = "/", repository = None):
    #     upload_href = self.create_upload(package_file)
    #     append = ""
    #     if repository != None:
    #         append = ", \"repository\": \"%s\"" % repository
    #     json_data = "{ \"file\":\"%s\" , \"relative_path\":\"%s\", \"upload\":\"%s\" %s }" % (package_file, relative_path, upload_href, append)
      
    #     self.req_wrapper.do_post_request_multipart("%s/pulp/api/v3/content/rpm/packages/" % self.pulp_url, json_data, package_file)
    #     json = json_wrapper(self.req_wrapper.get_request_content())
      
    #     # TODO: create upload, use PUT method
    #     self.do_upload(package_file)
      
    # def do_upload(self, package_file):
    #     buffer_size = 1024
    #     count = 0
    #     with io.open(package_file, 'rb') as fp:
    #         while (chunk := fp.read(buffer_size)):
    #             length = len(chunk)
    #             json_data = "{ \"Content-Range\":\"bytes %s-%s/*\"" % (count, count - 1 + length)
    #             self.do_put_chunk(chunk, count, count -1 + length)
    #             count = count + length
          
    # def do_put_chunk(self, bytes, start_byte, length, sha256 = None):
    #     self.req_wrapper.do_put_request("url", file)
  
    # def create_upload(self, package_file):
    #     file_size = os.path.getsize(package_file)
    #     json_data = self.post_pulp_var("/pulp/api/v3/uploads", "{ \"size\":\"%s\" }" % file_size)
    #     return json_data["pulp_href"]
    
    
    

class function_interactions(base_interactions):
    
    def __init__(self, pulp_url, username, password):
        super(function_interactions, self).__init__(pulp_url, username, password)
        self.getter = get_interactions(pulp_url, username, password)
        self.creator = create_interactions(pulp_url, username, password)
        self.deleter = delete_interactions(pulp_url, username, password)
        
    def sync_repository_with_remote(self, repository, remote = None, sync_policy = "mirror_complete", wait_for_task = True):
        append = ""
        if remote != None:
            append = ", \"remote\": \"%s\"" % remote
        json_data = "{ \"sync_policy\": \"%s\" %s}" % (sync_policy, append)
        try:
            try:
                task_href = self.post_pulp_var("%ssync/" % repository, json_data)["task"]
            except Exception:
                task_href = self.post_pulp_var("%s/sync/" % repository, json_data)["task"]
            if wait_for_task:
                self.wait_for_task(task_href)
        except Exception as e:
            json = self.show_href(task_href)
            if json["state"] != "failed":
                raise e
            elif sync_policy == "mirror_complete" and "MIRROR_INCOMPATIBLE_REPO_ERR_MSG" in json["error"]["traceback"]:
                print("MIRROR_INCOMPATIBLE_REPO_ERR_MSG: Trying \"additive\" instead")
                self.sync_repository_with_remote(repository, remote, "additive", wait_for_task)
            else:
                raise e
                
        
    
    def copy(self, source_repository_name, destination_repository_name, package_list = [], dependency_list = [], wait_for_task = True):
        src_href = self.getter.get_repository_version_href(source_repository_name)
        dst_href = self.getter.get_repository_href(destination_repository_name)
        json_data = "{ \"config\": [ { \"source_repo_version\":\"%s\", \"dest_repo\":\"%s\"" % (src_href, dst_href)
        if len(package_list) > 0:
            pkg_list = ", \"content\": ["
            start = True
            for p in package_list:
                if not start:
                    pkg_list += ","
                if p.startswith("/pulp/api/v3/content/"):
                    pkg_list += "\"%s\"" % p
                else:
                    pkg_list += "\"%s\"" % self.getter.get_package_href(p)
                start = False
            json_data += ("%s]" % pkg_list)
        response = self.post_pulp_var("/pulp/api/v3/rpm/copy/", json_data + "} ], \"dependency_solving\": \"true\" }")
        if wait_for_task:
            self.wait_for_task(response["task"])
        count = 1
        for i in dependency_list:
            dep_href = self.getter.get_repository_version_href(i)
            temp_repository = self.creator.create_repository("temp-repository-%d" % count)
            t_json = json_data + "} , { \"source_repo_version\":\"%s\", \"dest_repo\":\"%s\", \"content\": [] } ], \"dependency_solving\": \"true\" }" % (dep_href, temp_repository)
            response = self.post_pulp_var("/pulp/api/v3/rpm/copy/", t_json)
            if wait_for_task:
                self.wait_for_task(response["task"])
            count += 1
        for i in range(count - 1, 1, -1):
            self.copy("temp-repository-%d" % i, "temp-repository-%d" % (i - 1))
            self.deleter.delete_repository("temp-repository-%d" % i)
        if count > 1:
            self.copy("temp-repository-1", destination_repository_name)
            self.deleter.delete_repository("temp-repository-1")
            
    # Default, filter = include
    def copy_filter(self, regex, source_repository_name, destination_repository_name, package_list = [], dependency_list = [], invert_filter = False, wait_for_task = True):
        regex_f = regex_filter(regex)
        result_list = []
        if package_list == []:
            package_list = self.getter.get_all_repository_package_names(source_repository_name)
        if invert_filter:
            pkg_list = regex_f.invert_filter_list(package_list)
        else:
            pkg_list = regex_f.filter_list(package_list)
        result_list += pkg_list
        result_list += self.getter.get_all_repository_non_package_href(source_repository_name)
        self.copy(source_repository_name, destination_repository_name, package_list=list(result_list), dependency_list=dependency_list, wait_for_task=wait_for_task)
    
    def copy_filter_multiple(self, regex_list, source_repository_name, destination_repository_name, package_list = [], dependency_list = [], wait_for_task = True):
        excludes = []
        includes = []
        for filter, invert in regex_list.items():
            if invert:
                excludes.append(filter)
            else:
                includes.append(filter)
        self.copy_filters_multiple(source_repository_name, destination_repository_name, includes, excludes, package_list, dependency_list, wait_for_task)

    def copy_filters_multiple(self, source_repository_name, destination_repository_name, includes = [], excludes = [], package_list = [], dependency_list = [], wait_for_task = True):
        repo_name = "intermediate_repo"
        self.creator.create_repository(repo_name)
        self.copy_include_filters(excludes, source_repository_name, repo_name, package_list, dependency_list, wait_for_task)
        if includes == []:
            self.copy(repo_name, destination_repository_name, package_list, dependency_list, wait_for_task)
        else:
            self.copy_include_filters(includes, repo_name, destination_repository_name, package_list, dependency_list, wait_for_task)        
        self.deleter.delete_repository(repo_name)

    def copy_include_filters(self, includes, source_repository_name, destination_repository_name, package_list = [], dependency_list = [], wait_for_task = True):
        for include in includes:
            self.copy_filter(include, source_repository_name, destination_repository_name, package_list, dependency_list, False, wait_for_task)
            
            
    def copy_exclude_filters(self, excludes, source_repository_name, destination_repository_name, package_list = [], dependency_list = [], wait_for_task = True):
        t_repo_1 = "temporary_repo_1"
        t_repo_2 = "temporary_repo_1"
        self.creator.create_repository(t_repo_1)
        self.creator.create_repository(t_repo_2)
        self.copy(source_repository_name, t_repo_1)
        for exclude in excludes:
            self.copy_filter(exclude, t_repo_1, t_repo_2, package_list, dependency_list, True, wait_for_task)
            self.deleter.delete_repository(t_repo_1)
            self.creator.create_repository(t_repo_1)
            self.copy(t_repo_2, t_repo_1)
            self.deleter.delete_repository(t_repo_2)
            self.creator.create_repository(t_repo_2)
        self.copy(t_repo_1, destination_repository_name)
        self.deleter.delete_repository(t_repo_1)
        self.deleter.delete_repository(t_repo_2)
            
        
        
class delete_interactions(base_interactions):
    
    def __init__(self, pulp_url, username, password):
        super(delete_interactions, self).__init__(pulp_url, username, password)
        self.getter = get_interactions(pulp_url, username, password)
    
    def delete_href(self, href):
        self.req_wrapper.do_delete_request("%s%s" % (self.pulp_url, href))
        
    def delete_repository(self, name):
        self.delete_href(self.getter.get_repository_href(name))
        
    def delete_remote(self, name):
        self.delete_href(self.getter.get_remote_href(name))
        
    def delete_distribution(self, name):
        self.delete_href(self.getter.get_distribution_href(name))
        
    def delete_all(self):
        repos = self.getter.get_all_repositories()
        distros = self.getter.get_all_distributions()
        remotes = self.getter.get_all_remotes()
        
        print("Cleaning all repositories, remotes and distributions")
        for i in repos:
            print('.', end='')
            self.delete_href(i)
        for i in distros:
            print('.', end='')
            self.delete_href(i)
        for i in remotes:
            print('.', end='')
            self.delete_href(i)
        
        while self.getter.get_all_repositories() != [] or self.getter.get_all_remotes() != [] or self.getter.get_all_distributions() != []:
            print('.', end='')
            time.sleep(1)
        print(".done")