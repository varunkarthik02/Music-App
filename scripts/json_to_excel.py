import json
import pandas as pd

# Load the JSON data
with open('2025a1_modified.json', 'r') as file:
    data = json.load(file)

# Convert JSON data to a DataFrame
df = pd.DataFrame(data['songs'])

# Save the DataFrame to an Excel file
excel_file = 'songs_modified.xlsx'
df.to_excel(excel_file, index=False)

print(f"Excel file '{excel_file}' has been created.")
