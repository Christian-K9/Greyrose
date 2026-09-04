import sys
import logging
import os

#get list from firewall
sys.path.inset(0, '/usr/local/sbin')
import firewall
accepted_ports = firewall.accepted_ports
blocked_ports = firewall.blocked_ports
allowed_users = firewall.allwoed_users
blocked_users = firewall.blocked_users
whitelist = firewall.whitelist
blacklist = firewall.blacklist
allowed_services = firewall.allowed_services
blocked_services = firewall.blocked_services
reverseShellFlags = [r"python3?\s+-c\b", r"/bin/(ba)?sh\s+-i\b", r"nc\s+.*-e\b", r"ncat\s+.*-e\b", r"socat\s+.*EXEC\b"]

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
            elif (int(user_id) >= 1000):
                os.system("userdel " + userSplit[0])

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

# Checks for any additions to the crontab
def checkCrontab():
    f = open("/etc/crontab", "r")
    contents = f.read()
    f.close()
    if len(contents) > 0:
        if (contents != "\n"):
            f = open("/etc/crontab", "w")
            f.write("\n")
            f.close()

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
                os.system("mv /etc/systemd/system/" + serviceName + " /root/quarantined_services/")
                os.system("systemctl daemon-reload")

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