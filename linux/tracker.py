

import sys
import logging
import os
import time
import subprocess
import re
import os
from xml.dom.minicompat import StringTypes
import mariadb
import signal
from pathlib import Path
from dotenv import load_dotenv

#Centralized logging in linux .log file
logging.basicConfig(level=logging.DEBUG, filename="/opt/Greyrose.log", 
        filemode="w", format="%(asctime)s - %(levelname)s - %(message)s")

#load_dotenv("/opt/db.env")

database_name = os.environ.get("DB_NAME")
username = os.environ.get("USERNAME")
password = os.environ.get("PASSWORD")
server = os.environ.get("SERVER")

if server == "rocky":
    hostname = "127.0.0.1"
else:
    hostname = "localhost"


#connect with the mariadb database
try:
    conn = mariadb.connect(
        user=username,
        password=password,
        host=hostname,
        port=3306,
        database="Greyrose_DB"
    )
except mariadb.Error as e:
    print(f"error connecting to MariaDB: {e}")
    logging.error("Problem connecting to MariaDB:")
    sys.exit(1)

cursor = conn.cursor()

#get list from firewall
#import firewall
accepted_ports = []
blocked_ports = []
allowed_users = []
blocked_users = []
whitelist = []
blacklist = []
allowed_services = []
blocked_services = []
reverseShellFlags = [r"python3?\s+-c\b", r"/bin/(ba)?sh\s+-i\b", r"nc\s+.*-e\b", r"ncat\s+.*-e\b", r"socat\s+.*EXEC\b"]

def fetch():
    global accepted_ports
    global blocked_ports
    global allowed_users
    global blocked_users
    global whitelist
    global blacklist
    global allowed_services
    global blocked_services

    #use sql to fetch whitelist, and blacklist
    cursor.execute("SELECT port FROM accepted_ports")
    accepted_ports = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT port FROM blocked_ports")
    blocked_ports = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT name FROM allowed_services")
    allowed_services = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT name FROM blocked_services")
    blocked_services = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT name FROM allowed_users")
    allowed_users = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT name FROM blocked_users")
    blocked_users = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT ip FROM whitelist")
    whitelist = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT ip FROM blacklist")
    blacklist = [row[0] for row in cursor.fetchall()]

'''
User Error: #UE{index}#
Process Error: #PE{index}#
IP Error: #IPE{index}#
Crontab Error: #CTE{index}#
Service Error: #SE{index}#
'''

index = 0

#Rules for users
#   1. no suspicious user names
#   2. no user id or group id that is 0
#   3. no user id that is over 1000
def checkUsers():
    f = open("/etc/passwd", "r")
    users = f.readlines()
    f.close()
    for user in users:
        userSplit = user.split(":")
        username = userSplit[0]
        user_id = userSplit[2]
        group_id = userSplit[3]
        if (username not in allowed_users):
            if (username in blocked_users) or ((user_id == '0') or (group_id == '0')):
                os.system("userdel " + username)
                logging.error(f"#UE{index} < User {username} found on machine with unusual id >")
                index +=1
                logging.info(f"#UI{index} < User {username} removed from machine >")
                index +=1
            elif (int(user_id) >= 1000):
                os.system("userdel " + userSplit[0])
            logging.error(f"#UE{index} < User {username} found on machine with unusual id >")
            index +=1
            logging.info(f"#UI{index} < User {username} removed from machine >")
            index +=1

# Checks Processes that are flagged for being a potentially reverse shell
def checkProcesses():
    processes = getOutputOf("ps aux")
    processesSplit = processes.split("\n")
    for process in processesSplit:
        for flag in reverseShellFlags:
            if re.search(flag, process):
                processConts = process.split()
                pid = processConts[1]
                os.kill(int(pid), signal.SIGKILL)
                logging.error(f"#PE{index} < Process with PID {pid} found on machine >")
                index +=1
                logging.info(f"#PI{index} < Process with PID {pid} killed on machine >")
                index += 1

# Checks For ips that are not allowed by root
def checkIPs():
    connections = getOutputOf("who")
    connectionsSplit = connections.split("\n")
    for connection in connectionsSplit:
        connection = connection.split()
        if len(connection) >= 5:
            ipSplit = connection[4].split('.')
            if (len(ipSplit) == 4) and (connection[4] not in whitelist):
                user = connection[0]
                seat = connection[1]
                os.system("pkill -KILL -t " + seat)
                date = connection[2]
                time = connection[3]
                remoteIP = connection[4]
                logging.error(f"#IPE{index} < ip address {ipSplit} was found and flagged >")
                index +=1

# Checks for any additions to the crontab
def checkCrontab():
    crontab = Path("/etc/crontab")
    if crontab.is_file():
        f = open("/etc/crontab", "r")
        contents = f.read()
        f.close()
        if len(contents) > 0:
            if (contents != "\n"):
                f = open("/etc/crontab", "w")
                f.write("\n")
                f.close()
                logging.error(f"#CTE{index} < contents of /etc/crontab were not empty >")
                index +=1
                logging.info(f"CTI{index} < contents of /etc/crontab removed >")
                index +=1

# Checks for Services that are not allowed
def checkServices():
    services = getOutputOf("systemctl list-units --type=service --state=running")
    servicesSplit = services.split("\n")
    for service in servicesSplit:
        for blacklistedService in blocked_services:
            if blacklistedService in service:
                serviceName = service.split()[0]
                os.system("systemctl stop " + serviceName)
                os.system("systemctl disable " + serviceName)
                os.system("mv /etc/systemd/system/" + serviceName + " /root/quarantine/")
                os.system("systemctl daemon-reload")
                logging.error(f"#SE{index} < service {serviceName} found and flagged >")
                index +=1
                logging.info(f"#SI{index} < service {serviceName} disabled and moved to /root/quarantine >")
                index +=1

def getOutputOf(command):
    #Check if the command is a string. If it is, It goes through the shell
    shell = isinstance(command, StringTypes)

    #Start running the command in the background to set up
    # Pipes are used to capture the normal output (stdout) and possible error messages (stderr).
    try:
        proc = subprocess.Popen(
            command,
            shell=shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True  # text mode; works on Py2/3
        )
        out, err = proc.communicate()

        # Check if command failed or not
        if proc.returncode != 0:
            return (err or "").strip()
        return (out or "").strip()

    # Catch Exceptional Errors
    except OSError as e:
        # e.g., command not found
        return str(e).strip()

def run():
    while True:
        fetch()
        checkUsers()
        checkIPs()
        checkProcesses()
        checkServices()
        checkCrontab()
        time.sleep(30)

run()
