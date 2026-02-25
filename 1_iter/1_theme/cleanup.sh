#!/usr/bin/env bash

dir_path="$1"
errors_log="cleanup_errors.log"

if [ -z "$dir_path" ]; then
  echo "Usage: $0 <dir_path>"
  exit 2
fi

if [ ! -d "$dir_path" ]; then
  echo "Directory not found: $dir_path"
  exit 1
fi

tmp_files="$(ls -1 "$dir_path" 2>>"$errors_log" | grep -E '\.tmp$')"

if [ -z "$tmp_files" ]; then
  echo "No .tmp files found in: $dir_path"
  exit 0
fi

echo "Found .tmp files:"
printf '%s\n' "$tmp_files"

echo "$tmp_files" | while IFS= read -r file_name; do
  file_path="$dir_path/$file_name"

  rm -v -- "$file_path" 2>>"$errors_log" \
    && : \
    || echo "Failed to remove: $file_path (see $errors_log)"
done