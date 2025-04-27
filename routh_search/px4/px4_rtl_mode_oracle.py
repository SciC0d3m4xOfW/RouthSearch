import matplotlib.pyplot as plt
import pyulog
from pymavlink import mavutil, mavwp
import sys
from math import radians, sin, cos, sqrt, atan2
import copy

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


def normalize_list(input_list):
    if not input_list:
        return []

    min_val = min(input_list)
    max_val = max(input_list)

    if min_val == max_val:
        
        return [0.0] * len(input_list)

    normalized_list = [(x - min_val) / (max_val - min_val) for x in input_list]

    return normalized_list

def draw_traj(base_pos_v):
    time_v = []
    lat_v = []
    lng_v = []
    alt_v = []
    for base_pos in base_pos_v:
        time_v.append(base_pos['TimeUS'])
        lat_v.append(base_pos['Lat'])
        lng_v.append(base_pos['Lng'])
        alt_v.append(base_pos['Alt'])
    
    lat_v = normalize_list(lat_v)
    lng_v = normalize_list(lng_v)
    alt_v = normalize_list(alt_v)
    
    plt.plot(time_v, lat_v, label='traj')
    plt.plot(time_v, lng_v, label='traj')
    plt.plot(time_v, alt_v, label='traj')
    
    plt.title('circle traj')
    plt.xlabel('time')
    plt.ylabel('Lat')
    
    plt.legend()
    
    plt.show()

def get_rtl_event_and_pos(log_file):
    ulog = pyulog.ULog(log_file)
    data = ulog.data_list
    pos_v = []
    event_v = []

    for d in data:
        if d.name == 'vehicle_gps_position':
            for i in range(1, len(d.data['timestamp'])):
                pos_v.append({'TimeUS' : d.data['timestamp'][i], 'Lat' : d.data['latitude_deg'][i], 'Lng' : d.data['longitude_deg'][i], 'Alt' : d.data['altitude_msl_m'][i]})
        elif d.name == 'vehicle_status':
            event_v = d.list_value_changes('nav_state')
    return (event_v, pos_v)

def check_rtl_state_change(event_v):
    if len(event_v) != 5:
        return False
    state = ""
    for e in event_v:
        state += str(e[1])
        state += "."
    if state != "4.17.4.5.4.":
        return False
    return True

def get_return_pos_v(pos_v, rtl_cmd_timestamp, land_cmd_timestamp):
    result = []
    for pos in pos_v:
        if pos['TimeUS'] > rtl_cmd_timestamp and pos['TimeUS'] < land_cmd_timestamp:
            result.append(copy.deepcopy(pos))
    return result

def get_land_pos_v(pos_v, hit_ground_timestamp):
    result = []
    max_alt = -10000.0
    land_cmd_timestamp = -1
    for pos in reversed(pos_v):
        if pos['TimeUS'] >= hit_ground_timestamp:
            continue
        if pos['Alt'] > max_alt + 0.3:
            max_alt = pos['Alt']
            land_cmd_timestamp = pos['TimeUS']

    for pos in pos_v:
        if pos['TimeUS'] > land_cmd_timestamp and pos['TimeUS'] <= hit_ground_timestamp:
            result.append(copy.deepcopy(pos))
    return result

def check_land_pos_v(pos_v, home_lat, home_lng):
    dis_v = []    
    for pos in reversed(pos_v):
        
        distance = get_distance(pos['Lat'], pos['Lng'], home_lat, home_lng)
        dis_v.append(distance)
    cnt = 0
    for dis in dis_v:
        
        
        if dis > 50:
            print(dis)
            return 0
        else:
            cnt += 1
            if cnt > 100:
                return 1
    
    return 1

def check_return_pos_v(pos_v):
    dis_v = []    
    base_alt = pos_v[0]['Alt']

    for pos in pos_v[1:]:
        distance = abs(pos['Alt'] - base_alt)
        dis_v.append(distance)

    cnt = 0
    for dis in dis_v:
        
        
        if dis > 50:
            print(dis)
            return 0
        else:
            cnt += 1
            if cnt > 100:
                return 1
    
    return 1
    
if __name__ == "__main__":
    log_file_name = sys.argv[1]
    event_v, pos_v = get_rtl_event_and_pos(log_file_name)
    
    if check_rtl_state_change(event_v) == False:
        print(0)
        sys.exit(0)

    home_lat = pos_v[0]['Lat']
    home_lng = pos_v[0]['Lng']

    
    rtl_cmd_timestamp = event_v[3][0]
    hit_ground_timestamp = event_v[4][0]

    land_pos_v = get_land_pos_v(pos_v, hit_ground_timestamp)
    if len(land_pos_v) == 0 or check_land_pos_v(land_pos_v, home_lat, home_lng) == 0:
        print(0)
        sys.exit(0)

    land_cmd_timestamp = land_pos_v[0]['TimeUS']

    return_pos_v = get_return_pos_v(pos_v, rtl_cmd_timestamp ,land_cmd_timestamp)
    if len(return_pos_v) == 0 or check_return_pos_v(return_pos_v) == 0:
        print(0)
        sys.exit(0)


    print(1)
