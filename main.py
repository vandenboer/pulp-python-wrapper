#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 23 19:21:30 2023

@author: vandenboer
"""
from interactions import pulp_manager

pmgr = pulp_manager("http://127.0.0.1:24817", "admin", "pulp-admin")
print(pmgr.getter.req_wrapper.username)
print(pmgr.getter.req_wrapper.password)
print(pmgr.getter.get_all_repositories())

print("### ENSURING CLEAN SETUP ###")
pmgr.deleter.delete_all()
print("")
print("### CREATING ###")
remote = pmgr.creator.create_remote("test-remote", "http://mirror.centos.org/centos-7/7/os/x86_64/")
repository = pmgr.creator.create_repo("test-repository", remote)
print("")

print("### FUNCTIONS ###")
pmgr.functions.sync_repository_with_remote(repository)
publication = pmgr.creator.create_publication(repository)
pmgr.creator.create_distribution("test-distribution", "test-distro", publication)