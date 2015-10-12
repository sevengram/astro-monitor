#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time

while True:
    f = open(sys.argv[1])
    while True:
        line = f.readline()
        if not line:
            break
        print line.strip(' \r\n\t')
        sys.stdout.flush()
        time.sleep(1)
    f.close()
