import os
import re

def clean_filename(filename):
    # Remove content in parentheses at the end
    cleaned = re.sub(r'\s*\([^)]*\)\s*$', '', filename)
    
    # Extract extension
    name, ext = os.path.splitext(cleaned)
    
    # Remove any remaining dots and spaces at the end of the name
    name = name.rstrip('. ')
    
    # If there's no extension, try to find it in the original filename
    if not ext and '.' in filename:
        ext = '.' + filename.split('.')[-1]
    
    return f"{name}{ext}"

def rename_files(root_dir):
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.startswith('.'):  # Skip hidden files
                continue
            
            old_path = os.path.join(dirpath, filename)
            new_filename = clean_filename(filename)
            new_path = os.path.join(dirpath, new_filename)
            
            if old_path != new_path:
                os.rename(old_path, new_path)
                print(f"Renamed: {old_path} -> {new_path}")

# Usage
root_directory = "/home/chris/work/rcog/jobs/job_documents"
rename_files(root_directory)
