import json
import boto3

def lambda_handler(event, context):
    print("Event received:", event)
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('subscriptions')  # Replace with your table name

    try:
        # Extract data from API Gateway request
        body = json.loads(event['body'])
        email = body['email']
        song_uid = body['song_uid']
        
        # Use Expression Attribute Names to handle special characters in song_uid
        response = table.update_item(
            Key={'email': email},
            UpdateExpression="REMOVE #song_uid",
            ExpressionAttributeNames={
                "#song_uid": song_uid  # Alias for the song UID attribute
            }
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({'message': 'Subscription removed successfully!'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({'error': str(e)})
        }
