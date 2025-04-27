#
# This file provides functions to better interact with Ardupilot
#
from pymavlink import mavutil, mavwp
class APAgent:
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
        self.mav.mav.command_long_send(self.mav.target_system, self.mav.target_component,
                                             mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0, 0, 0, 0, 0, 0, 0, takeoff_altitude)

        takeoff_msg = self.mav.recv_match(type='COMMAND_ACK', timeout=30)
        print(f"--take off done")

    def change_mode(self, mode):
        mode_id = 0
        sub_mode = 0

        if mode not in self.mav.mode_mapping():
            print(f'Unknown mode : {mode}')
            print(f"available modes: {list(self.mav.mode_mapping().keys())}")
            raise Exception('Unknown mode')
            sub_mode = 0
            
        # Get mode ID
        mode_id = self.mav.mode_mapping()[mode]


        self.mav.mav.command_long_send(self.mav.target_system, self.mav.target_component, mavutil.mavlink.MAV_CMD_DO_SET_MODE,
                                    0, mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, mode_id, sub_mode, 0, 0, 0, 0)
        ack_msg = self.mav.recv_match(type='COMMAND_ACK', timeout=30)
        print(f"--mode changed to {mode}")

    def guided_fly_to(self, lan, lang, altitude):
        self.mav.mav.send(mavutil.mavlink.MAVLink_set_position_target_global_int_message(10, self.mav.target_system,
                self.mav.target_component, 
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, int(0b110111111000), 
                        int(lan * 10 ** 7), int(lang * 10 ** 7), altitude, 0, 0, 0, 0, 0, 0, 1.57, 0.5))

        msg = self.mav.recv_match(
            type='LOCAL_POSITION_NED', timeout=30)
        print("-- guided fly done!")

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
        # while True:
           # msg = self.mav.recv_match(type="PARAM_VALUE",  timeout=10)
           # msg_dict = msg.to_dict()
           # if msg_dict["param_id"] == name:
               # print('Receive name: %s\tvalue: %f' %(message['param_id'], message['param_value']))
               # break


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
        if id < 9:
            rc_channel_values = [65535 for _ in range(8)]
            rc_channel_values[id - 1] = pwm

            # global master
            self.mav.mav.rc_channels_override_send(
                self.mav.target_system,  # target_system
                self.mav.target_component,  # target_component
                *rc_channel_values)  # RC channel list, in microseconds.

class APLogParser:
    """
    Log Parser for Ardupilot log file.
    """
    def __init__(self, log_file_path):
        self.log_file = mavutil.mavlink_connection(log_file_path)

    def parse(self):
        logs = []
        while True:
            msg = self.log_file.recv_msg()
            if msg is None:
                break

            logs.append(msg)

        return logs









    

