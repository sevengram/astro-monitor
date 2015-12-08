import os
import platform
import threading

is_warning = False
is_win32 = platform.system().lower().startswith('cygwin')

warning_sound = 'e:/Music/bgm/warning.mp3' if is_win32 else '/home/jfan/Music/warning.mp3'
player = '/cygdrive/c/Program\ Files\ \(x86\)/Windows\ Media\ Player/wmplayer.exe' if is_win32 else 'cvlc'


def start_warning():
    global is_warning
    if not is_warning:
        is_warning = True
        wt = WarningThread()
        wt.start()


class WarningThread(threading.Thread):
    def run(self):
        global is_warning
        os.system(player + ' ' + warning_sound)
        is_warning = False
