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