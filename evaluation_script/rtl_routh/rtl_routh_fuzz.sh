
export WORKSPACE_BASE_DIR=/home/li/UAVFuzzing
export DEFAULT_PARAM_PATH=$WORKSPACE_BASE_DIR/ardupilot_default_data
export ARDUPILOT_HOME=/home/li/pgfuzz/ardupilot
export ARDUPILOT_FUZZ_HOME=$WORKSPACE_BASE_DIR/routh_fuzz/ardupilot
export MODE=rtl
export ESTIMATE_ABNORMAL_CONFIG=estimated_abnormal_config_${MODE}/${MODE}
DOCKER_CPUSET=0
first_step_end_flag=1

> $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/all_config.json
> $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/first_step_res.json
> $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/second_step_res.json
> $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/res_bounder.json
> $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/config_to_check.json
rm -rf $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/logs/*.BIN
rm -rf $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/logs/LASTLOG.TXT
rm -rf $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/res/*.result
start_time=$(date +%s)
end_time=$((start_time + 48 * 3600))
echo "----------------start time------------------"
echo $start_time
echo $end_time
echo "--------------------------------------------"

p_start=0.1
p_end=6.0
p_step=0.1
p_adjust_step=0.1
p_to_check=$p_start
update_boundary_flag=0
while (( $(echo "$p_to_check <= $p_end" | bc -l) )); do
    update_boundary_flag=0
    
    i_start=0.02
    i_end=1
    i_step=0.01
    i_adjust_step=0.01
    i_to_check=$i_end
    d_start=0.000
    d_end=1.0
    d_step=0.001
    d_adjust_step=0.01
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
        echo $(printf "%.1f" $p_to_check)
        echo $(printf "%.3f" $d_start)
        echo $(printf "%.3f" $i_to_check)
        echo "----------------------------------"
        
        echo "{\"PSC_VELXY_P\": $(printf "%.1f" $p_to_check), \"PSC_VELXY_I\": $(printf "%.2f" $i_to_check), \"PSC_VELXY_D\": $(printf "%.3f" $d_start)}" > $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/../config.json
        echo "{\"PSC_VELXY_P\": $(printf "%.1f" $p_to_check), \"PSC_VELXY_I\": $(printf "%.2f" $i_to_check), \"PSC_VELXY_D\": $(printf "%.3f" $d_start)}" >> $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/all_config.json

        echo "::Start Ardupilot"
        echo "::Execute Fuzz"
        CONTAINER_ID=$(sudo docker run --cpuset-cpus ${DOCKER_CPUSET} -d --rm -v $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/..:/ardu-sim/pids -v $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/logs:/ardu-sim/logs rtl_mode:latest)
        sudo docker wait $CONTAINER_ID
        PID_PARAMETERS="PSC_VELXY_P,PSC_VELXY_I,PSC_VELXY_D"
        CONTAINER_ID=$(docker run --cpuset-cpus ${DOCKER_CPUSET}  -d --rm -e PID_PARMS=${PID_PARAMETERS} -v $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/logs:/ardu-sim/logs  -v $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/res:/ardu-sim/results rtl_oracle:latest)
        sudo docker wait $CONTAINER_ID
        
        outputfile=`ls $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/res/*.result`
        output_left=$(awk '{print $NF}' "$outputfile")
        output_left=$(echo "$output_left" | bc -l)
        
        echo "first test res: ${output_left}"
        rm -rf $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/logs/*.BIN
        rm -rf $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/logs/LASTLOG.TXT
        rm -rf $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/res/*.result

        if [ "$output_left" -eq 0 ]; then
            echo "{\"PSC_VELXY_P\": $(printf "%.1f" $p_to_check), \"PSC_VELXY_I\": $(printf "%.2f" $i_to_check), \"PSC_VELXY_D\": $(printf "%.3f" $d_start)}" >> $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/first_step_res.json
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
        echo $(printf "%.1f" $p_to_check)
        echo $(printf "%.3f" $d_to_check)
        echo $(printf "%.3f" $i_to_check)
        echo "----------------------------------"

        echo "{\"PSC_VELXY_P\": $(printf "%.1f" $p_to_check), \"PSC_VELXY_I\": $(printf "%.2f" $i_to_check), \"PSC_VELXY_D\": $(printf "%.3f" $d_to_check)}" > $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/../config.json
        echo "{\"PSC_VELXY_P\": $(printf "%.1f" $p_to_check), \"PSC_VELXY_I\": $(printf "%.2f" $i_to_check), \"PSC_VELXY_D\": $(printf "%.3f" $d_to_check)}" >> $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/all_config.json

        echo "::Start Ardupilot"
        echo "::Execute Fuzz"
        CONTAINER_ID=$(sudo docker run --cpuset-cpus ${DOCKER_CPUSET} -d --rm -v $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/..:/ardu-sim/pids -v $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/logs:/ardu-sim/logs rtl_mode:latest)
        sudo docker wait $CONTAINER_ID

        PID_PARAMETERS="PSC_VELXY_P,PSC_VELXY_I,PSC_VELXY_D"
        CONTAINER_ID=$(sudo docker run --cpuset-cpus ${DOCKER_CPUSET}  -d --rm -e PID_PARMS=${PID_PARAMETERS} -v $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/logs:/ardu-sim/logs  -v $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/res:/ardu-sim/results rtl_oracle:latest)
        sudo docker wait $CONTAINER_ID

        outputfile=`ls $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/res/*.result`
        output=$(awk '{print $NF}' "$outputfile")
        output=$(echo "$output" | bc -l)

        echo "first test res: ${output}"
        rm -rf $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/logs/*.BIN
        rm -rf $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/logs/LASTLOG.TXT
        rm -rf $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/res/*.result

        if [ "$output" -eq 0 ]; then
            
            echo "{\"PSC_VELXY_P\": $(printf "%.1f" $p_to_check), \"PSC_VELXY_I\": $(printf "%.2f" $i_to_check), \"PSC_VELXY_D\": $(printf "%.3f" $d_to_check)}" >> $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/first_step_res.json
            
            if [ "$have_ajusted_i_up" -eq 1 ]; then
                
                update_boundary_flag=1
                python3 $ARDUPILOT_FUZZ_HOME/generate_abnormal_config.py PSC_VELXY_P $p_to_check $p_to_check PSC_VELXY_I $i_to_check $i_end PSC_VELXY_D $d_to_check $d_to_check $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/res_bounder.json
                
                have_ajusted_i_up=0
                have_ajusted_i_down=0
                
                d_to_check=$(echo "scale=3; ($(printf "%.3f" $d_to_check) + $(printf "%.3f" $d_adjust_step))" | bc -l)
            
            else
                
                if (( $(echo "$i_to_check <= $i_start" | bc -l) )); then
                    
                    update_boundary_flag=1
                    python3 $ARDUPILOT_FUZZ_HOME/generate_abnormal_config.py PSC_VELXY_P $p_to_check $p_to_check PSC_VELXY_I $i_to_check $i_end PSC_VELXY_D $d_to_check $d_to_check $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/res_bounder.json
                    
                    have_ajusted_i_up=0
                    have_ajusted_i_down=0
                    
                    d_to_check=$(echo "scale=3; ($(printf "%.3f" $d_to_check) + $(printf "%.3f" $d_adjust_step))" | bc -l)
                    continue
                fi
                
                have_ajusted_i_down=1
                
                i_to_check=$(echo "scale=2; ($(printf "%.2f" $i_to_check) - $(printf "%.2f" $i_adjust_step))" | bc -l)
            fi
        
        else
            
            if [ "$have_ajusted_i_down" -eq 1 ]; then
                
                i_to_check=$(echo "scale=2; ($(printf "%.2f" $i_to_check) + $(printf "%.2f" $i_adjust_step))" | bc -l)
                
                update_boundary_flag=1
                python3 $ARDUPILOT_FUZZ_HOME/generate_abnormal_config.py PSC_VELXY_P $p_to_check $p_to_check PSC_VELXY_I $i_to_check $i_end PSC_VELXY_D $d_to_check $d_to_check $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/res_bounder.json
                
                have_ajusted_i_up=0
                have_ajusted_i_down=0
                
                d_to_check=$(echo "scale=3; ($(printf "%.3f" $d_to_check) + $(printf "%.3f" $d_adjust_step))" | bc -l)
            
            else
                
                if (( $(echo "$i_to_check >= $i_end" | bc -l) )); then
                    
                    have_ajusted_i_up=0
                    have_ajusted_i_down=0
                    
                    d_to_check=$(echo "scale=3; ($(printf "%.3f" $d_to_check) + $(printf "%.3f" $d_adjust_step))" | bc -l)
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
    p_to_check=$(echo "scale=1; ($(printf "%.1f" $p_to_check) + $(printf "%.1f" $p_adjust_step))" | bc -l)
done


diff <(sed -e '$a\' $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/res_bounder.json) <(sed -e '$a\' $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/first_step_res.json) | grep "< *" | awk -F "< " '{print $2}' > $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/config_to_check.json

grep -v '^$' $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/config_to_check.json | while IFS= read -r line; do
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
    echo "$line" > $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/../config.json
    echo "$line" >> $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/all_config.json

    echo "::Start Ardupilot"
    echo "::Execute Fuzz"
    CONTAINER_ID=$(sudo docker run --cpuset-cpus ${DOCKER_CPUSET} -d --rm -v $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/..:/ardu-sim/pids -v $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/logs:/ardu-sim/logs rtl_mode:latest)
    sudo docker wait $CONTAINER_ID

    
    PID_PARAMETERS="PSC_VELXY_P,PSC_VELXY_I,PSC_VELXY_D"
    CONTAINER_ID=$(sudo docker run --cpuset-cpus ${DOCKER_CPUSET}  -d --rm -e PID_PARMS=${PID_PARAMETERS} -v $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/logs:/ardu-sim/logs  -v $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/res:/ardu-sim/results rtl_oracle:latest)
    sudo docker wait $CONTAINER_ID

    
    outputfile=`ls $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/res/*.result`
    output=$(awk '{print $NF}' "$outputfile")
    output=$(echo "$output" | bc -l)

    
    rm -rf $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/logs/*.BIN
    rm -rf $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/logs/LASTLOG.TXT
    rm -rf $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/res/*.result

    echo "first test res: ${output}"
    if [ "$output" -eq 0 ]; then
        echo "$line" >> $ARDUPILOT_FUZZ_HOME/routh_fuzz_data_dir/${ESTIMATE_ABNORMAL_CONFIG}/second_step_res.json
    fi
done
