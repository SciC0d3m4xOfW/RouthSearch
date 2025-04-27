#
# This file provides functions to better interact with Ardupilot
#
from pymavlink import mavutil, mavwp
class PX4Agent:
    def __init__(self):
        connection_string = '127.0.0.1:14550'
        self.mav = mavutil.mavlink_connection('udp:'+connection_string)
        self.mav.wait_heartbeat()
        print("--heartbeat okay\n")

    def arm_throttle(self):
        self.mav.mav.command_long_send(1, 1, mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0,
                              1,
                              0, 0, 0, 0, 0, 0)
        msg = self.mav.recv_match(type=['COMMAND_ACK'],blocking=True)
        print ("--arm throttle done!\n")

    def disam(self):
        self.mav.mav.command_long_send(1, 1, mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0,
                              0,
                              0, 0, 0, 0, 0, 0)
        msg = self.mav.recv_match(type=['COMMAND_ACK'],blocking=True)
        print ("--disarm done!\n")

    def takeoff(self, takeoff_altitude):
        # Command Takeoff
        msg = self.mav.recv_match(type='GLOBAL_POSITION_INT', blocking=True)
        starting_alt = msg.alt / 1000

        self.mav.mav.command_long_send(self.mav.target_system, self.mav.target_component,
                                             mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0, 0, 0, 0, 0, 
                                             float("NAN"), float("NAN"), starting_alt + takeoff_altitude)

        takeoff_msg = self.mav.recv_match(type='COMMAND_ACK', blocking=True)
        print(f"--take off done")

    def change_mode(self, mode_name):
        if mode_name not in self.mav.mode_mapping():
            print(f'Unknown mode : {mode_name}')
            print(f"available modes: {list(self.mav.mode_mapping().keys())}")
            raise Exception('Unknown mode')
            
        # Get mode ID
        mode = self.mav.mode_mapping()[mode_name]

        self.mav.mav.command_long_send(self.mav.target_system, self.mav.target_component, mavutil.mavlink.MAV_CMD_DO_SET_MODE,
                                    0, mode[0], mode[1], mode[2], 0, 0, 0, 0)
        ack_msg = self.mav.recv_match(type='COMMAND_ACK', timeout=30)
        print(f"--mode changed to {mode}")

    def do_orbit(self, radius, latitude, longitude, altitude):
        MAV_CMD_DO_ORBIT=34
        self.mav.mav.command_long_send(
            self.mav.target_system,
            self.mav.target_component,
            MAV_CMD_DO_ORBIT,
            0,
            radius,  
            10,
            0,  
            0,              
            latitude,  
            longitude,  
            altitude
        )
        ack_msg = self.mav.recv_match(type='COMMAND_ACK', timeout=30)
        print("--do orbit succeed")

    """
    def guided_fly_to(self, north, east, down):
        self.mav.mav.send(mavutil.mavlink.MAVLink_set_position_target_local_ned_message(10, self.mav.target_system,
                         self.mav.target_component, mavutil.mavlink.MAV_FRAME_LOCAL_NED, int(0b010111111000), north, east, down, 0, 0, 0, 0, 0, 0, 1.57, 0.5))

        msg = self.mav.recv_match(
            type='LOCAL_POSITION_NED', timeout=30)
        print("-- guided fly done!")
    """

    """
    def guided_fly_to(self, lan, lang, altitude):
        self.mav.mav.send(mavutil.mavlink.MAVLink_set_position_target_global_int_message(10, self.mav.target_system,
                self.mav.target_component,
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT, 
                int(0b110111111000),
                        int(lan * 10 ** 7), int(lang * 10 ** 7), altitude, 0, 0, 0, 0, 0, 0, 1.57, 0.5))

        msg = self.mav.recv_match(
            type='LOCAL_POSITION_NED', timeout=30)
        print("-- guided fly done!")
    """

    def guided_fly_to(self, latitude, longitude, altitude):
        MAV_CMD_DO_REPOSITION=192
        MAV_DO_REPOSITION_FLAGS_CHANGE_MODE=1
        self.mav.mav.command_long_send(
            self.mav.target_system,
            self.mav.target_component,
            MAV_CMD_DO_REPOSITION,
            0,
            -1.0,
            MAV_DO_REPOSITION_FLAGS_CHANGE_MODE,
            0.0,
            float("NAN"),
            latitude,  
            longitude,  
            float("NAN")
        )
        ack_msg = self.mav.recv_match(type='COMMAND_ACK', timeout=30)

    def write_parameter(self, name, value):
        print('Send name: %s\tvalue: %f' %
              (name, value))

        # Set parameter value
        # Set a parameter value TEMPORARILY to RAM. It will be reset to default on system reboot.
        # Send the ACTION MAV_ACTION_STORAGE_WRITE to PERMANENTLY write the RAM contents to EEPROM.
        # The parameter variable type is described by MAV_PARAM_TYPE in http://mavlink.org/messages/common.
        self.mav.mav.param_set_send(
            self.mav.target_system, self.mav.target_component,
            name,
            value,
            mavutil.mavlink.MAV_PARAM_TYPE_REAL32
        )

        # Read ACK
        # IMPORTANT: The receiving component should acknowledge the new parameter value by sending a
        # param_value message to all communication partners.
        # This will also ensure that multiple GCS all have an up-to-date list of all parameters.
        # If the sending GCS did not receive a PARAM_VALUE message within its timeout time,
        # it should re-send the PARAM_SET message.
        message = self.mav.recv_match(type='PARAM_VALUE', blocking=True).to_dict()
        print('Receive name: %s\tvalue: %f' %
              (message['param_id'], message['param_value']))


    def tune_pid(self, pid_map):
        """
        Tuning pid parameter value {name:=value}
        """
        for key, value in pid_map.items():
            self.write_parameter(key, value)

    def read_parameter(self, name):
        # Request parameter
        self.mav.mav.param_request_read_send(
            self.mav.target_system, self.mav.target_component,
            name,
            -1
        )

        # Print old parameter value
        message = self.mav.recv_match(type='PARAM_VALUE', timeout=30).to_dict()
        print('name: %s\tvalue: %d' %
              (message['param_id'], message['param_value']))

    def get_alt(self):
        """Wait to be landed"""
        m = self.mav.recv_match(type='GLOBAL_POSITION_INT', timeout=30)
        alt = m.relative_alt / 1000.0 # mm -> m
        return alt

    # ------------------------------------------------------------------------------------
    # Create a function to send RC values
    # More information about Joystick channels
    # here: https://www.ardusub.com/operators-manual/rc-input-and-output.html#rc-inputs
    def set_rc_channel_pwm(self, id, pwm=1500):
        """ Set RC channel pwm value
        Args:
            id (TYPE): Channel ID
            pwm (int, optional): Channel pwm value 1100-1900
        """
        if id < 1:
            print("Channel does not exist.")
            return

        # We only have 8 channels
        # https://mavlink.io/en/messages/common.html#RC_CHANNELS_OVERRIDE
        if id < 18:
            rc_channel_values = [65535 for _ in range(18)]
            rc_channel_values[id - 1] = pwm

            # global master
            self.mav.mav.rc_channels_override_send(
                self.mav.target_system,  # target_system
                self.mav.target_component,  # target_component
                *rc_channel_values)  # RC channel list, in microseconds.


    def send_wp_to_airframe(self, wp):
        # Send Waypoint to airframe
        self.mav.waypoint_clear_all_send()
        self.mav.waypoint_count_send(wp.count())

        for i in range(wp.count()):
            msg = self.mav.recv_match(type=['MISSION_REQUEST'],blocking=True)
            self.mav.mav.send(wp.wp(msg.seq))
            print('--Sending waypoint %s' %(msg.seq))

        msg = self.mav.recv_match(type=['MISSION_ACK'],blocking=True) # OKAY
        print("--send waypoint done!")

    def read_wp_from_airframe(self):
        # Read Waypoint from airframe
        self.mav.waypoint_request_list_send()
        waypoint_count = 0

        msg = self.mav.recv_match(type=['MISSION_COUNT'],blocking=True)
        waypoint_count = msg.count
        print("--Got %d waypoints" %waypoint_count)

        for i in range(waypoint_count):
            self.mav.waypoint_request_send(i)
            msg = self.mav.recv_match(type=['MISSION_ITEM'],blocking=True)
            print('Receving waypoint {0}'.format(msg.seq))
            print(msg)

        self.mav.mav.mission_ack_send(self.mav.target_system, self.mav.target_component, 0) # OKAY









    

