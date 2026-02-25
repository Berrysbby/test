#!/usr/bin/env bash

workdir="workdir"
current_user="${USER}"
current_date="${DATE:-$(date +%F)}"
user_data_file="user_data.txt"

mkdir -p "$workdir" && {
  > "$workdir/app.log"
  > "$workdir/app.tmp"
  > "$workdir/readme.txt"
  echo "$current_user $current_date" > "$user_data_file"
}