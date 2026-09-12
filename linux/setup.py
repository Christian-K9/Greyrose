import subprocess
import logging
import os
import time
import sys
from pathlib import Path
import re
import getpass

#assign splunk forwarder based on machine
forwarders = {"debian": "https://download.splunk.com/products/universalforwarder/releases/10.0.3/linux/splunkforwarder-10.0.3-adbac1c8811c-linux-amd64.deb",
    "ubuntu": "https://download.splunk.com/products/universalforwarder/releases/10.0.3/linux/splunkforwarder-10.0.3-adbac1c8811c-linux-amd64.deb",
    "centos": "https://download.splunk.com/products/universalforwarder/releases/10.0.3/linux/splunkforwarder-10.0.3-adbac1c8811c-linux-amd64.deb",
    "fedora": "https://download.splunk.com/products/universalforwarder/releases/10.0.3/linux/splunkforwarder-10.0.3-adbac1c8811c-linux-amd64.rpm"
    }

#types of servers running
machines = ["debian", "ubuntu", "centos", "fedora"]
print("Server Types:")
print(f"        {machines}")

server = ""
#machine is based on user input
while server not in machines:
    server = input("What Server Are You Running? ")
    if server.lower() not in machines:
        print("Not Valid Operating System Name")

username = input("Enter Database Username (Can be sysadmin): ")
password = getpass.getpass("Enter Database Password: ")

#get name of operating system via hostnamectl
result = subprocess.run(["hostnamectl"], capture_output=True, text=True)
pattern = r"Operating System: (.+)"
match = re.search(pattern, result.stdout)
if match:
    log_name = match.group(1).strip()
    
else:
    print("Opearting system field not found in hostnamectl")
    log_name = "linux"

#Centralized logging in linux .log file
logging.basicConfig(level=logging.DEBUG, filename=f"{log_name}.log", 
        filemode="w", format="%(asctime)s - %(levelname)s - %(message)s")

new_owner = "root:root"

def act_I():
    #installing necessary libraries
    #putting a 0.1 second gap between each one so processes don't conflict
    time.sleep(0.1)
    libraries = ["libmariadb-dev", "python3-dev", "build-essential",
                 "python3-venv", "python3-pip", "mariadb-server", "mariadb-client"]
    subprocess.run(["sudo", "timedatectl", "set-ntp", "true"])
    subprocess.run(["sudo", "apt-get", "update"])
    subprocess.run(["sudo", "apt-get", "--fix-missing-install"])
    for i in libraries:
        command = ["sudo", "apt-get", "install", i, "-y"]
        try:
            result = subprocess.run(["sudo", "apt-get", "install", "-y"] + libraries, check=True,)
            time.sleep(0.1)

            print("Installation Sucessful!")
            logging.debug(f"Installed Library: {i}")

    #in case things go wrong (WHICH THEY SHOULDN'T)
        except subprocess.CalledProcessError as e:
            print(f"Installation failed with exit code: {e.returncode}")
            print("--- Error Details ---")
            logging.warning(f"Failed to install Library {i}")
            try_again(i)

            

#apparently nothing wants to work :[
def try_again(library):
    print("trying to install library again")
    subprocess.run(["sudo", "apt-get", "update"])
    subprocess.run(["sudo", "apt-get", "--fix-missing-install"])
    try:
        subprocess.run(["sudo", "apt-get", "install", library, "-y"])
        print("Installation Successful")
        logging.info(f"reattempt to install {library} successful")

    #If things go wrong twice run the 3 subprocesses above via CLI
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to install Library{library} TWICE")
        print(f"Error: Installation Failed twice with exit code: {e.returncode}")
        sys.exit()


def act_III():
    #run nftables based on loaded configuration file
    print("Running nftables...")
    subprocess.run(["sudo", "nft", 
        "-f", "nftables.conf"])
    logging.debug("Running nftables")

    #start the nftables service
    print("Starting nftables service...")
    subprocess.run(["sudo", "systemctl", "start", "nftables"])
    logging.debug("Starting nftable service")

    #enable the nftables service
    print("Enabling nftables service...")
    subprocess.run(["sudo", "systemctl", "enable", "--now", "nftables"])
    logging.debug("Enabling nftables service")

    #reloading changes based on conf table
    subprocess.run(["sudo", "nft", "-f", "nftables.conf"])

    logging.debug("nftables service started and enabled")

def act_II():
    #create python environment to prevent any dependency issues
    #side note: this is optional. not all linux machines have undependable python libraries
    venv_dir = "ccdc_venv"
    print("creating python environment")
    subprocess.run(["sudo", "python3", "-m", "venv", venv_dir])
    python_executable = f"{venv_dir}/bin/python3"
    pip_dir = f"{venv_dir}/bin/pip"
    subprocess.run(["sudo", "chown", "-R", new_owner, venv_dir])
    subprocess.run(["sudo", "mkdir", "-p", "wheels"])
    subprocess.run(["sudo", "chown", "-R", new_owner, "wheels"])

    logging.debug(f"python environment: {venv_dir} created")

    #installing python dependencies
    print("installing python dependencies")
    executable = "ccdc_venv/bin/python3"
    time.sleep(0.1)
    subprocess.run([executable, "-m", "pip", "download",
        "mariadb[binary]", "setuptools", "wheel", "-d", "wheels"])
    time.sleep(0.1)
    subprocess.run([executable, "-m", "pip", "install", "--no-index",
        "--find-links=wheels", "setuptools wheel"])
    time.sleep(0.1)
    subprocess.run([executable, "-m", "pip", "install", "--no-index",
        "--find-links=wheels", "mariadb[binary]"])
    time.sleep(0.1)

    logging.debug(f"python depenencies installed")


    #activate mariadb
    subprocess.run(["sudo", "systemctl", "enable", "mariadb"])
    subprocess.run(["sudo", "systemctl", "start", "mariadb"])
    location = os.path.join(os.getcwd(), "ccdc_venv", "bin", "python3")

    logging.debug("Mariadb service started")

    lines = [
        "databasename=Greyrose_DB",
        f"username={username}",
        f"password={password}"
    ]

    with open("db.conf", "a") as file:
        file.writelines(lines)

    create_user = f"/--END: greyrose_user username/i \\\tCREATE USER IF NOT EXISTS '{username}'@'localhost';"
    create_password = f'/--END: greyrose_user password/i \\\tIDENTIFIED BY {password};'
    grant_privileges = f"/--END: granted_privileges/i \\\tTO '{username}'@'localhost';"

    subprocess.run(["sudo", "sed", "-i",
            create_user, "db.conf"])
    subprocess.run(["sudo", "sed", "-i",
                create_password, "db.conf"])
    subprocess.run(["sudo", "sed", "-i",
                grant_privileges, "db.conf"])
    
    shebang = f"#!{location}"
    print(f"shebang: {shebang}")
    subprocess.run(["sudo", "sed", "-i", f"1i {shebang}", "firewall"])
    subprocess.run(["sudo", "cp", "firewall", "/usr/local/bin/firewall"])
    subprocess.run(["sudo", "chmod", "700", "/usr/local/bin/firewall"])

    #initiate greyrose database
    with open("connectors.sql", "r") as sql_file:
        result = subprocess.run(
            ["sudo", "mariadb", "-u", "root"],
            stdin=sql_file,
            capture_output=True,
            text=True
        )

    logging.debug("Mariadb .sql database initiated")

    #create service
    new_location = f's|^ExecStart=.*|ExecStart={python_executable}| /usr/loca/bin/tracker.py'
    subprocess.run(["sudo", "sed", "-i", new_location, "Greyrose.service"])
    subprocess.run(["sudo", "cp", "Greyrose.service", "/etc/systemd/system/Greyrose.service"])
    subprocess.run(["sudo", "cp", "tracker.py", "/usr/local/bin/tracker.py"])
    subprocess.run(["sudo", "chmod", "700", "/usr/local/bin/tracker.py"])
    subprocess.run(["sudo", "systemctl", "daemon-reload"])
    subprocess.run(["sudo", "systemctl", "enable", "Greyrose.service"])
    subprocess.run(["sudo", "systemctl", "start", "Greyrose.service"])

    logging.debug("Greyrose Service started and enabled")


def act_IV():
    #get splunk forwarder off the internet
    print("Fetching splunk forwarder off the internet...")
    print(f"Forwarder Name: {forwarders[server]}")
    subprocess.run(["sudo", "wget", "-O", "/opt/splunkforwarder-10.0.3-adbac1c8811c-linux-amd64.deb", forwarders[server]])
    subprocess.run(["sudo", "dpkg", "-i", "/opt/splunkforwarder-10.0.3-adbac1c8811c-linux-amd64.deb"])
    logging.debug("Fetched splunk forwarder off the internet")

    #start splunk forwarder
    #side note: Splunk will prompt you for an administrator username
    print("Starting Splunk...")
    subprocess.run(["sudo", "/opt/splunkforwarder/bin/splunk", "start", "--accept-license"])
    logging.debug("Started Splunk")
    splunk = input("What Is The Splunk Ip Address?: ")
    port = input("What is the Splunk Port: ")
    forward_server = f"{splunk}:{port}"
    
    #add monitors
    print("Adding Monitors...")
    subprocess.run(["/opt/splunkforwarder/bin/splunk", "add", "forward-server", "forward_server"])
    subprocess.run(["/opt/splunkforwarder/bin/splunk", "add", "monitor", "/var/log"])
    subprocess.run(["/opt/splunkforwarder/bin/splunk", "add", "monitor", "/etc/crontab"])
    subprocess.run(["/opt/splunkforwarder/bin/splunk", "add", "monitor", "/etc/passwd"])
    subprocess.run(["/opt/splunkforwarder/bin/splunk", "add", "monitor", "/etc/systemd/system"])
    subprocess.run(["/opt/splunkforwarder/bin/splunk", "add", "monitor", "/usr/lib/systemd/system"])
    subprocess.run(["/opt/splunkforwarder/bin/splunk", "enable", "boot-start"])
    logging.debug("Added new monitors to splunk")


def epilogue():
    #change the permission of every file in the directory
    print("Applying permissions...")
    subprocess.run(["sudo", "chmod", "700", "setup.py"])
    subprocess.run(["sudo", "chmod", "700", "start.py"])
    subprocess.run(["sudo", "chmod", "700", "tracker.py"])
    logging.debug("Applying permissions to files inside Greyrose Directory")

    #Add firewall to sbin
    print("Adding firewall command")
    subprocess.run(["sudo", "chown", new_owner, "/usr/local/bin/firewall"])
    subprocess.run(["sudo", "chmod", "700", "/usr/local/bin/firewall"])
    logging.debug("Firewall command set")

    #move quarentine to root directory
    subprocess.run(["mv", "quarantine", "/root/quarantine"])

def final_check():
    print("Final Check....")
    #check for correct permissions
    locations = ["connectors.sql", "firewall", "Greyrose.service", "nftables.conf",
                 "setup.py", "tracker.py", "wheels", "ccdc_venv", "ubuntu.log"]
    for i in locations:
        subprocess.run(["sudo", "chown",  "-R", new_owner, i])
        subprocess.run(["sudo", "chmod", "700", i])

    #check for mariadb service started
    result = subprocess.run(["sudo", "systemctl", "is-active", "mariadb.service"], capture_output=True, text=True)
    if result == "inactive":
        print("ERROR: mariadb.service is inactive")
        logging.warning("mariadb service is inactive")

    #check if nftables service started
    result = subprocess.run(["sudo", "systemctl", "is-active", "nftables.service"], capture_output=True, text=True)
    if result == "inactive":
        print("ERROR: nftables.service is inactive")
        logging.warning("nftables service is inactive")

    #check for greyrose service started
    result = subprocess.run(["sudo", "systemctl", "is-active", "Greyrose.service"], capture_output=True, text=True)
    if result == "inactive":
        print("ERROR: Greyrose.service is inactive")
        logging.warning("Greyrose service is inactive")

    #check if splunk exist
    print("Checking if splunk forwarder is addded")
    splunk_path = ("/opt/splunkforwarder/bin/splunk")
    if splunk_path.is_file():
        print("Splunk Pathway exists")
        logging.warning("Splunk Pathway exist")
    else:
        print("Splunk Pathway does not exist")
        logging.warning("Splunk Pathway does not exist")
    #check if my sanity still exist


act_I()
act_II()
act_III()
act_IV()
epilogue()
final_check()