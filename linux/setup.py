import subprocess
import logging

#types of servers running
machines = {0: "Debian", 1: "Ubuntu", 2: "centOS"
            3: "Fedora"}
print("Server Types:")
print(machines)

#machine is based on user input
server = input("What Server Are You Running? (Enter Number): ")

#assign splunk forwarder based on machine
forwarders = {debian: "https://download.splunk.com/products/universalforwarder/#releases/10.0.1/linux/splunkforwarder-10.0.1-c486717c322b-linux-amd64.deb",
            ubuntu: "https://download.splunk.com/products/universalforwarder/#releases/10.0.1/linux/splunkforwarder-10.0.1-c486717c322b-linux-amd64.deb",
            centos: "https://download.splunk.com/products/universalforwarder/#releases/10.0.1/linux/splunkforwarder-10.0.1-c486717c322b-linux-amd64.deb",
            fedora: "https://download.splunk.com/products/universalforwarder/releases/#10.0.1/linux/splunkforwarder-10.0.1-c486717c322b.x86_64.rpm"
}

log_name = subprocess.run(["sudo", "grep", "-Po", "'^NAME="\K[^"]+' /etc/os-release"])
#Centralized logging in ubuntu.log file
basicConfic(level=logging.DEBUG, filename=log_name, 
    filemode="w", format="%(asctime)s - %(levelname)s - %(message)s")

#run nftables based on loaded configuration file
print("Running nftables...")
subprocess.run(["sudo", "nft", 
    "-f", "nftables.conf"])
logging.debug("Running nftables")

#change the permission of every file in the directory
print("Applying permissions...")
subprocess.run(["sudo", "chmod", "700", "setup.py"])
subprocess.run(["sudo", "chmod", "700", "start.py"])
subprocess.run(["sudo", "chmod", "700", "tracker.py"])
logging.debug("Applying permissions to files inside Greyrose Directory")

#start the nftables service
print("Starting nftables service...")
subprocess.run(["sudo", "systemctl", "start", "nftables"])
logging.debug("Starting nftable service")

#enable the nftables service
print("Enabling nftables service...")
subprocess.run(["sudo", "systemctl", "enable", "--now", "nftables"])
logging.debug("Enabling nftables service")

#reloading changes based on conf table
subprocess.run(["sudo", "nft", "nftables.conf"])

#create service
subprocess.run(["cp", "Greyrose.service", "etc/systemd/system/Greyrose.service"])
subprocess.run(["sudo", "systemctl", "daemon-reload"])
subprocess.run(["sudo", "systemctl", "start", "Greyrose.service"])
subprocess.run(["sudo", "systemctl ", "enable", "Greyrose.service"])

#get splunk forwarder off the internet
print("Feting splunk forwarder off the internet...")
subprocess.run(["wget", "-splunkforwarder.tgz", "forwarders[server]"])
subprocess.run(["tar", "-xvzf", "splunkforwarder.tgz", "-C", "/opt/"])
logging.debug("Fetched splunk forwarder off the internet")

#start splunk forwarder
print("Starting Splunk...")
subprocess.run(["opt/splunkforwarder/bin/splunk", "start", "--accept-license"])
logging.debug("Started Splunk")
splunk = input("What Is The Splunk Ip Address?: ")
port = input("What is the Splunk Port")
forward_server = f"{splunk}:{port}"

#add monitors
print("Adding Monitors...")
subprocess.run(["opt/splunkforwarder/bin/splunk", "add", "forward-server", "forward_server"])
subprocess.run(["opt/splunkforwarder/bin/splunk", "add", "monitor", "/var/log"])
subprocess.run(["opt/splunkforwarder/bin/splunk", "add", "monitor", "/etc/crontab"])
subprocess.run(["opt/splunkforwarder/bin/splunk", "add", "monitor", "/etc/passwd"])
subprocess.run(["opt/splunkforwarder/bin/splunk", "add", "monitor", "/etc/systemd/system"])
subprocess.run(["opt/splunkforwarder/bin/splunk", "add", "monitor", "/usr/lib/systemd/system"])
subprocess.run(["opt/splunkforwarder/bin/splunk", "enable", "boot-start"])
logging.debug("Added new monitors to splunk")

#Add firewall to sbin
print("Adding firewall command")
subprocess.run(["sudo", "cp", "firewall", "/usr/local/sbin/"])
subprocess.run(["sudo", "chown", "root:sysadmin", "/usr/local/sbin/firewall"])
subprocess.run(["sudo", "chmod", "700", "/usr/local/sbin/firewall"])
logging.debug("Firewall command set")

#move quarentine to root directory
subprocess.run(["mv", "quarantine", "/root/quarantine"])