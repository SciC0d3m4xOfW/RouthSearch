import matplotlib.pyplot as plt
import pyulog
import sys
import copy
from math import radians, sin, cos, sqrt, atan2

def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    radius = 637100000.0

    distance = radius * c

    return distance

def get_distance(lat1, lng1, lat2, lng2):
    lat1_scale_up = lat1 * 1e7
    lng1_scale_up = lng1 * 1e7
    lat2_scale_up = lat2 * 1e7
    lng2_scale_up = lng2 * 1e7
    lat_d = lat1_scale_up - lat2_scale_up
    lng_d = lng1_scale_up - lng2_scale_up
    return sqrt(lat_d * lat_d + lng_d * lng_d)

def draw_traj(base_pos_v):
    index_v = []
    alt_v = []
    index = 0
    for base_pos in base_pos_v:
        index_v.append(index)
        alt_v.append(base_pos['Alt'])
    
    
    plt.plot(index_v, alt_v, label='alt_traj')
    
    plt.title('circle traj')
    plt.xlabel('Lat')
    plt.ylabel('Lng')
    
    plt.legend()
    
    plt.show()

import math

def quaternion_to_euler(q):
    
    sinr_cosp = 2 * (q.w * q.x + q.y * q.z)
    cosr_cosp = 1 - 2 * (q.x * q.x + q.y * q.y)
    roll = math.atan2(sinr_cosp, cosr_cosp)

    
    sinp = 2 * (q.w * q.y - q.z * q.x)
    if abs(sinp) >= 1:
        pitch = math.copysign(math.pi / 2, sinp)  
    else:
        pitch = math.asin(sinp)

    
    siny_cosp = 2 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
    yaw = math.atan2(siny_cosp, cosy_cosp)

    roll = roll * 180 / math.pi
    pitch = pitch * 180 / math.pi
    yaw = yaw * 180 / math.pi

    return roll, pitch, yaw


class Quaternion:
    def __init__(self, w, x, y, z):
        self.w = w
        self.x = x
        self.y = y
        self.z = z

def get_hold_event_and_pos(log_file):
    ulog = pyulog.ULog(log_file)
    data = ulog.data_list
    pos_v = []
    event_v = []
    att_v = []

    for d in data:
        if d.name == 'vehicle_gps_position':
            for i in range(1, len(d.data['timestamp'])):
                pos_v.append({'TimeUS' : d.data['timestamp'][i], 'Lat' : d.data['latitude_deg'][i], 'Lng' : d.data['longitude_deg'][i], 'Alt' : d.data['altitude_msl_m'][i]})
        elif d.name == 'vehicle_status':
            event_v = d.list_value_changes('nav_state')
        elif d.name == 'vehicle_attitude':
            for i in range(1, len(d.data['timestamp'])):
                q = Quaternion(d.data['q[0]'][i], d.data['q[1]'][i], d.data['q[2]'][i], d.data['q[3]'][i])
                roll , pitch , yaw = quaternion_to_euler(q)
                att_v.append({'TimeUS' : d.data['timestamp'][i], 'Roll' : roll, 'Pitch' : pitch, 'Yaw' : yaw})
            
    return (event_v, pos_v, att_v)

def check_hold_state_change(event_v):
    if len(event_v) != 3:
        return False
    state = ""
    for e in event_v:
        state += str(e[1])
        state += "."
    if state != "4.17.4.":
        return False
    return True

def get_hold_pos_and_att(pos_v, att_v , hold_cmd_timestamp):
    hold_pos_v = []
    hold_att_v = []
    for pos in pos_v:
        if pos['TimeUS'] > hold_cmd_timestamp:
            hold_pos_v.append(copy.deepcopy(pos))
    for att in att_v:
        if att['TimeUS'] > hold_cmd_timestamp:
            hold_att_v.append(copy.deepcopy(att))
    return (hold_pos_v, hold_att_v)

def check_hold_pos(hold_pos_v):

    last_point_lat = hold_pos_v[len(hold_pos_v) - 1]['Lat']
    last_point_lng = hold_pos_v[len(hold_pos_v) - 1]['Lng']
    last_point_alt = hold_pos_v[len(hold_pos_v) - 1]['Alt']
    
    cnt = 0
    err_cnt = 0  
    for pos in reversed(hold_pos_v):
        distance = get_distance(pos['Lat'], pos['Lng'], last_point_lat, last_point_lng)
        alt_distance = abs(pos['Alt'] - last_point_alt)
        if distance < 30 and alt_distance < 0.5:
            cnt += 1
            if cnt > 30:
                return 1
        else:
            err_cnt += 1
            if err_cnt > 3:
                return 0
    
    return 0

def check_hold_att(hold_att_v):

    last_point_roll = hold_att_v[len(hold_att_v) - 1]['Roll']
    last_point_pitch = hold_att_v[len(hold_att_v) - 1]['Pitch']
    last_point_yaw = hold_att_v[len(hold_att_v) - 1]['Yaw']
    
    cnt = 0
    err_cnt = 0  
    for att in reversed(hold_att_v):
        roll_err = abs(att['Roll'] - last_point_roll)
        pitch_err = abs(att['Pitch'] - last_point_pitch)
        yaw_err = abs(att['Yaw'] - last_point_yaw)
        print(f"roll_err:{roll_err}, pitch_err:{pitch_err}, yaw_err:{yaw_err}")
        
        
        
        
        
        
        
        
    
    return 0

if __name__ == "__main__":
    log_file_name = sys.argv[1]
    event_v, pos_v, att_v = get_hold_event_and_pos(log_file_name)
    if check_hold_state_change(event_v) == False:
        print(0)
        sys.exit(0)
    
    hold_cmd_timestamp = event_v[2][0]
    hold_pos_v, hold_att_v = get_hold_pos_and_att(pos_v, att_v , hold_cmd_timestamp)
    if check_hold_pos(hold_pos_v) == False:
        print(0)
        sys.exit(0)
    if check_hold_att(hold_att_v) == False:
        print(0)
        sys.exit(0)

    print(1)

    
    
    
    