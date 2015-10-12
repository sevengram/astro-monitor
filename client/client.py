#!/usr/bin/env python
# -*- coding:utf-8 -*-

import socket
import time
import threading

HOST = "localhost"
PORT = 4600
BUFFERSIZE = 1024
ADDR = (HOST, PORT)


class DaemonThread(threading.Thread):
    def __init__(self, connection):
        threading.Thread.__init__(self)
        self.sock = connection

    def run(self):
        while True:
            time.sleep(2)
            self.sock.sendall('hello')


if __name__ == '__main__':
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(ADDR)
    t = DaemonThread(sock)
    t.setDaemon(True)
    t.start()
    while True:
        recvdata = sock.recv(BUFFERSIZE)
        if not recvdata:
            break
        print recvdata
    print "client close"
    sock.close()
