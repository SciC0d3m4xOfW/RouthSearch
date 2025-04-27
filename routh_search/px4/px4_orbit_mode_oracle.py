import matplotlib.pyplot as plt
import pyulog
from pymavlink import mavutil, mavwp
import sys
from math import radians, sin, cos, sqrt, atan2

def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    radius = 6371.0

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
    lat_v = []
    lng_v = []
    for base_pos in base_pos_v:
        lat_v.append(base_pos['Lat'])
        lng_v.append(base_pos['Lng'])
    
    
    plt.plot(lat_v, lng_v, label='traj')
    
    plt.title('circle traj')
    plt.xlabel('Lat')
    plt.ylabel('Lng')
    
    plt.legend()
    
    plt.show()

def get_circle_pos(log_file):
    INIT_TIME = 120000000

    ulog = pyulog.ULog(log_file)
    data = ulog.data_list
    pos_v = []

    for d in data:
        if d.name == 'vehicle_gps_position':
            start_timestamp = d.data['timestamp'][0]
            for i in range(1, len(d.data['timestamp'])):
                if d.data['timestamp'][i] > start_timestamp + INIT_TIME:
                    pos_v.append({'TimeUS' : d.data['timestamp'][i], 'Lat' : d.data['latitude_deg'][i], 'Lng' : d.data['longitude_deg'][i], 'Alt' : d.data['altitude_msl_m'][i]})
    
    return pos_v

def calculate_major_axis_distance(pos_v):
    
    major_axis_distance = 0
    for pos_one in pos_v:
        for pos_two in pos_v:
            d = get_distance(pos_one['Lat'], pos_one['Lng'], pos_two['Lat'], pos_two['Lng'])
            if d > major_axis_distance:
                major_axis_distance = d
    
    return major_axis_distance

def check_major_axis_distance(pos_v, base_major_axis_distance):
    major_axis_distance = calculate_major_axis_distance(pos_v)
    if abs(base_major_axis_distance - major_axis_distance) / base_major_axis_distance > 0.05:
        return False
    return True

def check_trajectory_coincide(pos_v):
    check_index = 0
    lat_threshold = 0.000003
    lng_threshold = 0.00003
    lat_to_check = pos_v[check_index]['Lat']
    lng_set = set()
    lng_set.add(pos_v[check_index]['Lng'])
    for pos in pos_v[check_index + 1:]:
        if abs(pos['Lat'] - lat_to_check) <= lat_threshold:
            min_distance = sys.float_info.max
            for lng in lng_set:
                if abs(pos['Lng'] - lng) < min_distance:
                    min_distance = abs(pos['Lng'] - lng)
            if min_distance > lng_threshold:
                if len(lng_set) >= 2:
                    return False
                else:
                    lng_set.add(pos['Lng'])
    return True
    
if __name__ == "__main__":
    base_log_file_name = "/home/li/Downloads/base_orbit.ulg"
    base_pos_v = get_circle_pos(base_log_file_name)
    

    base_major_axis_distance = calculate_major_axis_distance(base_pos_v)

    log_file_name = sys.argv[1]
    pos_v = get_circle_pos(log_file_name)
    draw_traj(pos_v)
    
    if check_major_axis_distance(pos_v, base_major_axis_distance) == False or check_trajectory_coincide(pos_v) == False:
        print(0)
        sys.exit(0)
    
    print(1)