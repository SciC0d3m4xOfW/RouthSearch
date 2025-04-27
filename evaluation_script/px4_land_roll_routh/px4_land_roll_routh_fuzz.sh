
export WORKSPACE_BASE_DIR=/home/li/UAVFuzzing
export PX4_HOME=/home/li/pgfuzz/px4
export PX4_FUZZ_HOME=$WORKSPACE_BASE_DIR/routh_fuzz/px4
export MODE=land
export ESTIMATE_ABNORMAL_CONFIG=estimated_abnormal_config_${MODE}_roll/${MODE}
first_step_end_flag=1
second_step_end_flag=1

> $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/all_config.json
> $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/first_step_res.json
> $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/second_step_res.json
> $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/res_bounder.json
> $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/config_to_check.json
rm -rf $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/logs/*
rm -rf $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/res/*.result
start_time=$(date +%s)
end_time=$((start_time + 48 * 3600))
echo "----------------start time------------------"
echo $start_time
echo $end_time
echo "--------------------------------------------"

p_start=0.01
p_end=0.5
p_step=0.01
p_adjust_step=0.01
p_to_check=$p_start
update_boundary_flag=0
while (( $(echo "$p_to_check <= $p_end" | bc -l) )); do
    
    update_boundary_flag=0
    i_start=0.01
    i_end=1
    i_step=0.01
    i_adjust_step=0.01
    i_to_check=$i_end
    d_start=0.0000
    d_end=0.0100
    d_step=0.0005
    d_adjust_step=0.0010
    output=1
    
    
    while (( $(echo "$i_to_check >= $i_start" | bc -l) )); do
        current_time=$(date +%s)
        echo "----------------current_time------------------"
        echo $current_time
        echo "----------------------------------------------"
        if [ "$current_time" -ge "$end_time" ]; then
            exit 0
        fi
        
        
        echo "----------------------------------"
        echo $(printf "%.2f" $p_to_check)
        echo $(printf "%.4f" $d_start)
        echo $(printf "%.2f" $i_to_check)
        echo "----------------------------------"
        echo "{\"MC_ROLLRATE_P\": $(printf "%.2f" $p_to_check), \"MC_ROLLRATE_I\": $(printf "%.2f" $i_to_check), \"MC_ROLLRATE_D\": $(printf "%.4f" $d_start)}" > $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/../config.json
        echo "::Start PX4"
        echo "::Execute Fuzz"
    
        CONTAINER_ID=$(sudo docker run --cpus=6 -d --rm -e SPEED_UP=5 -v $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/../config.json:/px4/pids/config.json -v $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/logs:/px4/PX4-Autopilot/build/px4_sitl_default/rootfs/log -v `pwd`/default.json:/px4/default.json px4_land_mode)
    
        sudo docker wait $CONTAINER_ID

        echo "{\"MC_ROLLRATE_P\": $(printf "%.2f" $p_to_check), \"MC_ROLLRATE_I\": $(printf "%.2f" $i_to_check), \"MC_ROLLRATE_D\": $(printf "%.4f" $d_start)}" >> $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/all_config.json

        PID_PARAMETERS="MC_ROLLRATE_P,MC_ROLLRATE_I,MC_ROLLRATE_D"
        CONTAINER_ID=$(docker run --cpus=6  -d --rm -e PID_PARMS=${PID_PARAMETERS} -v $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/logs:/px4/logs  -v $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/res:/px4/results px4_land_oracle)
        sudo docker wait $CONTAINER_ID

        
        outputfile=$(ls "$PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/res/"*.result 2>/dev/null)

        if [ $? -ne 0 ]; then
            output_left=0
        else
            output_left=$(awk '{print $NF}' "$outputfile")
            output_left=$(echo "$output_left" | bc -l)
        fi

        
        rm -rf $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/logs/*
        rm -rf $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/res/*.result

        echo "second test res: ${output_left}"

        if [ "$output_left" -eq 0 ]; then
            echo "{\"MC_ROLLRATE_P\": $(printf "%.2f" $p_to_check), \"MC_ROLLRATE_I\": $(printf "%.2f" $i_to_check), \"MC_ROLLRATE_D\": $(printf "%.4f" $d_start)}" >> $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/first_step_res.json
            i_to_check=$(echo "scale=2; ($(printf "%.2f" $i_to_check) - $(printf "%.2f" $i_adjust_step))" | bc -l)
        else
            break
        fi
    done
    
    echo "----------------------------------"
    echo "end step 1"
    echo "----------------------------------"

    if (( $(echo "$i_to_check < $i_end" | bc -l) )); then
        i_to_check=$(echo "scale=2; ($(printf "%.2f" $i_to_check) + $(printf "%.2f" $i_adjust_step))" | bc -l)
    fi
    d_to_check=$d_start
    have_ajusted_i_down=0
    have_ajusted_i_up=0
    while (( $(echo "$d_to_check <= $d_end" | bc -l) )); do
        current_time=$(date +%s)
        echo "----------------current_time------------------"
        echo $current_time
        echo "----------------------------------------------"
        if [ "$current_time" -ge "$end_time" ]; then
            exit 0
        fi
        echo "----------------------------------"
        echo $(printf "%.2f" $p_to_check)
        echo $(printf "%.4f" $d_to_check)
        echo $(printf "%.2f" $i_to_check)
        echo "----------------------------------"

        echo "{\"MC_ROLLRATE_P\": $(printf "%.2f" $p_to_check), \"MC_ROLLRATE_I\": $(printf "%.2f" $i_to_check), \"MC_ROLLRATE_D\": $(printf "%.4f" $d_to_check)}" > $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/../config.json
        echo "{\"MC_ROLLRATE_P\": $(printf "%.2f" $p_to_check), \"MC_ROLLRATE_I\": $(printf "%.2f" $i_to_check), \"MC_ROLLRATE_D\": $(printf "%.4f" $d_to_check)}" >> $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/all_config.json

        echo "::Start PX4"
        echo "::Execute Fuzz"
        CONTAINER_ID=$(sudo docker run --cpus=6 -d --rm -e SPEED_UP=5 -v $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/../config.json:/px4/pids/config.json -v $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/logs:/px4/PX4-Autopilot/build/px4_sitl_default/rootfs/log -v `pwd`/default.json:/px4/default.json px4_land_mode)
        sudo docker wait $CONTAINER_ID

        
        PID_PARAMETERS="MC_ROLLRATE_P,MC_ROLLRATE_I,MC_ROLLRATE_D"
        CONTAINER_ID=$(docker run --cpus=6  -d --rm -e PID_PARMS=${PID_PARAMETERS} -v $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/logs:/px4/logs  -v $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/res:/px4/results px4_land_oracle)
        sudo docker wait $CONTAINER_ID

        
        outputfile=$(ls "$PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/res/"*.result 2>/dev/null)

        if [ $? -ne 0 ]; then
            output=0
        else
            output=$(awk '{print $NF}' "$outputfile")
            output=$(echo "$output" | bc -l)
        fi

        
        rm -rf $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/logs/*
        rm -rf $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/res/*.result

        echo "first test res: ${output}"
        
        if [ "$output" -eq 0 ]; then
            
            echo "{\"MC_ROLLRATE_P\": $(printf "%.2f" $p_to_check), \"MC_ROLLRATE_I\": $(printf "%.2f" $i_to_check), \"MC_ROLLRATE_D\": $(printf "%.4f" $d_to_check)}" >> $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/first_step_res.json
            
            if [ "$have_ajusted_i_up" -eq 1 ]; then
                
                update_boundary_flag=1
                python3 $PX4_FUZZ_HOME/generate_abnormal_config.py MC_ROLLRATE_P $p_to_check $p_to_check MC_ROLLRATE_I $i_to_check $i_end MC_ROLLRATE_D $d_to_check $d_to_check $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/res_bounder.json
                
                have_ajusted_i_up=0
                have_ajusted_i_down=0
                
                d_to_check=$(echo "scale=3; ($(printf "%.4f" $d_to_check) + $(printf "%.4f" $d_adjust_step))" | bc -l)
            
            else
                
                if (( $(echo "$i_to_check <= $i_start" | bc -l) )); then
                    
                    update_boundary_flag=1
                    python3 $PX4_FUZZ_HOME/generate_abnormal_config.py MC_ROLLRATE_P $p_to_check $p_to_check MC_ROLLRATE_I $i_to_check $i_end MC_ROLLRATE_D $d_to_check $d_to_check $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/res_bounder.json
                    
                    have_ajusted_i_up=0
                    have_ajusted_i_down=0
                    
                    d_to_check=$(echo "scale=3; ($(printf "%.4f" $d_to_check) + $(printf "%.4f" $d_adjust_step))" | bc -l)   
                    continue
                fi
                
                have_ajusted_i_down=1
                
                i_to_check=$(echo "scale=2; ($(printf "%.2f" $i_to_check) - $(printf "%.2f" $i_adjust_step))" | bc -l)
            fi
        
        else
            
            if [ "$have_ajusted_i_down" -eq 1 ]; then
                
                i_to_check=$(echo "scale=2; ($(printf "%.2f" $i_to_check) + $(printf "%.2f" $i_adjust_step))" | bc -l)
                
                update_boundary_flag=1
                python3 $PX4_FUZZ_HOME/generate_abnormal_config.py MC_ROLLRATE_P $p_to_check $p_to_check MC_ROLLRATE_I $i_to_check $i_end MC_ROLLRATE_D $d_to_check $d_to_check $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/res_bounder.json
                
                have_ajusted_i_up=0
                have_ajusted_i_down=0
                
                d_to_check=$(echo "scale=3; ($(printf "%.4f" $d_to_check) + $(printf "%.4f" $d_adjust_step))" | bc -l)
            
            else
                
                if (( $(echo "$i_to_check >= $i_end" | bc -l) )); then
                    
                    have_ajusted_i_up=0
                    have_ajusted_i_down=0
                    
                    d_to_check=$(echo "scale=3; ($(printf "%.4f" $d_to_check) + $(printf "%.4f" $d_adjust_step))" | bc -l)   
                    continue
                fi
                
                have_ajusted_i_up=1
                
                i_to_check=$(echo "scale=2; ($(printf "%.2f" $i_to_check) + $(printf "%.2f" $i_adjust_step))" | bc -l)
            fi
        fi
    done
    
    
    
    

    
    if [ "$update_boundary_flag" -eq 0 ]; then
        break
    fi
    
    p_to_check=$(echo "scale=1; ($(printf "%.2f" $p_to_check) + $(printf "%.2f" $p_adjust_step))" | bc -l)
done

diff <(sed -e '$a\' $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/res_bounder.json) <(sed -e '$a\' $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/first_step_res.json) | grep "< *" | awk -F "< " '{print $2}' > $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/config_to_check.json

grep -v '^$' $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/config_to_check.json | while IFS= read -r line; do
    current_time=$(date +%s)
    echo "----------------current_time------------------"
    echo $current_time
    echo "----------------------------------------------"
    if [ "$current_time" -ge "$end_time" ]; then
         exit 0
    fi
    echo "----------------------------------"
    echo "$line"
    echo "----------------------------------"
    echo "$line" > $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/../config.json
    echo "$line" >> $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/all_config.json

    echo "::Start Ardupilot"
    echo "::Execute Fuzz"
    CONTAINER_ID=$(sudo docker run --cpus=6 -d --rm -e SPEED_UP=5 -v $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/../config.json:/px4/pids/config.json -v $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/logs:/px4/PX4-Autopilot/build/px4_sitl_default/rootfs/log -v `pwd`/default.json:/px4/default.json px4_land_mode)
    sudo docker wait $CONTAINER_ID

    
    PID_PARAMETERS="MC_ROLLRATE_P,MC_ROLLRATE_I,MC_ROLLRATE_D"
    CONTAINER_ID=$(docker run --cpus=6  -d --rm -e PID_PARMS=${PID_PARAMETERS} -v $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/logs:/px4/logs  -v $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/res:/px4/results px4_land_oracle)
    sudo docker wait $CONTAINER_ID

    
    outputfile=$(ls "$PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/res/"*.result 2>/dev/null)

    if [ $? -ne 0 ]; then
        output=0
    else
        output=$(awk '{print $NF}' "$outputfile")
        output=$(echo "$output" | bc -l)
    fi

    
    rm -rf $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/logs/*
    rm -rf $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/res/*.result

    echo "first test res: ${output}"
    if [ "$output" -eq 0 ]; then
        echo "$line" >> $PX4_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/second_step_res.json
    fi
done
