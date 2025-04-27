import time
import os
import sys
import signal
import subprocess
from subprocess import check_output

def kill_process(name):
    raw_opt = check_output("ps aux | grep %s | awk '{print $2;}'"%name, shell=True) 
    pid_strs = [pid_raw.decode('ascii') for pid_raw in raw_opt.split(b'\n')]
    for pid_str in pid_strs:
        if pid_str != '':
            try:
                os.kill(int(pid_str), signal.SIGKILL)
            except ProcessLookupError:
                pass

kill_process("mavproxy")

