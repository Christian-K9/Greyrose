#!/bin/bash

sudo yum install -y nftables
sudo systemctl enable nftables.service
sudo systemctl start nftables.service

sudo nft -f nftables.conf