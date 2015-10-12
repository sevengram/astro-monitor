#!/bin/bash

./run_log.py logs/bye/1.txt > logs/bye/2.txt &
./run_log.py logs/phd/1.txt > logs/phd/2.txt &
./server/server.py --byelog=logs/bye --phdlog=logs/phd