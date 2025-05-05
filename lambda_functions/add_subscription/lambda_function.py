import json
import boto3

def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('subscriptions')  # Replace with your table name
    
    try:
        # Parse request body
        body = json.loads(event['body'])
        email = body['email']
        title = body['title']
        album = body['album']
        artist = body['artist']
        year = body['year']
        
        # Construct attribute name and value
        song_uid = f"{title} - {album}"
        artist_year = f"{artist} - {year}"
        
        # Update DynamoDB item
        response = table.update_item(
            Key={'email': email},
            UpdateExpression="SET #song_uid = :value",
            ExpressionAttributeNames={"#song_uid": song_uid},
            ExpressionAttributeValues={":value": artist_year}
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({'message': 'Subscription added successfully!'})
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
