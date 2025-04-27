import matplotlib.pyplot as plt
from pymavlink import mavutil, mavwp
import sys
import math
import subprocess
import os
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

def get_rtl_event_and_pos(log_file):
    event_v = []
    pos_v = []
    while True:    
        msg = log_file.recv_msg()
        if msg is None:
            break
        if msg.get_type() == 'MAVC' and msg.to_dict()['Cmd'] == 176 and msg.to_dict()['P2'] == 6.0:
            event_v.append(msg.to_dict())
        if msg.get_type() == 'MSG' and msg.to_dict()['Message'].find('SIM Hit ground') != -1:
            event_v.append(msg.to_dict())

        if msg.get_type() == 'POS':
            pos_v.append(msg.to_dict())

    return (event_v, pos_v)

def get_return_pos_v(pos_v, rtl_cmd_timestamp, land_cmd_timestamp):
    result = []
    for pos in pos_v:
        if pos['TimeUS'] > rtl_cmd_timestamp and pos['TimeUS'] < land_cmd_timestamp:
            result.append(copy.deepcopy(pos))
    return result

def get_land_pos_v(pos_v, hit_ground_timestamp):
    result = []
    last_alt = -10000.0
    for pos in reversed(pos_v):
        if pos['TimeUS'] > hit_ground_timestamp:
            continue
        if pos['RelHomeAlt'] >= last_alt:
            last_alt = pos['RelHomeAlt']
            result.append(copy.deepcopy(pos))
        else:
            break
    result.reverse()
    return result

def check_land_pos_v(pos_v, home_lat, home_lng):
    dis_v = []    
    cnt = 0
    for pos in reversed(pos_v):
        distance = get_distance(pos['Lat'], pos['Lng'], home_lat, home_lng)
        dis_v.append(distance)
    
    for dis in dis_v:
        #100cm
        print(dis)
        cnt += 1
        if dis > 200:
            return 0
        if cnt > 100:
            return 1
    return 1

def check_return_pos_v(pos_v):
    max_alt = sys.float_info.min
    min_alt = sys.float_info.max
    for pos in pos_v:
        if pos['RelHomeAlt'] > max_alt:
            max_alt = pos['RelHomeAlt']
        if pos['RelHomeAlt'] < min_alt:
            min_alt = pos['RelHomeAlt']
    # 1m
    if max_alt - min_alt > 1:
        return 0
    
    return 1
if __name__ == "__main__":
    # log_file_name = "/home/li/pgfuzz/ardupilot/logs/00000001.BIN"
    log_file_name = sys.argv[1]
    log_file = mavutil.mavlink_connection(log_file_name)
    event_v, pos_v = get_rtl_event_and_pos(log_file)

    if len(event_v) != 2 or len(pos_v) == 0:
        print(0)
        sys.exit(0)

    home_lat = pos_v[0]['Lat']
    home_lng = pos_v[0]['Lng']

    rtl_cmd_timestamp = event_v[0]['TimeUS']
    hit_ground_timestamp = event_v[1]['TimeUS']

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
    
   