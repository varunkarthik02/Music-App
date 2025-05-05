import json

# Load JSON data from file
with open('2025a1.json', 'r') as file:
    data = json.load(file)

# Extract songs
songs = data['songs']

# Add 'UID' as concatenated value of title and album name
for song in songs:
    song['UID'] = f"{song['title']} - {song['album']}"
    # Remove 'primary_key' if it exists
    if 'primary_key' in song:
        del song['primary_key']

# Save the modified JSON data back to a file
with open('2025a1_modified.json', 'w') as file:
    json.dump(data, file, indent=4)

# Display a few modified entries for verification
print(songs[:5])  # Optional: Print first 5 entries to verify changes
