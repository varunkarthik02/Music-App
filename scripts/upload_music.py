import boto3
import json

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Music')

# Load modified JSON data
with open('2025a1_modified.json', 'r') as file:
    data = json.load(file)

# Upload each song to DynamoDB using UID as primary key
for song in data['songs']:
    try:
        table.put_item(Item={
            'UID': song['UID'],           # Primary key
            'title': song['title'],
            'artist': song['artist'],
            'album': song['album'],
            'year': int(song['year'])     # Convert year to integer if needed
        })
        print(f"Uploaded: {song['UID']}")
    except Exception as e:
        print(f"Error uploading {song['UID']}: {e}")
