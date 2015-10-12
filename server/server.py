#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
import Queue
from SocketServer import ThreadingTCPServer, BaseRequestHandler

from workers import MsgDispatchThread, ProcessCheckThread

from monitor import ByeLogMonitor, PhdLogMonitor

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


class ClientPool(object):
    def __init__(self):
        self._msg_queue = Queue.Queue()
        self._socks = {}

    def add_client(self, address, sock):
        self._socks[address] = sock

    def remove_client(self, address):
        self._socks[address] = None

    def put_msg(self, tag, level, msg):
        self._msg_queue.put('|'.join([tag, level, msg]))

    def dispatch_msg(self):
        msg = self._msg_queue.get()
        for addr, sock in self._socks.iteritems():
            try:
                if sock:
                    sock.sendall(msg)
            except IOError:
                continue


client_pool = ClientPool()


class ConnectionRequestHandler(BaseRequestHandler):
    def setup(self):
        addr_port = "%s:%s" % self.client_address
        logging.info("SERVER|connected %s" % addr_port)
        client_pool.add_client(addr_port, self.request)

    def handle(self):
        while True:
            try:
                data = self.request.recv(1024).strip()
                if data:
                    self.request.sendall(data)
                else:
                    break
            except IOError:
                break

    def finish(self):
        addr_port = "%s:%s" % self.client_address
        client_pool.remove_client(addr_port)
        logging.info("SERVER|disconnected %s" % addr_port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--byelog', type=str, help="Log path of BackyardEOS")
    parser.add_argument('--phdlog', type=str, help="Log path of PHDGuiding2")
    args = parser.parse_args()

    worker_threads = {}
    byelog = ByeLogMonitor(args.byelog, client_pool, worker_threads)
    phdlog = PhdLogMonitor(args.phdlog, client_pool, worker_threads)
    worker_threads[byelog.label + 'log'] = byelog.create_check_thread()
    worker_threads[byelog.label + 'daemon'] = byelog.create_daemon_thread()
    worker_threads[phdlog.label + 'log'] = phdlog.create_check_thread()
    worker_threads[phdlog.label + 'daemon'] = phdlog.create_daemon_thread()
    worker_threads['psmonitor'] = ProcessCheckThread(client_pool)
    worker_threads['logdispatch'] = MsgDispatchThread(client_pool)
    for t in worker_threads.values():
        t.setDaemon(True)
        t.start()
    ThreadingTCPServer.allow_reuse_address = True
    server = ThreadingTCPServer(("127.0.0.1", 4600), ConnectionRequestHandler)
    server.serve_forever()
