#!/usr/bin/env python
# -*- coding:utf-8 -*-

import argparse
import socket
import time
import threading


class DaemonThread(threading.Thread):
    def __init__(self, connection):
        threading.Thread.__init__(self)
        self.sock = connection

    def run(self):
        while True:
            time.sleep(2)
            self.sock.sendall('syn@%d' % time.time())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default='localhost')
    parser.add_argument('--port', type=int, default=4600)
    args = parser.parse_args()

    addr = (args.host, args.port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(addr)
    t = DaemonThread(sock)
    t.setDaemon(True)
    t.start()
    while True:
        recvdata = sock.recv(1024)
        if not recvdata:
            break
        print recvdata
    print "client close"
    sock.close()
