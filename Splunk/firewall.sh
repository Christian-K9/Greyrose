#!/bin/bash

sudo nft add table inet filter
sudo nft add chain inet filter input '{ type filter hook input priority 0; policy drop; }'

sudo nft add set inet filter blacklist '{ type ipv4_addr; flags interval; }'
sudo nft add set inet filter whitelist '{ type ipv4_addr; flags interval; }'

sudo nft add element inet filter blacklist { 198.51.100.1 }
sudo nft add element inet filter whitelist { 192.0.2.1 }
sudo nft add element inet filter blacklist { 10.0.0.0/8 }
sudo nft add element inet filter blacklist { 192.168.1.10-192.168.1.50 }

sudo nft delete element inet filter blacklist { 198.51.100.1 }

sudo nft add rule inet filter input iif "lo" accept
sudo nft add rule inet filter input ip saddr @blacklist drop
sudo nft add rule inet filter input ct state established, related accept
sudo nft add rule inet filter input ip saddr @whitelist accept

sudo nft add rule inet filter input tcp dport { 8000, 8009, 9997 } accept

sudo nft list ruleset | sudo tee /etc/nftables.conf > /dev/null
sudo systemctl enable --now nftables

echo "nftables configuration updated and saved successfully!"