import boto3

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')  # Change region if needed

# Create the login table with email as the primary key (on-demand mode)
table = dynamodb.create_table(
    TableName='login',
    KeySchema=[{'AttributeName': 'email', 'KeyType': 'HASH'}],  # Primary Key
    AttributeDefinitions=[{'AttributeName': 'email', 'AttributeType': 'S'}],  # String type
    BillingMode='PAY_PER_REQUEST'
)

print("Table is being created... Please wait.")
table.wait_until_exists()
print("Login table created successfully!")

table = dynamodb.Table('login')

student_id = "s4103992"

# Insert 10 users dynamically
for i in range(10):
    email = f"{student_id}{i}@student.rmit.edu.au"
    user_name = f"NameerAnsari{i}"
    password = f"{i}{(i+1)%10}{(i+2)%10}{(i+3)%10}{(i+4)%10}{(i+5)%10}"  # Generates a 6-digit password
    
    item = {
        "email": email,
        "user_name": user_name,
        "password": password
    }
    
    table.put_item(Item=item)

print("Login table populated successfully with dynamic data!")