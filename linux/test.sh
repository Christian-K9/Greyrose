#!/bin/bash

sed $'/# END: INSIDE PORT CONNECTION/i \\\ttcp dport 9999' nftables.conf

