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

    print("Switching to Orbit Mode...")

    # Send command to switch to Orbit Mode
    # pxa.do_orbit(100, 47.3987785, 8.54634364, 50)
    pxa.do_orbit(50, 47.3998785, 8.54634364, float("NAN"))


    print("Switched to Orbit Mode!")
    time.sleep(180)

if __name__ == "__main__":
    main()

