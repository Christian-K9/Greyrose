import subprocess

#list of ports and ips
accepted_ports = [80, 443, 9997]
blocked_ports = [22]
blocked_users = []
whitelist = []
blacklist = []

#function to reload table after configuration file change
def reload():
    subprocess.run(["sudo", "nft", "-f", "nftables.conf"])

#function to add port
def add_port(port_number):
    if port_number in accepted_ports:
        print("port already accepted")
        return
    if port_number in blocked_ports:
        blocked_ports.remove(port_number)
    string_arg = f'/# END: ACCEPTED INSIDE PORT CONNECTION/i \\\ttcp dport {port_number} accept'
    subprocess.run(["sudo", "sed", "-i",
        string_arg, "nftables.conf"])
    accepted_ports.append(port_number)

#function to remove port
def remove_port(port_number):
    if port_number in blocked_ports:
        print("port already blocked")
        return
    if port_number in accepted_ports:
        accepted_ports.remove(port_number)
    string_arg = f'/# END: DENIED INSIDE PORT CONNECTIONS/i \\\ttcp dport {port_number} accept'
    subprocess.run(["sudo", "sed", "-i",
        string_arg, "nftables.conf"])
    blocked_ports.append(port_number)

#function to add ip address
def add_ip(ip_address):
    if ip_address in whitelist:
        print("ip address is already accepted")
        return
    if ip_address in blacklist:
        blacklist.remove(ip_address)
    string_arg = f'/# END: ACCEPTED INSIDE IP CONNECTIONS/i \\\ttcp dport {ip_address} accept'
    subprocess.run(["sudo", "sed", "-i",
        string_arg, "nftables.conf"])
    whitelist.append(ip_address)

#function to add remove ip_address
def remove_ip(ip_address):
    if ip_address in blacklist:
        print("ip address is already blocked")
        return
    if ip_address in whitelist:
        whitelist.remove(ip_address)
    string_arg = f'/# END: ACCEPTED INSIDE IP CONNECTIONS/i \\\ttcp dport {ip_address} accept'
    subprocess.run(["sudo", "sed", "-i",
        string_arg, "nftables.conf"])
    blacklist.append(ip_address)


#function to remove users
def remove_user(user):
    if user in blocked_users
        print("user is already blocked")
        return
    blocked_users.append(user)

#interactive interface for administrator
def interface():
    while True:
        print(f"accepted_ports: {accepted_ports}")
        print(f"blocked_ports: {blocked_ports}")
        print(f"blocked_users: {blocked_users}")
        print(f"whitelist: {whitelist}")
        print(f"blacklist: {blacklist} ")

        changes = {1: add_port, 2: remove_port,
                    3: add_ip,  4: remove_ip,
                    5: remove_user}

        print(changes)

        change = input("Choose Method: ")
        changes[i]()