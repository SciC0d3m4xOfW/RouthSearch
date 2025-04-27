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

    radius = 6371.0

    distance = radius * c

    return distance

def get_zigzag_statechange_and_pos(log_file):
    zigzag_statechange_v = []
    pos_v = []
    while True:    
        msg = log_file.recv_msg()
        if msg is None:
            break

        if msg.get_type() == 'AUXF':
            zigzag_statechange_v.append(msg.to_dict())
        
        if msg.get_type() == 'MSG' and msg.to_dict()['Message'] == 'ZigZag: manual control':
            zigzag_statechange_v.append(msg.to_dict())

        if msg.get_type() == 'SIM':
            pos_v.append(msg.to_dict())
    
    return (zigzag_statechange_v, pos_v)

def check_zigzag_statechage(zigzag_statechange_v):
    statechange_str = ""
    for zigzag_state in zigzag_statechange_v:
        if zigzag_state['mavpackettype'] == 'AUXF':
            statechange_str += str(zigzag_state['pos'])
        elif zigzag_state['mavpackettype'] == 'MSG':
            statechange_str += 'm'
    # print(statechange_str)
    # maybe "1020m2m0m2m"
    if statechange_str == "1020m2m0m2" or statechange_str == "1020m2m0m2m":
        return True
    else:
        return False
    
def calculate_manual_auto_average_distance(base_distance_v):
    manual_average_distance = 0
    auto_average_distance = 0
    # print(base_distance_v)
    for i in range(len(base_distance_v)):
        if i % 2 == 1:
            manual_average_distance += base_distance_v[i]
        else:
            auto_average_distance += base_distance_v[i]
    
    manual_len = int(len(base_distance_v) / 2)
    # print(manual_len)
    auto_len = len(base_distance_v) - manual_len

    manual_average_distance /= manual_len
    auto_average_distance /= auto_len
    
    return (manual_average_distance, auto_average_distance)

def get_zigzag_statechange_time(zigzag_statechange_v):
    state_change_time_v = []
    for index, zigzag_state in enumerate(zigzag_statechange_v):
        # skip init
        if zigzag_state['mavpackettype'] == 'AUXF' and zigzag_state['pos'] == 1:
            continue
        # skip end
        if zigzag_state['mavpackettype'] == 'MSG' and index == len(zigzag_statechange_v) - 1:
            break
        state_change_time_v.append(zigzag_state['TimeUS'])
    return state_change_time_v

def split_pos_v_by_statechange_time(pos_v, statechange_time_v):
    result = []
    if len(statechange_time_v) == 0:
        result = pos_v
        return result
    
    current_split = []
    state_i = 0
    for item in pos_v:
        current_time = item['TimeUS']
        
        #skip invalid pos
        if state_i == 0 and current_time < statechange_time_v[state_i]:
            continue
        
        if state_i < len(statechange_time_v)  - 1 and current_time >= statechange_time_v[state_i] and current_time < statechange_time_v[state_i + 1]:
            current_split.append({'Alt': item['Alt'], 'Lat': item['Lat'], 'Lng': item['Lng'], 'TimeUS': item['TimeUS']})
        elif state_i == len(statechange_time_v)  - 1:
            current_split.append({'Alt': item['Alt'], 'Lat': item['Lat'], 'Lng': item['Lng'], 'TimeUS': item['TimeUS']})
            continue
        else:
            result.append(copy.deepcopy(current_split))
            current_split.clear()
            current_split.append({'Alt': item['Alt'], 'Lat': item['Lat'], 'Lng': item['Lng'], 'TimeUS': item['TimeUS']})
            state_i += 1

    # last split
    if current_split:
        result.append(copy.deepcopy(current_split))

    return result

def calculate_distance(split_pos_v):
    results = []
    
    for split_pos in split_pos_v:
        distance = haversine(split_pos[0]['Lat'], split_pos[0]['Lng'], split_pos[len(split_pos) - 1]['Lat'], split_pos[len(split_pos) - 1]['Lng'])
        results.append(distance)
    
    return results

def check_distance(distance_v, manual_average_distance, auto_average_distance):
    max_manual_distance = sys.float_info.min
    min_manual_distance = sys.float_info.max
    max_auto_distance = sys.float_info.min
    min_auto_distance = sys.float_info.max
    for i in range(len(distance_v)):
        # manual mode
        if i % 2 == 1:
            if distance_v[i] > max_manual_distance:
                max_manual_distance = distance_v[i]
            if distance_v[i] < min_manual_distance:
                min_manual_distance = distance_v[i]
        # auto mode
        else:
            if distance_v[i] > max_auto_distance:
                max_auto_distance = distance_v[i]
            if distance_v[i] < min_auto_distance:
                min_auto_distance = distance_v[i]
    # print(f"max_m:{max_manual_distance}, min_m:{min_manual_distance}")
    if (max_manual_distance - min_manual_distance) > manual_average_distance * 0.15:
        return False
    # print(max_auto_distance - min_auto_distance)
    if (max_auto_distance - min_auto_distance) > auto_average_distance * 0.15:
        return False
    
    return True

if __name__ == "__main__":
    base_log_file_name = "./oracle_logs/base.BIN"
    base_log_file = mavutil.mavlink_connection(base_log_file_name)
    base_zigzag_statechange_v, base_pos_v = get_zigzag_statechange_and_pos(base_log_file)
    base_statechange_time_v = get_zigzag_statechange_time(base_zigzag_statechange_v)
    base_split_pos_v = split_pos_v_by_statechange_time(base_pos_v, base_statechange_time_v)
    base_distance_v = calculate_distance(base_split_pos_v)
    base_manual_ave_dis, base_auto_ave_dis = calculate_manual_auto_average_distance(base_distance_v)
    # print(f"manual average distance: {base_manual_ave_dis}\nauto average distance: {base_auto_ave_dis}")
    
    
    # command = "ls -v /home/li/pgfuzz/pgfuzz/test_script/data/zigzag_mode_pid_tuning_log/zigzag_mode_pid_tuning/"
    # result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, text=True)
    # output_lines = result.stdout.splitlines()
    # print(output_lines)
    # path = "/home/li/pgfuzz/pgfuzz/test_script/data/zigzag_mode_pid_tuning_log/zigzag_mode_pid_tuning/"
    # for line in output_lines:
    #     log_file = mavutil.mavlink_connection(path + line)
    #     zigzag_statechange_v, pos_v = get_zigzag_statechange_and_pos(log_file)
    #     if check_zigzag_statechage(zigzag_statechange_v) == False:
    #         # state change error
    #         print(int(False))
    #         continue
    #     statechange_time_v = get_zigzag_statechange_time(zigzag_statechange_v)
    #     # print(statechange_time_v)
    #     split_pos_v = split_pos_v_by_statechange_time(pos_v, statechange_time_v)
    #     # for split_pos in split_pos_v:
    #     #     print(split_pos)
    #     distance_v = calculate_distance(split_pos_v)
    #     print(int(check_distance(distance_v, base_manual_ave_dis, base_auto_ave_dis)))

    # path = "/home/li/pgfuzz/pgfuzz/test_script/data/zigzag_mode_pid_tuning_log/zigzag_mode_pid_tuning/"
    # log_file = mavutil.mavlink_connection(path + "00000154.BIN")        
    # zigzag_statechange_v, pos_v = get_zigzag_statechange_and_pos(log_file)
    # if check_zigzag_statechage(zigzag_statechange_v) == False:
    #     # state change error
    #     print(int(False))
    #     sys.exit(0)
    # statechange_time_v = get_zigzag_statechange_time(zigzag_statechange_v)
    # # print(statechange_time_v)
    # split_pos_v = split_pos_v_by_statechange_time(pos_v, statechange_time_v)
    # # for split_pos in split_pos_v:
    # #     print(split_pos)
    # distance_v = calculate_distance(split_pos_v)
    # print(distance_v)
    # print(int(check_distance(distance_v, base_manual_ave_dis, base_auto_ave_dis)))

    log_file_name = sys.argv[1]
    log_file = mavutil.mavlink_connection(log_file_name)        
    zigzag_statechange_v, pos_v = get_zigzag_statechange_and_pos(log_file)
    if check_zigzag_statechage(zigzag_statechange_v) == False:
        # state change error
        print(int(False))
        sys.exit(0)
    statechange_time_v = get_zigzag_statechange_time(zigzag_statechange_v)
    # print(statechange_time_v)
    split_pos_v = split_pos_v_by_statechange_time(pos_v, statechange_time_v)
    # for split_pos in split_pos_v:
    #     print(split_pos)
    distance_v = calculate_distance(split_pos_v)
    print(int(check_distance(distance_v, base_manual_ave_dis, base_auto_ave_dis)))
