import subprocess
import logging
import os
import time
import sys

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

def act_I():
    #installing necessary libraries
    #putting a 0.1 second gap between each one so processes don't conflict
    time.sleep(0.1)
    libraries = ["libmariadb-dev", "python3-dev", "build-essesntials",
                 "python3-venv", "python3-pip", "mariadb-server", "mariadb-client"]
    for i in libraries:
        command = ["sudo", "apt-get", "install", i, "-y"]
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            time.sleep(0.1)

            print("Installation Sucessful!")
            print(result.stdout)

        except subprocess.CalledProcessError as e:
            print(f"Installation failed with exit code: {e.returncode}")
            print("--- Error Details ---")
            print(e.stderr)
            sys.exit()
            
    log_name = server
    print(f"Log Name: {log_name}")
    #Centralized logging in ubuntu.log file
    logging.basicConfig(level=logging.DEBUG, filename=f"{log_name}.log", 
        filemode="w", format="%(asctime)s - %(levelname)s - %(message)s")

def act_II():
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

def act_III():
    #create python environment to prevent any dependency issues
    #side note: this is optional. not all linux machines have undependable python libraries
    venv_dir = "ccdc_venv"
    print("creating python environment")
    subprocess.run(["sudo", "python3", "-m", "venv", venv_dir])
    python_executable = f"{venv_dir}/bin/python3"
    pip_dir = f"{venv_dir}/bin/pip"
    subprocess.run(["sudo", "chown", "-R", "chris:chris", venv_dir])
    subprocess.run(["sudo", "mkdir", "-p", "wheels"])
    subprocess.run(["sudo", "chown", "-R", "chris:chris", "wheels"])

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


    #activate mariadb
    subprocess.run(["sudo", "systemctl", "enable", "mariadb"])
    subprocess.run(["sudo", "systemctl", "start", "mariadb"])
    location = os.path.join(os.getcwd(), "ccdc_venv", "bin", "python3")
    shebang = f"#!{location}"
    print(f"shebang: {shebang}")
    subprocess.run(["sudo", "sed", "-i", f"1i {shebang}", "firewall"])
    subprocess.run(["sudo", "cp", "firewall", "/usr/local/bin/firewall"])
    subprocess.run(["sudo", "chmod", "755", "/usr/local/bin/firewall"])

    #initiate greyrose database
    #subprocess.run(["sudo", "mysql", "-u", "root", "-ppassword", "<", "connectors.sql"])
    with open("connectors.sql", "r") as sql_file:
        result = subprocess.run(
            ["sudo", "mariadb", "-u", "root"],
            stdin=sql_file,
            capture_output=True,
            text=True
        )
    
    #create service
    new_location = f's|^ExecStart=.*|ExecStart={python_executable}| /usr/loca/bin/tracker.py'
    subprocess.run(["sudo", "sed", "-i", new_location, "Greyrose.service"])
    subprocess.run(["sudo", "cp", "Greyrose.service", "/etc/systemd/system/Greyrose.service"])
    subprocess.run(["sudo", "cp", "tracker.py", "/usr/local/bin/tracker.py"])
    subprocess.run(["sudo", "chmod", "700", "/usr/local/bin/tracker.py"])
    subprocess.run(["sudo", "systemctl", "daemon-reload"])
    subprocess.run(["sudo", "systemctl", "enable", "Greyrose.service"])
    subprocess.run(["sudo", "systemctl", "start", "Greyrose.service"])

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
    subprocess.run(["sudo", "chown", "chris:chris", "/usr/local/bin/firewall"])
    subprocess.run(["sudo", "chmod", "700", "/usr/local/bin/firewall"])
    logging.debug("Firewall command set")

    #move quarentine to root directory
    subprocess.run(["mv", "quarantine", "/root/quarantine"])

act_I()
act_III()
act_II()
