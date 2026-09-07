#!/bin/bash

sudo chown "$USER":"$USER" ccdc_venv
executable="$PWD/ccdc_venv/bin/python3"
sleep 5
"$executable" -m pip install mariadb[binary]
sleep 5
"$executable" -m pip install setuptools wheel
sleep 5
