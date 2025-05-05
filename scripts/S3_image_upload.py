import boto3
import requests
import os
import json

# AWS S3 Configuration
BUCKET_NAME = 'a1-music-assignment'  # Replace with your bucket name

def download_image(url, file_name):
    """Download an image from a given URL."""
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(file_name, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        print(f"Downloaded: {file_name}")
    else:
        print(f"Failed to download: {url}")

def upload_to_s3(file_name, bucket_name, object_key):
    """Upload a file to S3 without specifying ACLs."""
    s3_client = boto3.client('s3')
    try:
        s3_client.upload_file(file_name, bucket_name, object_key)
        print(f"Uploaded: {file_name} as {object_key} to bucket {bucket_name}")
    except Exception as e:
        print(f"Failed to upload {file_name}: {e}")

def process_images(json_file_path):
    """Process images from JSON data."""
    # Load JSON data
    with open(json_file_path, 'r') as json_file:
        data = json.load(json_file)

    # Iterate through songs and process images
    for song in data['songs']:
        title = song['title'].replace(' ', '_').replace('/', '_')  # Sanitize title
        album = song['album'].replace(' ', '_').replace('/', '_').replace('?', '') # Sanitize album
        object_key = f"{title}_-_{album}.jpg"  # Format filename as title-album.jpg

        # Step 1: Download image
        download_image(song['img_url'], object_key)

        # Step 2: Upload image to S3
        upload_to_s3(object_key, BUCKET_NAME, object_key)

        # Cleanup local file after upload
        os.remove(object_key)

# Run the process with your JSON file path
process_images('2025a1.json')


