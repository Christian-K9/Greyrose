#!/bin/bash

sudo chown chris:chris ccdc_venv
echo "downloading python dependencies"
executable="$PWD/ccdc_venv/bin/python3"
sleep 5
"$executable" -m pip download "mariadb[binary]" setuptools wheel -d wheels
sleep 5
"$executable" -m pip install --no-index --find-links=wheels setuptools wheel
sleep 5
"$executable" -m pip install --no-index --find-links=wheels mariadb[binary]
sleep 5
