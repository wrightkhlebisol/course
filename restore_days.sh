#!/bin/bash

# Script to restore missing day directories from commit 5214b0fb

echo "Restoring missing day directories..."

# Get all day directories from the commit
git show 5214b0fb --name-only | grep -E "^day[0-9]+/" | cut -d'/' -f1 | sort -u | sort -V > all_days.txt

echo "Found day directories:"
cat all_days.txt

# Restore each directory
while read day; do
    echo "Restoring $day..."
    git checkout 5214b0fb -- "$day"
done < all_days.txt

echo "Restoration complete!"
echo "Current day directories:"
ls -la | grep "^d" | grep "day" | sort -V
