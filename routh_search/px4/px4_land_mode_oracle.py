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

def get_land_event_and_pos(log_file):
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

def check_land_state_change(event_v):
    if len(event_v) != 5:
        return False
    state = ""
    for e in event_v:
        state += str(e[1])
        state += "."
    if state != "4.17.4.5.4.":
        return False
    return True

def get_land_pos_v(pos_v, land_cmd_timestamp):
    result = []
    last_alt = -10000.0
    for pos in pos_v:
        if pos['TimeUS'] > land_cmd_timestamp:
            result.append(copy.deepcopy(pos))
    return result

def check_land_pos_v(pos_v, land_lat, land_lng):    
    dis_v = []   
    for pos in pos_v:
        distance = get_distance(pos['Lat'], pos['Lng'], land_lat, land_lng)
        dis_v.append(distance)

    for dis in dis_v:
        
        if dis > 100:
            return 0
    
    return 1

if __name__ == "__main__":
    log_file_name = sys.argv[1]
    event_v, pos_v = get_land_event_and_pos(log_file_name)
    check_land_state_change(event_v)

    
    land_cmd_timestamp = event_v[3][0]

    land_pos_v = get_land_pos_v(pos_v, land_cmd_timestamp)
    land_lat = land_pos_v[0]['Lat']
    land_lng = land_pos_v[0]['Lng']
    if len(land_pos_v) == 0 or check_land_pos_v(land_pos_v, land_lat, land_lng) == 0:
        print(0)
        sys.exit(0)

    print(1)
    