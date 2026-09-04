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

def checkIPs():
    connections = getOutputOf("who")
    connectionsSplit = connections.split("\n")
    for connection in connectionsSplit:
        connection = connection.split()
        if len(connection) >= 5:
            ipSplit = connection[4].split('.')
            if (len(ipSplit) == 4) and (connection[4] not in allowedIPs):
                user = connection[0]
                seat = connection[1]
                os.system('echo "These are not the machines you are looking for." | write ' + user + " " + seat)
                os.system("pkill -KILL -t " + seat)
                date = connection[2]
                time = connection[3]
                remoteIP = connection[4]
                triggerAlert(datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S') + " - Unrecognized IP address '" + remoteIP + "' connected to the system as user '" + user + "' on " + date + " at " + time)

def checkCrontab():
    f = open("/etc/crontab", "r")
    contents = f.read()
    f.close()
    if len(contents) > 0:
        if (contents != "\n"):
            triggerAlert(datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S') + " - Contents found in /etc/crontab:" + contents)
            f = open("/etc/crontab", "w")
            f.write("\n")
            f.close()

def checkServices():
    services = getOutputOf("systemctl list-units --type=service --state=running")
    servicesSplit = services.split("\n")
    for service in servicesSplit:
        for blacklistedService in blacklistedServices:
            if blacklistedService in service:
                triggerAlert(datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S') + " - Blacklisted service found and stopped: " + service)
                serviceName = service.split()[0]
                os.system("systemctl stop " + serviceName)
                os.system("systemctl disable " + serviceName)
                os.system("mv /etc/systemd/system/" + serviceName + " /root/quarantined_services/")
                os.system("systemctl daemon-reload")

def getOutputOf(command):
    """
    Run a command and return stdout (or stderr if the command fails).
    Accepts either a shell string or a list argv.
    """
    # shell=True if a single shell string; False if a list/tuple argv
    shell = isinstance(command, StringTypes)

    try:
        proc = subprocess.Popen(
            command,
            shell=shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True  # text mode; works on Py2/3
        )
        out, err = proc.communicate()

        if proc.returncode != 0:
            return (err or "").strip()
        return (out or "").strip()

    except OSError as e:
        # e.g., command not found
        return str(e).strip()