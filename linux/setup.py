import subprocess
import logging
import os
import venv

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
    log_name = server
    print(f"Log Name: {log_name}")
    #Centralized logging in ubuntu.log file
    logging.basicConfig(level=logging.DEBUG, filename=log_name, 
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
    print("creating python environment")
    venv_dir = "ccdc_venv"
    venv.create(venv_dir, with_pip=True)
    python_executable = os.path.join(venv_dir, "bin", "python")

    #upgrading pip inside newly created python virtual environment
    subprocess.run([python_executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)

    #installing mariadb for database
    subprocess.run([python_executable, "-m", "pip", "install", "mariadb"], check=True)

    subprocess.run(["sudo", "cp", "firewall", "/usr/local/bin/firewall"])
    subprocess.run(["sudo", "chmod", "755", "/usr/local/bin/firewall"])
    #create service
    new_location = f's|^ExecStart=.*|ExecStart={python_executable}| /usr/loca/bin/tracker.py'
    subprocess.run(["sudo", "sed", new_location, "Greyrose.service"])
    subprocess.run(["sudo", "cp", "Greyrose.service", "/etc/systemd/system/Greyrose.service"])
    subprocess.run(["sudo", "cp", "tracker.py", "/usr/local/bin/tracker.py"])
    subprocess.run(["sudo", "chmod", "700", "/usr/local/bin/tracker.py"])
    subprocess.run(["sudo", "systemctl", "daemon-reload"])
    subprocess.run(["sudo", "systemctl", "start", "Greyrose.service"])
    subprocess.run(["sudo", "systemctl ", "enable", "Greyrose.service"])

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
    subprocess.run(["sudo", "cp", "firewall", "/usr/local/sbin/"])
    subprocess.run(["sudo", "chown", "root:sysadmin", "/usr/local/sbin/firewall"])
    subprocess.run(["sudo", "chmod", "700", "/usr/local/sbin/firewall"])
    logging.debug("Firewall command set")

    #move quarentine to root directory
    subprocess.run(["mv", "quarantine", "/root/quarantine"])
act_I()
act_II()
act_III()