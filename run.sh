#!/usr/bin/env bash

set -euo pipefail

python main.py \
    /mnt/d/Projects/GenshinData/OSRELWin4.4.0_R20559831_S20338540_D20555221 \
    --output_dir "exp/v1" \
    --remove_quest_cycles "true" \
    --lang "CHS" \
    --traveller_sex "female" \
    --traveller_name "旅行者" \
    --mate_name "空" \
    --wanderer_name "流浪者" \
    --narrator_name "\`旁白\`" \
    --unknown_name "\`未知\`" \
    --unknown_text "\`未知\`" \
    --replace_newline "true" \
    --remove_broken_trace "false" \
    --remove_absent_text "true" \
    ;

