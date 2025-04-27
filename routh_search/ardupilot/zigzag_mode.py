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

def rc7_th(stop_event, apa, pwm):
    while not stop_event.is_set():
        apa.set_rc_channel_pwm(7, pwm)
        time.sleep(0.2)

def main(argv):
    pid_file = argv[1]
    with open(pid_file) as pf:
        pid_config = json_to_pid_config(pf)

        print("--set RC7_OPTION to 61(zigzag saveWP)")
        apa.write_parameter(b"RC7_OPTION", 61)

        print("--init")
        apa.change_mode("GUIDED")
        apa.arm_throttle()
        time.sleep(1)

        apa.takeoff(30)
        time.sleep(20)

        print("--Set rc 3 to 1500")
        rc3_thread_stop_event = threading.Event()
        rc3_thread = threading.Thread(target=rc3_th, args=(rc3_thread_stop_event, apa, 1500))
        rc3_thread.start()
        print("--Set rc 3 to 1500")
        rc7_thread_stop_event = threading.Event()
        rc7_thread = threading.Thread(target=rc7_th, args=(rc7_thread_stop_event, apa, 1500))
        rc7_thread.start()

        print("--Change to loiter mode")
        apa.change_mode("LOITER")
        time.sleep(5)
        
        print("--Change to zigzag mode")
        apa.change_mode("ZIGZAG")
        time.sleep(5)

        # manually fly time(10s = count * mf_sleep_time)
        count=50
        mf_sleep_time = 0.2
        print(f"--manually fly to point A")
        while count > 0:
            apa.set_rc_channel_pwm(1, 1000)
            time.sleep(mf_sleep_time)
            count -= 1

        apa.set_rc_channel_pwm(1, 1500)
        print(f"--wait 5s to stop")
        time.sleep(5)
        print(f"--set zigzag point A")
        rc7_thread_stop_event.set()
        rc7_thread.join()
        rc7_thread_stop_event = threading.Event()
        rc7_thread = threading.Thread(target=rc7_th, args=(rc7_thread_stop_event, apa, 1000))
        rc7_thread.start()
        time.sleep(5)

        print(f"manually fly to piont B")
        count = 50
        while count > 0:
            apa.set_rc_channel_pwm(2, 1000)
            time.sleep(mf_sleep_time)
            count -= 1
        
        apa.set_rc_channel_pwm(2, 1500)
        print(f"--wait 5s to stop")
        time.sleep(5)
        print(f"--set zigzag point B")
        rc7_thread_stop_event.set()
        rc7_thread.join()
        rc7_thread_stop_event = threading.Event()
        rc7_thread = threading.Thread(target=rc7_th, args=(rc7_thread_stop_event, apa, 1900))
        rc7_thread.start()
        time.sleep(5)

        #zigzag count
        k = 2
        while k > 0:
            count = 50
            print(f"--manually fly to point B\'")
            while count > 0:
                apa.set_rc_channel_pwm(1, 1000)
                time.sleep(mf_sleep_time)
                count -= 1

            apa.set_rc_channel_pwm(1, 1500)
            print(f"--wait 5s to stop")
            time.sleep(5)
            print(f"zigzag auto fly")
            rc7_thread_stop_event.set()
            rc7_thread.join()
            rc7_thread_stop_event = threading.Event()
            rc7_thread = threading.Thread(target=rc7_th, args=(rc7_thread_stop_event, apa, 1000))
            rc7_thread.start()
            time.sleep(25)

            print(f"manually fly to piont A\'")
            count = 50
            while count > 0:
                apa.set_rc_channel_pwm(1, 1000)
                time.sleep(mf_sleep_time)
                count -= 1
        
            apa.set_rc_channel_pwm(1, 1500)
            print(f"--wait 5s to stop")
            time.sleep(5)
            print(f"zigzag auto fly")
            rc7_thread_stop_event.set()
            rc7_thread.join()
            rc7_thread_stop_event = threading.Event()
            rc7_thread = threading.Thread(target=rc7_th, args=(rc7_thread_stop_event, apa, 1900))
            rc7_thread.start()
            time.sleep(25)
            
            k -= 1


        print("--current sampling done")

        # Exit this sample
        rc3_thread_stop_event.set()
        rc3_thread.join()
        rc7_thread_stop_event.set()
        rc7_thread.join()
        sys.exit()


if __name__ == "__main__":
    main(sys.argv)


