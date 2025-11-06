#!/usr/bin/env python3
import shutil
import os
import sys

src_dir = 'lucid-work'
dst_dir = '.'

if not os.path.exists(src_dir):
    print(f"Source directory {src_dir} does not exist")
    sys.exit(1)

# Move all files and directories from lucid-work to current directory
for item in os.listdir(src_dir):
    src_path = os.path.join(src_dir, item)
    dst_path = os.path.join(dst_dir, item)
    
    # Skip if already exists in destination (like web/ directory)
    if os.path.exists(dst_path):
        print(f"Skipping {item} (already exists)")
        continue
    
    print(f"Moving {item}...")
    shutil.move(src_path, dst_path)

# Copy .git directory if it exists
git_src = os.path.join(src_dir, '.git')
git_dst = os.path.join(dst_dir, '.git')
if os.path.exists(git_src):
    if os.path.exists(git_dst):
        print("Removing existing .git directory...")
        shutil.rmtree(git_dst)
    print("Copying .git directory...")
    shutil.copytree(git_src, git_dst)

# Remove the now-empty lucid-work directory
if os.path.exists(src_dir):
    print(f"Removing {src_dir} directory...")
    shutil.rmtree(src_dir)

print("Done!")
