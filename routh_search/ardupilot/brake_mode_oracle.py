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

def get_brake_event_and_pos(log_file):
    event_v = []
    pos_v = []
    while True:    
        msg = log_file.recv_msg()
        if msg is None:
            break
        if msg.get_type() == 'MAVC' and msg.to_dict()['Cmd'] == 176 and msg.to_dict()['P2'] == 17.0:
            event_v.append(msg.to_dict())
        if msg.get_type() == 'POS':
            pos_v.append(msg.to_dict())

    return (event_v, pos_v)

def get_brake_pos(pos_v, brake_timestamp):
    result = []
    for pos in pos_v:
        if pos['TimeUS'] > brake_timestamp:
            result.append(copy.deepcopy(pos))
    
    return result


def check_brake_pos_v(brake_pos_v):
    dis_v = []

    last_point_lat = brake_pos_v[len(brake_pos_v) - 1]['Lat']
    last_point_lng = brake_pos_v[len(brake_pos_v) - 1]['Lng']
    last_point_alt = brake_pos_v[len(brake_pos_v) - 1]['Alt']
    
    cnt = 0
    err_cnt = 0  
    for pos in reversed(brake_pos_v):
        distance = get_distance(pos['Lat'], pos['Lng'], last_point_lat, last_point_lng)
        alt_distance = pos['Alt'] - last_point_alt
        if distance < 150 and alt_distance < 0.05:
            cnt += 1
            if cnt > 100:
                return 1
        else:
            err_cnt += 1
            if err_cnt > 3:
                return 0
    
    return 0

if __name__ == "__main__":
    # log_file_name = "/home/li/pgfuzz/ardupilot/logs/00000001.BIN"
    log_file_name = sys.argv[1]
    log_file = mavutil.mavlink_connection(log_file_name)
    event_v, pos_v = get_brake_event_and_pos(log_file)
    brake_timestamp = event_v[0]['TimeUS']
    brake_pos_v = get_brake_pos(pos_v, brake_timestamp)

    print(check_brake_pos_v(brake_pos_v))
    
   