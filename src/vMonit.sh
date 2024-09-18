#!/bin/bash

py=python3
File=~/virt/$py/bin/activate
echo $File
source $File

#$py -V
while true; do
    $py -B vMonit.py
    sleep 5
done
