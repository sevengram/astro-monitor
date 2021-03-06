#!/usr/bin/env python
# -*- coding:utf-8 -*-

import argparse
import logging
import socket
import time
import threading
from sound import start_warning

last_ack_time = 0


class DaemonThread(threading.Thread):
    def __init__(self, connection):
        threading.Thread.__init__(self)
        self.sock = connection

    def run(self):
        while True:
            time.sleep(1)
            tnow = time.time()
            if last_ack_time != 0 and tnow - last_ack_time > 4:
                logging.error('ack timeout!!')
                start_warning()
            self.sock.sendall('syn@%d' % tnow)


level_map = {
    'info': logging.INFO,
    'debug': logging.DEBUG,
    'warn': logging.WARN,
    'warning': logging.WARNING,
    'error': logging.ERROR
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default='localhost')
    parser.add_argument('--port', type=int, default=4600)
    parser.add_argument('--level', type=str, default='info', help='Log level')
    args = parser.parse_args()

    logging.basicConfig(level=level_map.get(args.level),
                        format='%(asctime)s %(levelname)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    addr = (args.host, args.port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(addr)
    t = DaemonThread(sock)
    t.setDaemon(True)
    t.start()
    while True:
        block = sock.recv(1024)
        if not block:
            logging.error('socket closed by peer!!')
            start_warning()
            break
        last_ack_time = time.time()
        for data in block.split('#')[:-1]:
            try:
                label, level, msg = tuple(data.split('|')[:3])
                logging.log(level_map.get(level, 0), '%s|%s', label, msg)
                if level == 'error':
                    start_warning()
            except ValueError:
                pass
    logging.info("client close")
    sock.close()
