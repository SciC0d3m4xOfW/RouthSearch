import time
import json
import sys
import threading
from pymavlink import mavutil
from ArdupilotUtil import APAgent

apa = APAgent()
def json_to_pid_config(json_file_hdr):
    raw_config = json.load(json_file_hdr)
    pid_config = {}

    for key, value in raw_config.items():
        pid_config[key.encode('ascii')] = value

    return pid_config

def rc3_th(stop_event, apa, pwm):
    while not stop_event.is_set():
        apa.set_rc_channel_pwm(3, pwm)
        time.sleep(0.2)

def main(argv):
    pid_file = argv[1]
    with open(pid_file) as pf:
        pid_config = json_to_pid_config(pf)

        print("--init")
        apa.change_mode("GUIDED")
        apa.arm_throttle()
        time.sleep(1)

        apa.takeoff(30)
        time.sleep(30)

        print("--Set rc 3 to 1500")
        rc3_thread_stop_event = threading.Event()
        rc3_thread = threading.Thread(target=rc3_th, args=(rc3_thread_stop_event, apa, 1500))
        rc3_thread.start()
        
        apa.guided_fly_to(-35.36010683154955, 149.15992263447498, 100.0)
        time.sleep(12)

        apa.change_mode("BRAKE")
        time.sleep(30)
        
        print("--current sampling done")

        # Exit this sample
        rc3_thread_stop_event.set()
        rc3_thread.join()
        sys.exit()


if __name__ == "__main__":
    main(sys.argv)


