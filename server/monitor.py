# -*- coding: utf-8 -*-

import logging
import os
import threading

import workers


class BaseLogMonitor(object):
    def __init__(self, path, clients, threads):
        self.label = 'log'
        self.path = path
        self.clients = clients
        self.threads = threads
        self._file = self._recent_log()
        self._event = threading.Event()

    def _recent_log(self):
        return self.path + '/' + os.listdir(self.path)[-1]

    def _check(self, text):
        self.clients.put_msg(self.label, 'info', text)
        logging.info('%s|%s' % (self.label, text))

    def _filter(self, logline):
        return True

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
            logging.error('%s|%s' % (self.label, msg))

    def create_check_thread(self):
        return workers.LogCheckThread(self._file, self._event, self._check, self._filter)

    def create_daemon_thread(self):
        return workers.LogDaemonThread(self._event, self._search_log)


class ByeLogMonitor(BaseLogMonitor):
    def __init__(self, path, clients, threads):
        super(ByeLogMonitor, self).__init__(path, clients, threads)
        self.label = 'bye'

    def _filter(self, logline):
        parts = logline.split()
        if len(parts) < 6:
            return False
        typ = parts[2].strip('[]')
        text = ' '.join(parts[5:])
        return text.startswith('Pausing') or (
            typ == 'CameraTakePictureOnMessageRecieved' and text.startswith('TAKE')) or (
                   typ == 'TakePictureBulbFramework' and text.startswith('BackgroundThreadProcessor')) or (
                   typ == 'OnStateEventHandler' and text.startswith(
                       'Items')) or typ == 'CameraImageDownloadProcessor' or (
                   typ.startswith('IMG') and text.endswith('downloaded')) or text.startswith('Imaging')

    def _check(self, text):
        text = ' '.join(text.split()[5:])
        self.clients.put_msg(self.label, 'info', text)
        logging.info('%s|%s' % (self.label, text))


class PhdLogMonitor(BaseLogMonitor):
    def __init__(self, path, clients, threads):
        super(PhdLogMonitor, self).__init__(path, clients, threads)
        self.label = 'phd'

    def _filter(self, logline):
        frame = logline.split(',')[0]
        return frame.isdigit() and int(frame) % 5 == 0
