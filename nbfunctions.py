# import python modules
import requests
import time
import urllib3
import pprint
import json
import logging
import re
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger=logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) 

##############################################################################
#Parse syslog message from rsyslog via stdin
##############################################################################

def find_ip_addr(msg, taskID):
    syslogmsg = msg.rstrip()

    ip_addr = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', syslogmsg)
    ip_addr = ip_addr.group()

    #logging
    logger.info("TaskID: " + taskID + " | IP Address from syslog: " + ip_addr)

    return ip_addr

##############################################################################
#Login and obtain Token
##############################################################################

def api_login (nb_url, headers, taskID, user, password, auth_id=""):
    """ Logs into NetBrain API and return Token """

    body = {
        "username": user,
        "password": password,
        "authentication_id": auth_id
    }

    login_url = "/ServicesAPI/API/V1/Session"

    try:
        # Do the HTTP request
        response = requests.post(nb_url + login_url, headers=headers, data = json.dumps(body), verify=False)
        # Check for HTTP codes other than 200
        if response.status_code == 200:
            # Decode the JSON response into a dictionary and use the data
            js = response.json()
            # Put token into variable to use later
            token = js['token']
            logger.info("TaskID: " + taskID + " | Login Successful")
        else:
            logger.error("TaskID: " + taskID + " | Get token failed! - " + str(response.text))
    except Exception as e:
        logger.error("TaskID: " + taskID + " | Get token failed! - " + str(e))

    return token

##################################################################################
#Set current domain
##################################################################################

def set_domain(nb_url, headers, taskID, domain_id, tenant_id):
    """ Set working Tenant and Domain """
    full_url = nb_url + "/ServicesAPI/API/V1/Session/CurrentDomain"

    body = {
        "tenantId": tenant_id,
        "domainId": domain_id
    }

    try:
        # Do the HTTP request
        response = requests.put(full_url, data=json.dumps(body), headers=headers, verify=False)
        # Check for HTTP codes other than 200
        if response.status_code == 200:
            # Decode the JSON response into a dictionary and use the data
            # result = response.json()
            logger.info("TaskID: " + taskID + " | Set Domain Successful")
        elif response.status_code != 200:
            logger.error("TaskID: " + taskID + " | " + str(response.text))

    except Exception as e:
        logger.error("TaskID: " + taskID + " | " + str(e))

    return

#################################################################################
#change IP to Hostname
#################################################################################

def lookup_hostname(nb_url, headers, taskID, ip_addr):
    """ Convert syslog source IP address to NetBrain hostname and return hostname """
    full_url= nb_url + "/ServicesAPI/API/V1/CMDB/Devices"

    query = {"ip" : ip_addr}

    try:
        response = requests.get(full_url, headers=headers, params = query, verify=False)
        if response.status_code == 200:
            result = response.json()
            device = result['devices'][0]['hostname']
            logger.info("TaskID: " + taskID + " | Hostname: " + str(device))
            return device
        else:
            logger.error("TaskID: " + taskID + " | Get Devices failed! - " + str(response.text))
    except Exception as e:
        logger.error("TaskID: " + taskID + " | " + str(e))

#################################################################################
# Trigger Event Driven Automation
#################################################################################

def PublishEvent(nb_url, headers, taskID, ip_addr, deviceName):
    """ Trigger Event Driven Automation """
    full_url = nb_url + "/ServicesAPI/API/V1/CMDB/EventDriven/Events"
   
    Event_Data = {
        "type": "syslog-event",
        "sys_updated_on": str(datetime.datetime.now()),
        "u_source_ip_new": ipAddr,
        "devicename": deviceName,
        "opened_by": {
            "link": "rsyslog",
            "value": taskID
        }
    }

    try:
        response = requests.post(api_full_url, data=json.dumps(Event_Data), headers=headers, verify=False)
        if response.status_code == 200:
            #result = response.json()
            logger.info("TaskID: " + taskID + " | Event Automation Triggered Successfully")
        else:
            logger.error("TaskID: " + taskID + " | Event Automation Trigger Failed - " + str(response.text))

    except Exception as e:
        logger.error("TaskID: " + taskID + " | " + str(e))

####################################################
#logout
####################################################

def logout(nb_url, headers, taskID):
    """ Logout of NetBrain API """
    full_url = nb_url + "/ServicesAPI/API/V1/Session"
    try:
        # Do the HTTP request
        response = requests.delete(full_url, headers=headers, verify=False)
        # Check for HTTP codes other than 200
        if response.status_code == 200:
            # Decode the JSON response into a dictionary and use the data
            #result = response.json()
            logger.info("TaskID: " + taskID + " | Logout of Session Completed Successfully")
        else:
            logger.error("TaskID: " + taskID + " | Session logout failed! - " + str(response.text))

    except Exception as e:
        logger.error("TaskID: " + taskID + " | " + str(e))