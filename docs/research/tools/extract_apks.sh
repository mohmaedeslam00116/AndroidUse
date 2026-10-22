#!/bin/bash
set -u
P=/mnt/d/tmp/opencode/parts
OUT=/mnt/d/tmp/opencode/apks
mkdir -p "$OUT"
for part in system system_ext product; do
  mkdir -p "$OUT/$part"
  for d in app priv-app framework; do
    echo "--- $part /$d ---"
    debugfs -R "rdump /$d $OUT/$part" "$P/$part.img" 2>&1 | grep -v "^debugfs" | head -5
  done
done
echo "=== apk count ==="
find "$OUT" -name "*.apk" | wc -l
find "$OUT" -name "*.apk" | head -40
