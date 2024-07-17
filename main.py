import os
import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import time

base_url = "https://wordlists-cdn.assetnote.io/"
raw_base_url = "https://wordlists-cdn.assetnote.io/rawdata/"

def get_files(category):
    url = base_url + category + '/'
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Failed to fetch files. Status code: {response.status_code}")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    files = [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith(('.txt', '.tar.gz', '.tar', '.json.tar.gz'))]
    return files

def download_file(file_url, save_path, retries=3):
    for attempt in range(retries):
        try:
            response = requests.get(file_url, stream=True)
            if response.status_code == 200:
                with open(save_path, 'wb') as file:
                    for data in response.iter_content(1024):
                        file.write(data)
                print(f"Downloaded the file to: {save_path}")
                return True
            else:
                print(f"Failed to download file. Status code: {response.status_code}")
        except requests.exceptions.ChunkedEncodingError as e:
            print(f"Connection error: {e}. Retrying {attempt + 1}/{retries}...")
            time.sleep(5)  # wait for a bit before retrying
    return False

def download_latest_files(category):
    files = get_files(category)
    if not files:
        print(f"No files found for category: {category}")
        return False, None

    # Separate files into dynamic and static
    date_files = [f for f in files if re.search(r'\d{4}_\d{2}_\d{2}', f)]
    static_files = [f for f in files if not re.search(r'\d{4}_\d{2}_\d{2}', f)]

    # Group dynamic files by their prefix
    grouped_files = {}
    for file in date_files:
        match = re.match(r'.*?(?=_\d{4}_\d{2}_\d{2})', file)
        if match:
            prefix = match.group(0)
            if prefix not in grouped_files:
                grouped_files[prefix] = []
            grouped_files[prefix].append(file)

    latest_files_already_present = True
    latest_file_date = None

    # Download the latest dynamic files
    for prefix, group in grouped_files.items():
        latest_file = max(group, key=lambda x: datetime.strptime(re.search(r'\d{4}_\d{2}_\d{2}', x).group(0), '%Y_%m_%d'))
        latest_file_date = re.search(r'\d{4}_\d{2}_\d{2}', latest_file).group(0)
        latest_file_path = os.path.join(category, latest_file)
        
        if os.path.exists(latest_file_path):
            print(f"You have the latest asset note wordlist ({latest_file_date}).")
            return True, latest_file_date
        else:
            latest_files_already_present = False
            # Delete old files
            for old_file in group:
                old_file_path = os.path.join(category, old_file)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
            
            # Download the latest file
            file_url = base_url + category + '/' + latest_file
            os.makedirs(os.path.dirname(latest_file_path), exist_ok=True)
            download_file(file_url, latest_file_path)

    # Download static files
    for static_file in static_files:
        static_file_path = os.path.join(category, static_file)
        if not os.path.exists(static_file_path):
            file_url = base_url + category + '/' + static_file
            os.makedirs(os.path.dirname(static_file_path), exist_ok=True)
            download_file(file_url, static_file_path)

    # Special case for kiterunner to download additional files from raw_base_url
    if category == 'data/kiterunner':
        special_files = [
            'swagger-files.tar',
            'routes-small.json.tar.gz',
            'routes-large.json.tar.gz'
        ]
        for special_file in special_files:
            special_file_path = os.path.join(category, special_file)
            if not os.path.exists(special_file_path):
                special_file_url = raw_base_url + 'kiterunner/' + special_file
                os.makedirs(os.path.dirname(special_file_path), exist_ok=True)
                download_file(special_file_url, special_file_path)

    return latest_files_already_present, latest_file_date

categories = ["data/automated", "data/manual", "data/technologies", "data/kiterunner"]

latest_file_date = None
all_latest_files_present = True

# Check and download files for each category
for category in categories:
    latest_files_already_present, date = download_latest_files(category)
    if not latest_files_already_present:
        all_latest_files_present = False
    if date:
        latest_file_date = date

if all_latest_files_present:
    print(f"You have the latest Assetnote wordlist ({latest_file_date}).")
else:
    print(f"Downloaded all the latest files ({latest_file_date}).")
