#!/bin/bash
kill -9 main.py
echo $PWD/main.py
python3 $PWD/main.py &
read  -n 1 -p "Input Selection:" mainmenuinput