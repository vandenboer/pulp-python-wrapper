#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  2 13:06:49 2023

@author: vandenboer
"""

from interactions import get_interactions
from interactions import create_interactions
from interactions import function_interactions
from interactions import delete_interactions
from interactions import upload_interactions

import traceback
import json

class pulp_manager():
    
    def __init__(self, pulp_url, username, password):
        self.username = username
        self.password = password
        self.getter = get_interactions(pulp_url, username, password)
        self.creator = create_interactions(pulp_url, username, password)
        self.functions = function_interactions(pulp_url, username, password)
        self.deleter = delete_interactions(pulp_url, username, password)
        self.uploader = upload_interactions(pulp_url, username, password)
        
    def wait_for_server(self):
        do_loop = True
        while do_loop:
            try:
                self.getter.get_status()
                do_loop = False
            except Exception:
                pass
            
        
    def create_repo_and_remote(self, repository_name, remote_url, remote_username = None, remote_password = None, use_pulp_login=False, policy = None):
        if policy == None:
            policy = "on_demand"
        if remote_username != None and remote_password != None:
            remote = self.creator.create_remote(repository_name + "_remote", remote_url, policy=policy, username=remote_username, password=remote_password)
        elif use_pulp_login == True:
            remote = self.creator.create_remote(repository_name + "_remote", remote_url, policy=policy, username=self.username, password=self.password)
        else:
            remote = self.creator.create_remote(repository_name + "_remote", remote_url, policy=policy)
        return self.creator.create_repository(repository_name, remote), remote
        
    def create_repo_and_remote_with_sync(self, repository_name, remote_url, remote_username = None, remote_password = None, use_pulp_login=False, policy = None):
        repository, remote = self.create_repo_and_remote(repository_name, remote_url)
        self.functions.sync_repository_with_remote(repository)
        return repository, remote
    
    def publish_repository(self, repository_href, distribution_name = None, base_path = None):
        if distribution_name == None:
            distribution_name = self.getter.get_repository_name(repository_href) + "_distribution"
        if base_path == None:
            base_path = self.getter.get_repository_name(repository_href)
        publication = self.creator.create_publication(repository_href)
        self.creator.create_distribution(distribution_name, base_path, publication)
        
    def setup_from_json(self, json_input):
        if isinstance(json_input, dict):
            json_data = json_input
        else:
            json_data = json.loads(json_input)
        try:
            remote_names = self._create_remotes_from_json(json_data['remotes'])
            repository_names = self._create_repositories_from_json(json_data[''])
        except Exception as e:
            print(e)
            remote_names = []
        #try:
        repository_names = self._create_repositories_from_json(json_data['repositories'])
        #except Exception as e:
            #print(e)
            #repository_names = []
            
    
    def _create_remotes_from_json(self, remotes_json):
        for remote_name, remote_values in remotes_json.items():
            if "url" in remote_values:
                url = remote_values["url"]
            else:
                raise Exception("Remote requires \"url\" variable")
            if "policy" in remote_values:
                policy = remote_values["policy"]
            else:
                policy = "on_demand"
            username = None
            password = None
            if "username" in remote_values:
                username = remote_values["username"]
            if "password" in remote_values:
                password = remote_values["password"]
            if "@" in url:
                username = url.split("@")[0].split(":")[1].split("/")[2]
                password = url.split("@")[0].split(":")[2]
                url = url.split("@")[1]
            self.creator.create_remote(remote_name, url, policy, username, password)
    
    def _create_repositories_from_json(self, repositories_json):
        for repository_name, repository_values in repositories_json.items():
            is_created = False
            try:
                remote = None
                sync_policy = "mirror_complete"
                if "remote" in repository_values:
                    remote = repository_values["remote"]
                if "sync_policy" in repository_values:
                    sync_policy = repository_values["sync_policy"]
                self.creator.create_repository(repository_name, self.getter.get_remote_href(remote))
                if "include" in repository_values or "exclude" in repository_values:
                    excludes = []
                    if "exclude" in repository_values:
                        excludes = repository_values["exclude"]
                    includes = []
                    if "include" in repository_values:
                        includes = repository_values["include"]
                    tmp_repo = "temp_repository"
                    self.creator.create_repository(tmp_repo)
                    is_created = True
                    filters = self._gen_filter_list(excludes, includes)
                    self.functions.sync_repository_with_remote(self.getter.get_repository_href(tmp_repo), self.getter.get_remote_href(remote), sync_policy)
                    self.functions.copy_filter_multiple(filters, tmp_repo, repository_name)
                    self.deleter.delete_repository(tmp_repo)
                else:
                    self.functions.sync_repository_with_remote(self.getter.get_repository_href(repository_name), None, sync_policy)
            except Exception as e:
                print("error with repository (%s) with %s" % (repository_name, repository_values))
                traceback.print_exception(e)
                print("Skipping...")
                if is_created:
                    self.deleter.delete_repository(tmp_repo)
            
    def _gen_filter_list(self, excludes, includes):
        result = {}
        for i in excludes:
            result[i] = True
        for i in includes:
            result[i] = False
        return result
            