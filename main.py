import os
import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup

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

def download_file(file_url, save_path):
    response = requests.get(file_url, stream=True)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            for data in response.iter_content(1024):
                file.write(data)
        print(f"Downloaded the file to: {save_path}")
    else:
        print(f"Failed to download file. Status code: {response.status_code}")

def download_latest_files(category):
    files = get_files(category)
    if not files:
        print(f"No files found for category: {category}")
        return

    # Separate files into dynamic and static
    date_files = [f for f in files if re.search(r'\d{4}_\d{2}_\d{2}', f)]
    static_files = [f for f in files if not re.search(r'\d{4}_\d{2}_\d{2}', f)]

    # Group dynamic files by their prefix
    grouped_files = {}
    for file in date_files:
        prefix = re.match(r'.*?(?=_\d{4}_\d{2}_\d{2})', file).group(0)
        if prefix not in grouped_files:
            grouped_files[prefix] = []
        grouped_files[prefix].append(file)

    # Download the latest dynamic files
    for prefix, group in grouped_files.items():
        latest_file = max(group, key=lambda x: datetime.strptime(re.search(r'\d{4}_\d{2}_\d{2}', x).group(0), '%Y_%m_%d'))
        file_url = base_url + category + '/' + latest_file
        save_path = os.path.join(category, latest_file)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        download_file(file_url, save_path)

    # Download static files
    for static_file in static_files:
        file_url = base_url + category + '/' + static_file
        save_path = os.path.join(category, static_file)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        download_file(file_url, save_path)

    # Special case for kiterunner to download additional files from raw_base_url
    if category == 'kiterunner':
        special_files = [
            'swagger-files.tar',
            'routes-small.json.tar.gz',
            'routes-large.json.tar.gz'
        ]
        for special_file in special_files:
            special_file_url = raw_base_url + category + '/' + special_file
            special_save_path = os.path.join(category, special_file)
            download_file(special_file_url, special_save_path)

categories = ["data/automated", "data/manual", "data/technologies", "data/kiterunner"]

for category in categories:
    download_latest_files(category)
