##!/usr/bin/env python

"""A skeleton for a python rsyslog output plugin
   Copyright (C) 2014 by Adiscon GmbH
   This file is part of rsyslog.
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
 
         http://www.apache.org/licenses/LICENSE-2.0
         -or-
         see COPYING.ASL20 in the source distribution
 
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
import select
import requests
import urllib3
import json
import sys
import logging
import datetime
import time
import uuid
import concurrent.futures
import threading
# Config & NetBrain API Functions
import config
import nbfunctions as nb

# Global Threading Options
thread_local = threading.local()

# skeleton config parameters
pollPeriod = 0.0001 # the number of seconds between polling for new messages
maxAtOnce = 1024  # max nbr of messages that are processed within one batch

# Create and configure logger 
logging.basicConfig(filename=config.logLocation+config.logfile, 
                    format='%(asctime)s - %(levelno)s-%(levelname)s - %(message)s', 
                    filemode='a')

# Creating a logging object 
logger=logging.getLogger(__name__)

# Setting the threshold of logger to DEBUG 
logger.setLevel(logging.DEBUG) 

def onInit():
	""" Do everything that is needed to initialize processing (e.g.
	    open files, create handles, connect to systems...)
    """

def onReceive(msgs):
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        # Start the load operations and mark each future with its URL
        future_to_msg = {executor.submit(netbrainTrigger, msg): msg for msg in msgs}
        for future in concurrent.futures.as_completed(future_to_msg):
            msg = future_to_msg[future]
            try:
                data = future.result()
            except Exception as e:
                logger.error("TaskID: " + str(data) + " | Task Failed - " + str(e))
            else:
                logger.info("TaskID: " + str(data) + " | Task Successful")


def netbrainTrigger(msg):
    # Set general options
    nb_url = config.nb_url
    tenant_id = config.tenant_id
    domain_id = config.domain_id
    username = config.username
    password = config.password
    auth_id = config.auth_id
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    taskID = str(uuid.uuid4())
    logger.info("TaskID: " + taskID + " | Task Starting")

    # Lookup IP from syslog message
    ip_addr = nb.find_ip_addr(msg, taskID)

    # Login to NetBrain, add token to header
    token = nb.api_login(nb_url, headers, taskID, username, password, auth_id)
    headers["Token"] = token

    # Set NetBrain working domain
    nb.set_domain(nb_url, headers, taskID, domain_id, tenant_id)

    # Lookup device hostname in NetBrain
    device = nb.lookup_hostname(nb_url, headers, taskID, ip_addr)

    # Call Event Driven Automation Trigger
    nb.PublishEvent(nb_url, headers, taskID, ip_addr, device)

    # Logout of session
    nb.logout(nb_url, headers, taskID)
    return taskID


def onExit():
	""" Do everything that is needed to finish processing (e.g.
	    close files, handles, disconnect from systems...). This is
	    being called immediately before exiting.
	"""

# Do not modify
onInit()
keepRunning = 1
while keepRunning == 1:
    while keepRunning and sys.stdin in select.select([sys.stdin], [], [], pollPeriod)[0]:
        msgs = []
        msgsInBatch = 0
        while keepRunning and sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            line = sys.stdin.readline()
            if line:
                msgs.append(line)
            else: # an empty line means stdin has been closed
                keepRunning = 0
            msgsInBatch = msgsInBatch + 1
            if msgsInBatch >= maxAtOnce:
                break;
        if len(msgs) > 0:
            onReceive(msgs)
            sys.stdout.flush() # very important, Python buffers far too much!
onExit()