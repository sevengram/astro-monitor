#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
import Queue
from SocketServer import ThreadingTCPServer, BaseRequestHandler

from workers import MsgDispatchThread, ProcessCheckThread

from monitor import ByeLogMonitor, PhdLogMonitor


class ClientPool(object):
    def __init__(self, queue_size=1000):
        self._msg_queue = Queue.Queue(queue_size)
        self._socks = {}

    def add_client(self, address, sock):
        self._socks[address] = sock

    def remove_client(self, address):
        del self._socks[address]

    def put_msg(self, tag, level, msg):
        self._msg_queue.put('|'.join([tag, level, msg]) + '#')

    def dispatch_msg(self):
        msg = self._msg_queue.get()
        for sock in self._socks.itervalues():
            try:
                sock.sendall(msg)
            except IOError:
                continue


client_pool = ClientPool()


class ConnectionRequestHandler(BaseRequestHandler):
    def setup(self):
        addr_port = '%s:%s' % self.client_address
        logging.info('server|connected %s' % addr_port)
        client_pool.add_client(addr_port, self.request)

    def handle(self):
        addr_port = '%s:%s' % self.client_address
        while True:
            try:
                data = self.request.recv(1024).strip()
                logging.debug('server|msg from %s %s', addr_port, data)
                if data:
                    self.request.sendall('ack|debug|%s#' % data)
                else:
                    raise IOError
            except IOError:
                logging.warning('server|broken from %s', addr_port)
                break

    def finish(self):
        addr_port = '%s:%s' % self.client_address
        client_pool.remove_client(addr_port)
        logging.info('server|disconnected %s' % addr_port)


level_map = {
    'info': logging.INFO,
    'debug': logging.DEBUG,
    'warn': logging.WARN,
    'warning': logging.WARNING,
    'error': logging.ERROR
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bye', type=str, required=True, help='Log path of BackyardEOS')
    parser.add_argument('--phd', type=str, required=True, help='Log path of PHDGuiding2')
    parser.add_argument('--level', type=str, default='info', help='Log level')
    parser.add_argument('--port', type=int, default=4600)
    args = parser.parse_args()

    logging.basicConfig(level=level_map.get(args.level),
                        format='%(asctime)s %(levelname)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    worker_threads = {}
    byelog = ByeLogMonitor(args.bye, client_pool, worker_threads)
    phdlog = PhdLogMonitor(args.phd, client_pool, worker_threads)
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
    server = ThreadingTCPServer(('', args.port), ConnectionRequestHandler)
    server.serve_forever()
