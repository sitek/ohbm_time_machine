#!/usr/bin/env python

### Libraries
import requests  # For the downloading
import pandas as pd
from tqdm import tqdm  # This is for showing a progress bar
import subprocess
import os

### Load the Excel file
file_path = '../info_sheets/2024/forUpload/2024_Oral Sessions_ForUpload REST.xlsx'
df = pd.read_excel(file_path)

### Download videos
def download_video(url, filename):
    # Stream the video content
    with requests.get(url, stream=True) as r:
        # Raise an error for bad responses
        r.raise_for_status()
        # Open a local file for writing
        with open(filename, 'wb') as f:
            # Write the streamed chunks to the file
            for chunk in tqdm(r.iter_content(chunk_size=8192),
                              desc=f"Downloading {filename}",
                              unit='KB'):
                f.write(chunk)
    print(f"Downloaded: {filename}")

# Define the upload function
def upload_video_to_youtube(file_path, title, description, keywords="OHBM, OHBM2024, Conference, Organization for Human Brain Mapping, Brain", category="28", privacy_status="public", made_for_kids="false", notifySubscribers="false"):
    print(f"Uploading video: {file_path}")
    print(f"Title: '{title}'")
    print(f"Description: '{description}'")

    cmd = [
        'python', 'upload_video.py',
        '--file', file_path,
        '--title', title,
        '--description', description,
        '--keywords', keywords,
        '--category', category,
        '--privacyStatus', privacy_status,
        '--selfDeclaredMadeForKids', made_for_kids,
        '--notifySubscribers', notifySubscribers
    ]

    subprocess.run(cmd, check=True)

# Loop through each available URL, download, and then upload
for index, row in df.iterrows():
    if pd.notnull(row['Download Link']):
        # Define the filename for the downloaded video
        filename = f"../video_downloads/video_{index}.mp4"
        download_video(row['Download Link'], filename)
        
        # Construct the title as per the new requirement
#        video_title = f"{row['Abstract ID']}: OHBM 2023 Educational Course: {row['First name']} {row['Last name']}"
        video_title = row['Youtube Title']

        # Get the description from the DataFrame
        video_description = row['Youtube Description']
        
        # Escape double quotes in title and description
        video_title = video_title.replace('"', '\\"')
        video_description = video_description.replace('"', '\\"')
        
        # Upload the video to YouTube
        upload_video_to_youtube(filename, video_title, video_description)

        # Optional: Remove the video file after upload if you don't want to keep it
        os.remove(filename)
