# -*- coding: utf-8 -*-

import logging
import platform
import threading
import time
from subprocess import Popen, PIPE

import terminable_thread


def open_log_process(logfile):
    return Popen(['tail', '-f', logfile], bufsize=1024, stdin=PIPE, stdout=PIPE, close_fds=True)


class LogDaemonThread(threading.Thread):
    def __init__(self, event, handler, timeout):
        threading.Thread.__init__(self)
        self._event = event
        self.handler = handler
        self.timeout = timeout

    def run(self):
        last_update = time.time()
        while True:
            time.sleep(5)
            if self._event.isSet():
                last_update = time.time()
                self._event.clear()
            else:
                if time.time() - last_update > self.timeout:
                    self.handler()
                    last_update = time.time()


class LogCheckThread(terminable_thread.TerminableThread):
    def __init__(self, logfile, event, handler):
        threading.Thread.__init__(self)
        self.handler = handler
        self._event = event
        self._process = open_log_process(logfile)

    def run(self):
        fout = self._process.stdout
        while True:
            text = fout.readline().rstrip(' \t\r\n')
            if text:
                self._event.set()
                self.handler(text)

    def terminate(self):
        self._process.terminate()
        terminable_thread.TerminableThread.terminate(self)


class ProcessCheckThread(terminable_thread.TerminableThread):
    def __init__(self, clients, flags):
        threading.Thread.__init__(self)
        self.clients = clients
        proc_names = {
            'eqmod': 'eqmod.exe',
            'phd': 'phd2.exe',
            'bye': 'BinaryRivers.BackyardEOS.Start.Camera1.exe'
        }
        self.essentials = set(proc_names[f] for f in flags)

    def run(self):
        flag = '-W' if platform.system().lower().startswith('cygwin') else '-ef'
        while True:
            process = Popen(["ps %s | grep 'eqmod\|phd\|BackyardEOS'" % flag], shell=True, bufsize=1024, stdin=PIPE,
                            stdout=PIPE, close_fds=True)
            fout = process.stdout
            lines = fout.readlines()
            self.handle(lines)
            time.sleep(5)

    def handle(self, lines):
        running = set([l.split('\\')[-1].strip(' \t\r\n') for l in lines])
        if self.essentials.issubset(running):
            msg = 'All running: ' + ','.join(running)
            self.clients.put_msg('proc', 'debug', msg)
            logging.debug('proc|%s', msg)
        else:
            missing = self.essentials - running
            msg = 'Process missing:' + ','.join(missing)
            self.clients.put_msg('proc', 'error', msg)
            logging.error('proc|%s', msg)


class MsgDispatchThread(threading.Thread):
    def __init__(self, clients):
        threading.Thread.__init__(self)
        self.clients = clients

    def run(self):
        while True:
            self.clients.dispatch_msg()
