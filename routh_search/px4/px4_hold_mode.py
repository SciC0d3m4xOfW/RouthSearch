import time
from pymavlink import mavutil
from PX4Util import PX4Agent

# Main function
def main():
    pxa = PX4Agent()
    
    pxa.change_mode("TAKEOFF")

    print("-- Arm PX4")
    pxa.arm_throttle()

    print("-- Takeoff PX4")
    pxa.takeoff(30)

    time.sleep(45)

    print("--Hold Mode")

    time.sleep(10)

if __name__ == "__main__":
    main()

