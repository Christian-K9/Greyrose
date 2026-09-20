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
    "fedora": "https://download.splunk.com/products/universalforwarder/releases/10.0.3/linux/splunkforwarder-10.0.3-adbac1c8811c-linux-amd64.rpm",
    "rocky": "https://download.splunk.com/products/universalforwarder/releases/10.0.3/linux/splunkforwarder-10.0.3-adbac1c8811c-linux-amd64.rpm",
    "oracle": "https://download.splunk.com/products/universalforwarder/releases/10.0.3/linux/splunkforwarder-10.0.3-adbac1c8811c-linux-amd64.rpm"
    }

new_owner = "root:root"
username = ""
password = ""
server = ""
log_name = ""

def prologue():
    global username
    global password
    global server
    global log_name
    #types of servers running
    machines = ["debian", "ubuntu", "centos", "fedora", "rocky"]
    print("Server Types:")
    print(f"        {machines}")

    server = ""
    #machine is based on user input
    while server not in machines:
        server = input("What Server Are You Running? ")
        if server.lower() not in machines:
            print("Not Valid Operating System Name")

    username = input("Enter Centralized Username (Can be sysadmin): ")
    password = getpass.getpass("Enter Centralized Password: ")

    #get name of operating system via hostnamectl
    result = subprocess.run(["hostnamectl"], capture_output=True, text=True)
    pattern = r"Operating System: (.+)"
    match = re.search(pattern, result.stdout)
    if match:
        log_name = match.group(1).split()[0]
    else:
        print("Opearting system field not found in hostnamectl")
        log_name = "linux"

    #Centralized logging in linux .log file
    logging.basicConfig(level=logging.DEBUG, filename=f"{log_name}.log", 
            filemode="w", format="%(asctime)s - %(levelname)s - %(message)s")


def exposition():
    #installing necessary libraries
    #putting a 0.1 second gap between each one so processes don't conflict
    package_managers = {"debian": "apt-get", "ubuntu": "apt-get", "centos": "apt-get",
               "fedora": "yum", "rocky": "yum"}
    manager = package_managers[server]
    print(f"manager: {manager}")
    time.sleep(5)
    time.sleep(0.1)
    libraries = ["python3-dev", "python3-pip", "mariadb-server"]
    if server == "ubuntu":
        libraries.append("libmariadb-dev")
        libraries.append("build-essential")
        libraries.append("mariadb-client")
        libraries.append("python3-venv")
    else:
        libraries.append("mariadb-connector-c-devel")
        libraries.append("'Development Tools'")
        libraries.append("python3-devel")
        libraries.append("mariadb")
        libraries.append("gcc")
        libraries.append("gcc-c++")
        libraries.append("make")
    print("synchronizing time")
    subprocess.run(["sudo", "timedatectl", "set-ntp", "true"])
    print("updating")
    subprocess.run(["sudo", manager, "update"])
    if server == "ubuntu":
        subprocess.run(["sudo", manager, "--fix-missing-install"])
    else:
        subprocess.run(["sudo", "yum", "distro-sync"])

    for i in libraries:         
            try:
                subprocess.run(["sudo", manager, "install", i, "-y"], check=True,)
                time.sleep(0.1)

                print("Installation Sucessful!")
                logging.debug(f"Installed Library: {i}")

        #in case things go wrong (WHICH THEY SHOULDN'T)
            except subprocess.CalledProcessError as e:
                print(f"Installation failed with exit code: {e.returncode}")
                print("--- Error Details ---")
                logging.warning(f"Failed to install Library {i}")
                try_again(i, manager)

            

#apparently nothing wants to work :[
def try_again(library, manager):
    print("trying to install library again")
    subprocess.run(["sudo", manager, "update"])
    if server == "ubuntu":
        subprocess.run(["sudo", manager, "--fix-missing-install"])
    else:
        subprocess.run(["sudo", "yum", "distro-sync"])
    try:
        subprocess.run(["sudo", manager, "install", library, "-y"])
        print("Installation Successful")
        logging.info(f"reattempt to install {library} successful")

    #If things go wrong twice run the 3 subprocesses above via CLI
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to install Library{library} TWICE")
        print(f"Error: Installation Failed twice with exit code: {e.returncode}")
        sys.exit()

def act_I():
    #create python environment to prevent any dependency issues
    #side note: this is optional. not all linux machines have undependable python libraries
    venv_dir = "ccdc_venv"
    print("creating python environment")
    time.sleep(5)
    subprocess.run(["sudo", "python3", "-m", "venv", venv_dir])
    pip_dir = f"{venv_dir}/bin/pip"
    subprocess.run(["sudo", "mkdir", "-p", "wheels"])

    logging.debug(f"python environment: {venv_dir} created")

    #installing python dependencies
    print("installing python dependencies")
    executable = "ccdc_venv/bin/python3"
    time.sleep(0.1)
    subprocess.run([executable, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.run([executable, "-m", "pip", "install", "--upgrade", "pip",
                    "setuptools", "wheel"])
    subprocess.run([executable, "-m", "pip", "download",
        "mariadb[binary]", "setuptools", "wheel", "-d", "wheels"])
    time.sleep(0.1)
    subprocess.run([executable, "-m", "pip", "install", "--no-index",
        "--find-links=wheels", "setuptools wheel"])
    time.sleep(0.1)
    subprocess.run([executable, "-m", "pip", "install", "--no-index",
        "--find-links=wheels", "mariadb[binary]"])
    time.sleep(0.1)

    subprocess.run(["sudo", "chown", "-R", new_owner, "wheels"])
    subprocess.run(["sudo", "chown", "-R", new_owner, venv_dir])

    logging.debug(f"python depenencies installed")


def act_II():
    #activate mariadb
    subprocess.run(["sudo", "systemctl", "enable", "mariadb"])
    subprocess.run(["sudo", "systemctl", "start", "mariadb"])
    location = os.path.join(os.getcwd(), "ccdc_venv", "bin", "python3")

    logging.debug("Mariadb service started")

    log_location = os.path.join(os.getcwd(), log_name)
                            
    lines = [
        f"databasename=Greyrose_DB\n",
        f"log_name={log_location}\n",
        f"username={username}\n",
        f"password={password}\n"
    ]

    #add last few lines to file
    with open("db.conf", "a") as file:
        file.writelines(lines)


    filename = "connectors.sql"
    replacements = {"--greyrose_user": f"CREATE USER IF NOT EXISTS '{username}'@'localhost' IDENTIFIED BY '{password}';",
               "--granted_privileges": f"GRANT ALL PRIVILEGES ON Greyrose_DB.* TO '{username}'@'localhost';"}
    
    #read the file
    with open(filename, "r") as f:
        content = f.read()

    updated_content = content

    for marker, replacement in replacements.items():
        if marker not in updated_content:
            print(f"Warning: {marker} not found")
        updated_content = updated_content.replace(marker, replacement)

    #update everything
    with open(filename, "w") as f:
        f.write(updated_content)

    shebang = f"#!{location}"
    print(f"shebang: {shebang}")
    subprocess.run(["sudo", "sed", "-i", f"1i {shebang}", "firewall"])
    subprocess.run(["sudo", "sed", "-i", f"1i {shebang}", "tracker.py"])
    subprocess.run(["sudo", "cp", "firewall", "/usr/local/bin/firewall"])
    subprocess.run(["sudo", "chmod", "700", "/usr/local/bin/firewall"])

    services = {"rocky": ["110", "25", "80", "443", "22", "9997"],
                "fedora": ["53", "9997"],
                "ubuntu": ["443", "22", "9997"],
                "oracle": ["8000", "8089", "9997"]}

    for port_number in services[server]:
        string_arg_I = f'/# END: ACCEPTED PORT CONNECTION/i \\\ttcp sport {port_number} accept'
        string_arg_II = f'/# END: ACCEPTED PORT CONNECTION/i \\\ttcp dport {port_number} accept'
        string_arg_III = f'/--default_ports/i INSERT INTO accepted_ports (port) VALUES ({port_number});'
        subprocess.run(["sudo", "sed", "-i",
            string_arg_I, "nftables.conf"])
        subprocess.run(["sudo", "sed", "-i",
            string_arg_II, "nftables.conf"])
        subprocess.run(["sudo", "sed", "-i",
                string_arg_III, "connectors.sql"])

    #initiate greyrose database
    print("RUNNING SQL SCRIPT...")
    with open("connectors.sql", "r") as sql_file:
        result = subprocess.run(
            ["sudo", "mariadb", "-u", "root"],
            stdin=sql_file,
            capture_output=True,
            text=True
        )

    logging.debug("Mariadb .sql database initiated")

def act_III():
    #create service
    venv_dir = "ccdc_venv"
    python_executable = f"{venv_dir}/bin/python3"
    new_location = f's|^ExecStart=.*|ExecStart={python_executable}| /usr/loca/bin/tracker.py'
    subprocess.run(["sudo", "sed", "-i", new_location, "Greyrose.service"])
    subprocess.run(["sudo", "cp", "Greyrose.service", "/etc/systemd/system/Greyrose.service"])
    subprocess.run(["sudo", "cp", "tracker.py", "/usr/local/bin/tracker.py"])
    subprocess.run(["sudo", "chmod", "700", "/usr/local/bin/tracker.py"])
    subprocess.run(["sudo", "systemctl", "daemon-reload"])
    subprocess.run(["sudo", "systemctl", "enable", "Greyrose.service"])
    subprocess.run(["sudo", "systemctl", "start", "Greyrose.service"])

    logging.debug("Greyrose Service started and enabled")


def climax():
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

def run_dpkg():
    cmd = ["sudo", "dpkg", "-i", "/opt/splunkforwarder-10.0.3-adbac1c8811c-linux-amd64.deb"]
    for i in range(5):
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("Installation successful!")
            logging.info(f"Installation attempt {i} successful")
            return True
        if "lock" in result.stderr or "locked" in result.stderr:
            print("dpkg is locked by another process. Retrying in 5s")
            time.sleep(5)
        else:
            print("dpkg returned with uknown error")
            logging.error("dpkg returned with unknown error")
    return False

def falling_action():
    #get splunk forwarder off the internet
    location = os.path.join(os.getcwd(), log_name)
    print("Fetching splunk forwarder off the internet...")
    print(f"Forwarder Name: {forwarders[server]}")
    time.sleep(0.1)
    subprocess.run(["sudo", "wget", "-O", "/opt/splunkforwarder-10.0.3-adbac1c8811c-linux-amd64.deb", forwarders[server]])
    time.sleep(0.1)
    if run_dpkg() == False:
        print("Splunk Forwarders Failed to install")
        logging.error("Python Forwarders Failed to Install")
        sys.exit()
    time.sleep(0.1)
    logging.debug("Fetched splunk forwarder off the internet")

    #start splunk forwarder
    #side note: Splunk will prompt you for an administrator username
    authentication = f"{username}:{password}"
    print("Starting Splunk...")
    subprocess.run(["sudo", "/opt/splunkforwarder/bin/splunk", "start", "--accept-license"])
    logging.debug("Started Splunk")
    splunk = input("What Is The Splunk Ip Address?: ")
    splunk_port = input("What is the Splunk Port: ")
    forward_server = f"{splunk}:{splunk_port}"
    
    #add monitors
    print("Adding Monitors...")
    splunk_dir = "/opt/splunkforwarder/bin/splunk"
    monitors = ["/var/log", "/etc/systemd/system", "/usr/lib/systemd/system", location]
    subprocess.run(["sudo", splunk_dir, "add", "forward-server", forward_server])
    for i in monitors:
        subprocess.run(["sudo", splunk_dir, "add", "monitor", "-auth", authentication, i])
    subprocess.run(["sudo", splunk_dir, "enable", "boot-start"])
    subprocess.run(["sudo", splunk_dir, "restart"])

    logging.debug("Added new monitors to splunk")


def resolution():
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
    subprocess.run(["sudo", "mv", "quarantine", "/root/quarantine"])
    subprocess.run(["sudo", "chown", "root:root", "/root/quarantine"])
    subprocess.run(["sudo", "chmod", "600", "/root/quarantine"])
    subprocess.run(["sudo", "cp", "db.conf", "/usr/local/bin/db.conf"])

def epilogue():
    print("Final Check....")

    subprocess.run(["sudo", "systemctl", "daemon-reload"])
    subprocess.run(["sudo", "systemctl", "restart", "Greyrose.service"])
    
    #check for correct permissions
    print("Applying correct permissions")
    locations = {"connectors.sql": "script", "firewall": "script", "Greyrose.service" : "non-script",
                "nftables.conf": "non-script", "setup.py": "script", "tracker.py": "script",
                 "wheels": "non-script", "ccdc_venv": "non-script", f"{log_name}.log": "non-script",
                "/usr/local/bin/db.conf": "non-script", "/usr/local/bin/firewall": "script",
                 "/usr/local/bin/tracker.py": "script", "/etc/systemd/system/Greyrose.service": "script",
                 "db.conf": "non-script", ".setup.py.swp": "non-script"}
    
    for i in locations:
        subprocess.run(["sudo", "chown",  "-R", new_owner, i])
        if locations[i] == "script":
            permissions = "700"
        else:
            permissions = "600"
        subprocess.run(["sudo", "chmod", permissions, i])

    #check for mariadb service started
    print("Checking if mariadb service is active")
    result = subprocess.run(["sudo", "systemctl", "is-active", "mariadb.service"], capture_output=True, text=True)
    if result == "inactive":
        print("ERROR: mariadb.service is inactive")
        logging.warning("mariadb service is inactive")
    else:
        print("mariadb service: active")

    #check if nftables service started
    print("Checking if nftables service is active")
    result = subprocess.run(["sudo", "systemctl", "is-active", "nftables.service"], capture_output=True, text=True)
    if result == "inactive":
        print("ERROR: nftables.service is inactive")
        logging.warning("nftables service is inactive")
    else:
        print("nftables service: active")

    #check for greyrose service started
    print("Checking if greyrose service is active")
    result = subprocess.run(["sudo", "systemctl", "is-active", "Greyrose.service"], capture_output=True, text=True)
    if result == "inactive" or result == "failed":
        print("ERROR: Greyrose.service is inactive")
        logging.warning("Greyrose service is inactive")
    else:
        print("active")

    #check if splunk exist
    print("Checking if splunk forwarder is addded")
    splunk_path = Path("/opt/splunkforwarder/bin/splunk")
    if splunk_path.is_file():
        print("Splunk Pathway exists")
        logging.warning("Splunk Pathway exist")
    else:
        print("Splunk Pathway does not exist")
        logging.warning("Splunk Pathway does not exist")
    #check if my sanity still exist


def run():
    prologue()
    #install packages
    exposition()
    #create python environment
    act_I()
    #create database
    act_II()
    #create greyrose service
    act_III()
    #enforce firewall
    climax()
    #add splunk forwarders
    falling_action()
    #move directories
    resolution()
    #apply final permissions
    epilogue()

if len(sys.argv) > 1:
    argument = sys.argv[1]
    prologue()
    if (argument == "-i") or (argument == "--install"):
        exposition()
    elif (argument == "-p") or (argument == "--python"):
        act_I()
    elif (argument == "-d") or (argument == "--database"):
        act_II()
    elif (argument == "-g") or (argument == "--greyrose"):
        act_III()
    elif (argument == "-e") or (argument == "--enforce"):
        climax()
    elif (argument == "-s") or (argument == "--splunk"):
        falling_action()
    elif (argument == "-m") or (argument == "--move"):
        resolution()
    elif (argument == "-f") or (argument == "--finale"):
        epilogue()
    else:
        print(f"{argument}: Not valid script argument")
else:
    run()
