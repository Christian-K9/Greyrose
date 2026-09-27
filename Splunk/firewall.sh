#!/bin/bash

sudo systemctl stop firewalld
sudo systemctl disable firewalld

sleep 1
sudo yum install -y nftables
sleep 1
sudo systemctl enable nftables.service
sudo systemctl start nftables.service

sudo nft -f nftables.conf

sleep 1
cd /opt/splunk/bin
sudo ./splunk restart
sleep 1
sudo ./splunk enable list 9997