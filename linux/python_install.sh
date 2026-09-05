#!/bin/bash

executable="$PWD/ccdc_venv/bin/python"
sudo "$executable" -m pip install mariadb[binary]
sudo "$executable" -m pip install setuptools wheel
sudo "$executable" -m pip install mariadb

