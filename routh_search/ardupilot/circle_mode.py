import time
import json
import sys
from pymavlink import mavutil
from ArdupilotUtil import APAgent

apa = APAgent()
def json_to_pid_config(json_file_hdr):
    raw_config = json.load(json_file_hdr)
    pid_config = {}

    for key, value in raw_config.items():
        pid_config[key.encode('ascii')] = value

    return pid_config

def main(argv):
    pid_file = argv[1]
    with open(pid_file) as pf:
        pid_config = json_to_pid_config(pf)

        apa.write_parameter(b"CIRCLE_RADIUS", 10000)
        apa.change_mode("GUIDED")
        apa.arm_throttle()
        time.sleep(3)

        apa.takeoff(30)
        time.sleep(20)

        print("--Set rc 3 to 1500")
        apa.set_rc_channel_pwm(3, 1500)

        apa.change_mode("CIRCLE")
        count=300
        print(f"--waiting for {count}s")
        while count > 0:
            apa.set_rc_channel_pwm(3, 1500)
            time.sleep(1)
            count -= 1

        print("--current sampling done")

        # Exit this sample
        sys.exit()


if __name__ == "__main__":
    main(sys.argv)


