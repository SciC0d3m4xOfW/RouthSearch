import time
import os
import sys
import signal
import subprocess
from subprocess import check_output
import psutil

ARDUPILOT_FUZZ_HOME = os.getenv("ARDUPILOT_FUZZ_HOME")

if ARDUPILOT_FUZZ_HOME is None:
    raise Exception("ARDUPILOT_FUZZ_HOME environment variable is not set!")

ARDUPILOT_HOME = os.getenv("ARDUPILOT_HOME")
if ARDUPILOT_HOME is None:
    raise Exception("ARDUPILOT_HOME environment variable is not set!")

start_ardupilot = "{}/Tools/autotest/sim_vehicle.py -v ArduCopter --map --console -w".format(ARDUPILOT_HOME)

c = 'exec python3 ' + start_ardupilot

cmd_list = ["gnome-terminal", "--", f"{ARDUPILOT_HOME}/Tools/autotest/sim_vehicle.py", "-v", "ArduCopter", "--map", "--console", "-w"]

proc = subprocess.Popen(cmd_list, stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=False)
time.sleep(60)

sys.exit()

