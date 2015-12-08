# -*- coding: utf-8 -*-

import logging
import os
import threading

import workers


class BaseLogMonitor(object):
    def __init__(self, path, clients, threads, timeout):
        self.label = 'log'
        self.path = path
        self.timeout = timeout
        self.clients = clients
        self.threads = threads
        self._file = self._recent_log()
        self._event = threading.Event()

    def _recent_log(self):
        return self.path + '/' + [f for f in os.listdir(self.path) if f.endswith('txt')][-1]

    def _check(self, text):
        self.clients.put_msg(self.label, 'info', text)
        logging.debug('%s|%s', self.label, text)

    def _search_log(self):
        new_logfile = self._recent_log()
        if new_logfile != self._file:
            logging.info('%s|new logfile: %s' % (self.label, new_logfile))
            self._file = new_logfile
            if self.label in self.threads:
                self.threads[self.label].terminate()
                nt = self.create_check_thread()
                nt.setDaemon(True)
                nt.start()
                self.threads[self.label] = nt
        else:
            msg = 'stop working!'
            self.clients.put_msg(self.label, 'error', msg)
            logging.error('%s|%s', self.label, msg)

    def create_check_thread(self):
        return workers.LogCheckThread(self._file, self._event, self._check)

    def create_daemon_thread(self):
        return workers.LogDaemonThread(self._event, self._search_log, self.timeout)


class ByeLogMonitor(BaseLogMonitor):
    def __init__(self, path, clients, threads, timeout=300):
        super(ByeLogMonitor, self).__init__(path, clients, threads, timeout)
        self.label = 'bye'

    def _recent_log(self):
        return self.path + '/' + [fn for fn in os.listdir(self.path)[-2:] if fn.find('backgroundworker') == -1][-1]

    def _check(self, text):
        text = ' '.join(text.split()[5:])
        if text.lower().find('disconnected') != -1 or text.find('shutdown') != -1:
            self.clients.put_msg(self.label, 'error', text)
            logging.error('%s|%s', self.label, text)
        else:
            self.clients.put_msg(self.label, 'info', text)
            logging.debug('%s|%s', self.label, text)


class PhdLogMonitor(BaseLogMonitor):
    def __init__(self, path, clients, threads, timeout=6):
        super(PhdLogMonitor, self).__init__(path, clients, threads, timeout)
        self.label = 'phd'

    def _check(self, text):
        if text.lower().find('drop') != -1:
            self.clients.put_msg(self.label, 'error', text)
            logging.error('%s|%s', self.label, text)
        else:
            self.clients.put_msg(self.label, 'info', text)
            logging.debug('%s|%s', self.label, text)
