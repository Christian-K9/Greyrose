#!/bin/bash

sudo yum install -y nftables
sudo systemctl enable nftables.service
sudo systemctl start nftables.service

sudo nft add table ip filter
sudo nft 'add chain ip filter input { type filter hook input priority 0; policy drop; }'

# 2. Create the IPv4 sets
sudo nft 'add set ip filter whitelist { type ipv4_addr; }'
sudo nft 'add set ip filter blacklist { type ipv4_addr; }'

# 3. Insert the blacklist and whitelist rules at the top
sudo nft insert rule ip filter input ip saddr @blacklist drop
sudo nft insert rule ip filter input ip saddr @whitelist accept

sudo nft add rule ip filter input tcp dport { 22, 80, 443 } accept
sudo nft add rule ip filter input iifname "lo" accept
sudo nft add rule ip filter input ct state established,related accept
