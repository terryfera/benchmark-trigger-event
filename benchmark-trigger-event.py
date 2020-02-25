import requests
import json
import time
import datetime
import requests.packages.urllib3 as urllib3
import uuid
urllib3.disable_warnings()
# Need to install requests package for python
# pip install requests

user = "admin"                               # account to log in to your NetBrain Domain       
pwd = "P@ssw0rd"                               # password 
host_url = "https://nb80.thegorbit.net"               # The URL of your NetBrain Domain
headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
headers1 = {'Content-Type': 'application/json', 'Accept': 'application/json'}
triggerTaskID = str(uuid.uuid1())
ipAddr = "10.0.100.1"
deviceName = "dc-rt01"


'''
Get token for netbrain
'''
TENANT = 'Initial Tenant'
DOMAIN = 'LAB'

def getTokens(user,password):
    login_api_url = r"/ServicesAPI/API/V1/Session"
    Login_url = host_url + login_api_url
    data = {
        "username": user,
        "password": password
    }
    token = requests.post(Login_url, data=json.dumps(
        data), headers=headers, verify=False)
    if token.status_code == 200:
        print(token.json())
        return token.json()["token"]
    else:
        return "error"
# get token 
token = getTokens(user,pwd)
headers["Token"] = token

def get_tenant_domain_id():

    tenant_id_url = '/ServicesAPI/API/V1/CMDB/Tenants' 
    full_url = host_url + tenant_id_url
    data = requests.get(full_url,headers=headers,verify=False)
    # tenant_id = '78a825ef-24bd-729d-f56f-a1ad2b79f2ff'
    # domain_id = '36700aff-c585-4f23-95eb-8ea00214b778'
    print(data.json())
    if data.status_code == 200:
        for tenant in data.json()['tenants']:
            if TENANT == tenant['tenantName']:
                tenant_id = tenant['tenantId']
        if tenant_id:
            domain_id_url = '/ServicesAPI/API/V1/CMDB/Domains'
            full_domain_url = host_url +domain_id_url
            domain_data = requests.get(full_domain_url,params={'tenantId':tenant_id},headers=headers,verify=False)
            print(domain_data.json())
            if domain_data.status_code == 200:
                for domain in domain_data.json()['domains']:
                    if DOMAIN == domain['domainName']:
                        domain_id = domain['domainId']
        return tenant_id,domain_id
    else:
        return tenant_id,domain_id

tenant_id,domain_id = get_tenant_domain_id()
print(tenant_id,domain_id)
headers["TenantGuid"]= tenant_id
headers["DomainGuid"]= domain_id

def Logout():
    logout_url = "/ServicesAPI/API/V1/Session"
    time.sleep(2)
    full_url = host_url + logout_url
    body = {
        "token": token
        }
    result = requests.delete(full_url, data=json.dumps(body), headers=headers, verify=False)
    print('Logout: ' + str(result.json()))
    if result.status_code == 200:
        print("LogOut success...")
    else:
        data = "errorCode" + "LogOut API test failed... "
        return result.json()
# Trigger API function

def PublishEvent(Event_Data):
    # Trigger  API url
    API_URL = r"/ServicesAPI/API/V1/CMDB/EventDriven/Events"
    # Trigger API payload
    print(headers)
    api_full_url = host_url + API_URL
    print('api_full_url: ' + api_full_url)
    api_result = requests.post(api_full_url, data=json.dumps(Event_Data), headers=headers, verify=False)
    if api_result.status_code == 200:
        return api_result.json()
    else:
        return api_result.json()


if __name__ =="__main__":
    #tenant_id,domain_id = get_tenant_domain_id()
    #print(tenant_id,domain_id)
    # tenant_id = '0b7eb490-d9cf-aacc-672c-ff9d58a47032'
    # domain_id = '53e4b108-086e-4b6f-95b8-ee23bd7d142a'
    Event_Data = {
        "type": "syslog-event",
        "sys_updated_on": str(datetime.datetime.now()),
        "u_source_ip_new": ipAddr,
        "devicename": deviceName,
        "opened_by": {
            "link": "rsyslog",
            "value": triggerTaskID
        }
    }
print(PublishEvent(Event_Data))
