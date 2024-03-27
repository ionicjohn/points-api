import os
import win32wnet
import win32netcon
import json
import time
from populate_point_tree import get_simplified_tree
from dotenv import load_dotenv
from datetime import datetime
load_dotenv()

def map_drive(network_path, user, password, drive, force=False):
    if os.path.exists(drive):
        print(drive, " Drive in use, trying to unmap...")
        if force:
            try:
                win32wnet.WNetCancelConnection2(drive, 1, 1)
                print(drive, "successfully unmapped...")
            except Exception as e:
                print(drive, "Unmap failed, This might not be a network drive...")
                print("Error:", e)
                return -1
        else:
            print("Non-forcing call. Will not unmap...")
            return -1
    else:
        print(drive, " drive is free...")

    print("Trying to map", network_path, "on to", drive, "...")
    try:
        print(network_path, drive)
        win32wnet.WNetAddConnection2(win32netcon.RESOURCETYPE_DISK, drive, network_path, None, user, password)
        print("Mapping successful")
        return 1
    except Exception as e:
        print("Failed to map network drive:", e)
        return -1

def get_folder_structure(directory):
    file_tree = {}
    for entry in os.listdir(directory):
        path = os.path.join(directory, entry)
        if os.path.isdir(path):
            file_tree[entry] = get_folder_structure(path)
        else:
            file_tree[entry] = None
    return file_tree

def process_directory(dir_path):
    years = {}
    months = {}
    folder_structure = {}
    for root, _, _ in os.walk(dir_path):
        parts = root.replace(dir_path, '').split(os.sep)
        if len(parts) >= 2:
            year = parts[1]
            if len(parts) >= 3:
                month = parts[2]
            else:
                month = None
            if year not in years:
                years[year] = []
            if month and month not in years[year]:
                years[year].append(month)
            if month:
                key = f"{year}/{month}"
                folder_structure.setdefault(key, []).append(root)
    return years, months, folder_structure

def path_to_dict(path):
    org_name = os.path.basename(os.path.dirname(path))
    if org_name.startswith("E") or org_name.startswith("K"):
        d = {'name': org_name, 'type': "directory", 'children': []}
        sur_path = os.path.join(path, "SUR")
        if os.path.exists(sur_path):
            sur_node = path_to_dict(sur_path)
            d['children'].append(sur_node)
        for x in sorted(os.listdir(path)):
            child_path = os.path.join(path, x)
            if os.path.isdir(child_path) and x != "SUR":
                d['children'].append(path_to_dict(child_path))
            elif os.path.isfile(child_path):
                d['children'].append({'name': x, 'type': "file"})
        return d

    d = {'name': os.path.basename(path)}
    if os.path.isdir(path):
        d['type'] = "directory"
        children = []
        dir_entries = sorted(os.listdir(path))
        for x in dir_entries:
            child_path = os.path.join(path, x)
            if os.path.isdir(child_path):
                sur_path = os.path.join(child_path, "SUR")
                if os.path.exists(sur_path):
                    children.append(path_to_dict(sur_path))
                else:
                    children.append(path_to_dict(child_path))
            else:
                children.append({'name': x, 'type': "file"})
        d['children'] = children
    else:
        d['type'] = "file"
    return d

simplified_tree_name = "simplified_tree.json"
full_tree_name = "output.json"
cache_info_name = "output_info.json"

def get_last_generation_date():
    try:
        with open(cache_info_name, "r") as file:
            return json.loads(file.read())["date"]
    except:
        return None
        
def get_last_cached_simplified_tree():
    with open(simplified_tree_name, "r") as file:
        return json.loads(file.read())

def get_last_cached_full_tree():
    with open(full_tree_name, "r") as file:
        return json.loads(file.read())


def populate_file_tree():
    username = os.environ.get("filetree_username")
    password = os.environ.get("filetree_password")
    drive = os.environ.get("filetree_drive")
    network_path = os.environ.get("filetree_networkpath")

    if not all([username, password, drive, network_path]):
        print("One or more environment variables are missing. Please check your .env file.")
        return

    map_drive(network_path, username, password, drive)
    now = datetime.now()
    date_time = now.strftime("%d/%m/%Y")
    sur_directory = None
    for root, dirs, _ in os.walk(drive):
        if "SUR" in dirs:
            sur_directory = os.path.join(root, "SUR")
            break

    if sur_directory is None:
        print("The 'SUR' directory was not found.")
        return

    serialized = path_to_dict(drive)
    with open(full_tree_name, "w") as file:
        file.write(json.dumps(serialized, indent=4))
    with open(cache_info_name, "w") as file:
        file.write(json.dumps({"date": date_time}))

    meow = get_simplified_tree(serialized)
    with open(simplified_tree_name, 'w') as f:
        f.write(json.dumps(meow))
