#!/bin/bash

sudo chown $USER:$USER ccdc_venv
executable="$PWD/ccdc_venv/bin/python3"
"$executable/bin/activate"
"$executable" -m pip install mariadb[binary]
"$executable" -m pip install setuptools wheel
"$executable" -m pip install mariadb

