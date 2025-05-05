import json
import boto3
from urllib.parse import parse_qs

def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('login')

    try:
        # Extract and parse the body from the event
        body = event.get('body', '')
        parsed_body = parse_qs(body)

        # Extract individual fields from the parsed body
        email = parsed_body.get('email', [None])[0]
        username = parsed_body.get('username', [None])[0]
        password = parsed_body.get('password', [None])[0]

        # Validate required fields
        if not email or not username or not password:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "POST"
                },
                "body": json.dumps({"error": "Missing required fields"})
            }

        # Check if email already exists in DynamoDB
        response = table.get_item(Key={'email': email})
        if 'Item' in response:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "POST"
                },
                "body": json.dumps({"error": "The email already exists"})
            }

        # Store user in DynamoDB
        table.put_item(Item={
            'email': email,
            'user_name': username,
            'password': password  # Storing plain text password (not recommended for production)
        })

        # Return a success response with a redirect signal
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST"
            },
            "body": json.dumps({"message": "Registration successful", "redirect_to": "/"})
        }
    
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST"
            },
            "body": json.dumps({"error": str(e)})
        }
