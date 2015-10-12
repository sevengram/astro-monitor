# -*- coding: utf-8 -*-

import ctypes
import threading


def _async_raise(tid, exctype):
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, 0)
        raise SystemError("PyThreadState_SetAsyncExc failed")


class TerminableThread(threading.Thread):
    def raise_exec(self, excobj):
        if not self.isAlive():
            return
        for tid, tobj in threading._active.items():
            if tobj is self:
                _async_raise(tid, excobj)
                return

    def terminate(self):
        self.raise_exec(SystemExit)
