#!/bin/bash

db_path=/home/pokeybill/virtz/virtz/data/game_data.db
py=/home/pokeybill/virtz/venv/bin/python
printf "DB_PATH: %s\nPYTHON_BIN: %s\n" "$db_path" "$py"
echo 'Press any key to continue'
read -n1 _
rm -v "$db_path"
$py models.py "$db_path"
$py tiles.py "$db_path"
