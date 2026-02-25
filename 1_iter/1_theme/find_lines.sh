#!/usr/bin/env bash

file_path="$1"
search_pattern="$2"

if [ -z "$file_path" ] || [ -z "$search_pattern" ]; then
  echo "Usage: $0 <file_path> <search_pattern>"
  exit 2
fi

if [ ! -f "$file_path" ]; then
  echo "File not found: $file_path"
  exit 1
fi

grep -in -- "$search_pattern" "$file_path"
grep_exit_code=$?

echo "EXIT_CODE=$grep_exit_code"

exit 0