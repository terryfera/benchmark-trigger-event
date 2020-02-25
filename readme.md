# NetBrain Trigger Configuration Capture on Change

## Getting Started

This guide will walk you through how to use NetBrain's restful API and a syslog server to capture device configurations as they're changed.

### Prerequisites

* Available Linux Server (CentOS in this example)
* Syslog Server capable of executing a script based on match (rsyslog)
* Linux Server has Python 3.7 + installed
* Network devices logging to the syslog server

### Installing

**Linux Server & rsyslog setup**

>*This guide assumes Linux is installed and configured with a static IP*

1. Login to your CentOS/Linux server and verify rsyslog is installed

```bash
# rpm -qa | grep rsyslog
rsyslog-8.24.0-34.el7.x86_64
```

2. Edit the default rsyslog configuration to accept logs on UDP 514 and log to a folder in opt

> Be sure to point the logs to a folder with enough storage to write them to disk, retention depends on the logrotate setttings configured later

```bash
# vi /etc/rsyslog.conf
```

```
# rsyslog configuration file

# For more information see /usr/share/doc/rsyslog-*/rsyslog_conf.html
# If you experience problems, see http://www.rsyslog.com/doc/troubleshoot.html

#### MODULES ####

# The imjournal module bellow is now used as a message source instead of imuxsock.
$ModLoad imuxsock # provides support for local system logging (e.g. via logger command)
$ModLoad imjournal # provides access to the systemd journal
#$ModLoad imklog # reads kernel messages (the same are read from journald)
#$ModLoad immark  # provides --MARK-- message capability

# Provides UDP syslog reception
$ModLoad imudp
$UDPServerRun 514

# Provides TCP syslog reception
#$ModLoad imtcp
#$InputTCPServerRun 514


#### GLOBAL DIRECTIVES ####

# Where to place auxiliary files
$WorkDirectory /opt/rsyslog

# Use default timestamp format
$ActionFileDefaultTemplate RSYSLOG_TraditionalFileFormat

# File syncing capability is disabled by default. This feature is usually not required,
# not useful and an extreme performance hit
#$ActionFileEnableSync on

# Include all config files in /etc/rsyslog.d/
$IncludeConfig /etc/rsyslog.d/*.conf

# Turn off message reception via local log socket;
# local messages are retrieved through imjournal now.
$OmitLocalLogging on

# File to store the position in the journal
$IMJournalStateFile imjournal.state

# Templates
$template PerHost,"/opt/rsyslog/%HOSTNAME%/%HOSTNAME%-%$year%-%$month%-%$day%.log"
*.* -?PerHost
```

3. Add a configuration file for rsyslog to execute a script when seeing a log message with *Configured* in it

> Make sure to poing the binary option to your python binary and location of the benchmark trigger script files

```
# vi /etc/rsyslog.d/nb-config-capture.conf
```

```
module(load="omprog")
if $rawmsg contains 'Configured' then
action(type="omprog" binary="/usr/bin/python3 /opt/nb-script/benchmark.py")
```

4. Enable rsyslog and start the service

```bash
# systemctl enable rsyslog
# systemctl start rsyslog
```

5. Add firewall rules for rsyslog

```bash
firewall-cmd
```

6. Download the configuration capture trigger script and supporting files and place them in the location provided in the rsyslog configuration file above.

7. Copy the config_example.py file to the same directory as the rsyslog-plugin-v2.py file and name it config.py

8. Modify the config.py file with settings appropriate to your environment.

> For details on how to get Tenant and Domain details please refer to: [NetBrain API Documentation](https://github.com/NetBrainAPI/NetBrain-REST-API-V8.02/tree/master/REST%20APIs%20Documentation/Authentication%20and%20Authorization)

> Ensure that the log file location is valid, use mkdir to create it if need be

```python
# Configuration options for Triggered Benchmark

logLocation = "/opt/nb-script/logs/"
logfile = "trigger-log-task.log"

nb_url = "http://172.16.100.46"
headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
username = "username"
password = "password"
auth_id = "" # Must match external authentication name in System settings or left blank
tenant_id = "ad8dd369-3ab9-b911-ebc1-5afe50c5f621" 
domain_id = "de3e5edb-cf2c-44b7-8a48-f92b9b1b9154"
```

> After completing this your directory structure should look like this:

```bash
# ls -lh
total 24K
-rw-r--r--. 1 root root  458 Feb 24 14:26 config.py
drwxr-xr-x. 2 root root    6 Feb 24 17:37 logs
-rw-r--r--. 1 root root  12K Feb 24 14:26 nbfunctions.py
-rw-r--r--. 1 root root 4.8K Feb 24 14:26 rsyslog-plugin-v2.py

```

9. Configure logrotate for syslog files and script logs

**For rsyslog**

Point the path to the location of your rsyslog logging root directory, this will rotate the logs daily and compress and keep them for 7 days

```bash
# vi /etc/logrotate.d/rsyslog
```

```
/opt/rsyslog/**/*.log {
        daily
        missingok
        rotate 7
        compress
}
```

**For NetBrain Script**

Point the path to the location of your NetBrain script logging root directory, this will rotate the logs daily and compress and keep them for 7 days

```bash
# vi /etc/logrotate.d/nb-script
```

```
/opt/nb-script/logs/*.log {
        daily
        missingok
        rotate 7
        compress
}
```

## Testing

This automation can be tested by either intiating a configuration change on a device or sending the python script a text file with device management IPs in it on new lines:

> Making a test file

```bash
# vi /opt/nb-script/test.txt
```

```
10.0.100.1
10.0.100.2
172.16.100.10
```

> Executing the Test file

```bash
# /usr/bin/python3 /opt/nb-script/rsyslog-plugin-v2.py < test.txt
```

This will pass the list of IP addresses to the script, there will be no console output but you should see tasks being created in the NetBrain Task Manager. Once it's completed you will be returned to the bash console.

## Authors

* **Kazi Faisal** - *Initial work*
* **Terry Fera** - *Initial work*
