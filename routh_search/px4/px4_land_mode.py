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

    print("--Fly to Mission Point")

    # Send command to switch to Orbit Mode
    # pxa.do_orbit(100, 47.3987785, 8.54634364, 50)
    pxa.guided_fly_to(47.4014527, 8.5452711, 50)

   # pxa.guided_fly_to(4000, 4000, -10)
    time.sleep(120)
    print("-- Guided Fly Done!")

    pxa.change_mode("LAND")
    time.sleep(120)

if __name__ == "__main__":
    main()

