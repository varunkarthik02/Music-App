from flask import Flask, request, render_template, redirect, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import boto3
from boto3.dynamodb.conditions import Key
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')  # Update region if needed
login_table = dynamodb.Table('login')  
music_table = dynamodb.Table('Music')
subscription_table = dynamodb.Table('subscriptions')

# Initialize S3 client
s3_client = boto3.client('s3')

# Replace with your actual S3 bucket name
s3_bucket_name = "a1-music-assignment"

def get_presigned_s3_url(song_uid):
    """Generate presigned URL for artist image"""
    try:
        s3_key = song_uid.replace(" ", "_") + ".jpg"
        return s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': s3_bucket_name, 'Key': s3_key},
            ExpiresIn=3600
        )
    except Exception as e:
        return None

# Ensure SESSION_SECRET_KEY is set in the environment
if not os.getenv('SESSION_SECRET_KEY'):
    raise RuntimeError("The SESSION_SECRET_KEY environment variable is not set. Please set it before running the application.")

app.secret_key = os.getenv('SESSION_SECRET_KEY')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = '/'


# Define User model for Flask-Login
class User(UserMixin):
    def __init__(self, email, username):
        self.id = email  # Use email as unique identifier for the user
        self.username = username


@login_manager.user_loader
def load_user(user_id):
    response = login_table.get_item(Key={'email': user_id})
    user = response.get('Item')
    if user:
        return User(email=user['email'], username=user['user_name'])
    return None


@app.after_request
def prevent_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "-1"
    return response


@app.route('/')
def login_page():
    return render_template('login.html', error=None)


@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']  # Plain text comparison

    try:
        response = login_table.get_item(Key={'email': email})
        user = response.get('Item')

        if user and user['password'] == password:  # Direct string comparison
            flask_user = User(email=user['email'], username=user['user_name'])
            login_user(flask_user)
            return redirect('/main')
        else:
            return render_template('login.html', error="Invalid email or password")
    
    except Exception as e:
        return render_template('login.html', error=f"An error occurred: {e}")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html', error=None)

    elif request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        try:
            # Send registration data to Lambda via API Gateway
            response = requests.post(
                'https://au5d1wejr0.execute-api.us-east-1.amazonaws.com/prod/register',
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                data=f"email={email}&username={username}&password={password}"
            )

            lambda_response = response.json()

            if response.status_code == 200:
                # Redirect based on Lambda's response
                return redirect(lambda_response.get("redirect_to", "/"))
            else:
                # Display error message from Lambda's response
                return render_template('register.html', error=lambda_response.get("error", "An unexpected error occurred"))
        
        except Exception as e:
            return render_template('register.html', error=f"An error occurred: {e}")


@app.route('/main', methods=['GET', 'POST'])
@login_required  # Protect this route with Flask-Login
def main_page():
    query_results = None
    error_message = None

    subscriptions = []
    
    # Fetch user subscriptions
    try:
        response = subscription_table.query(
            KeyConditionExpression=Key('email').eq(current_user.id)
        )
        # print(response)
        subscriptions_raw = [
            {k: v for k, v in item.items() if k != 'email'} 
            for item in response['Items']
        ]

        for song_uid, song_details in subscriptions_raw[0].items():  # Extract keys (song UIDs) and values (details)
            # Split the song_uid into title and album (assuming format "Title - Album")
            title, album = song_uid.split(' - ')
            
            # Generate presigned URL for each song UID
            img_url = get_presigned_s3_url(song_uid)
            
            # Split the song details into artist and year (assuming format "Artist - Year")
            artist, year = song_details.split(' - ')
            
            # Append the subscription with all details and image URL to user_subscriptions
            subscriptions.append({
                'song_uid' : song_uid,
                'title': title.strip(),
                'album': album.strip(),
                'artist': artist.strip(),
                'year': year.strip(),
                'img_url': img_url
            })

    except Exception as e:
        flash("Error loading subscriptions", "error")

    if request.method == 'POST':
        # Get search criteria from form submission
        title = request.form.get('title', '').strip()
        artist = request.form.get('artist', '').strip()
        album = request.form.get('album', '').strip()
        year = request.form.get('year', '').strip()

        try:
            # Priority-based GSI querying
            if title:
                filter_expressions = []
                expression_attribute_values = {}
                expression_attribute_names = {}

                if artist:
                    filter_expressions.append("artist = :artist")
                    expression_attribute_values[":artist"] = artist
                if album:
                    filter_expressions.append("album = :album")
                    expression_attribute_values[":album"] = album
                if year:
                    filter_expressions.append("#yr = :year")
                    expression_attribute_values[":year"] = int(year)
                    expression_attribute_names["#yr"] = "year"

                filter_expression = " AND ".join(filter_expressions) if filter_expressions else None

                query_params = {
                    "IndexName": "title-index",
                    "KeyConditionExpression": boto3.dynamodb.conditions.Key('title').eq(title)
                }
                if filter_expression:
                    query_params["FilterExpression"] = filter_expression
                if expression_attribute_values:
                    query_params["ExpressionAttributeValues"] = expression_attribute_values
                if expression_attribute_names:
                    query_params["ExpressionAttributeNames"] = expression_attribute_names

                response = music_table.query(**query_params)

            elif artist:
                filter_expressions = []
                expression_attribute_values = {}
                expression_attribute_names = {}

                if album:
                    filter_expressions.append("album = :album")
                    expression_attribute_values[":album"] = album
                if year:
                    filter_expressions.append("#yr = :year")
                    expression_attribute_values[":year"] = int(year)
                    expression_attribute_names["#yr"] = "year"

                filter_expression = " AND ".join(filter_expressions) if filter_expressions else None

                query_params = {
                    "IndexName": "artist-index",
                    "KeyConditionExpression": boto3.dynamodb.conditions.Key('artist').eq(artist)
                }
                if filter_expression:
                    query_params["FilterExpression"] = filter_expression
                if expression_attribute_values:
                    query_params["ExpressionAttributeValues"] = expression_attribute_values
                if expression_attribute_names:
                    query_params["ExpressionAttributeNames"] = expression_attribute_names

                response = music_table.query(**query_params)

            elif album:
                filter_expressions = []
                expression_attribute_values = {}
                expression_attribute_names = {}

                if year:
                    filter_expressions.append("#yr = :year")
                    expression_attribute_values[":year"] = int(year)
                    expression_attribute_names["#yr"] = "year"

                filter_expression = " AND ".join(filter_expressions) if filter_expressions else None

                query_params = {
                    "IndexName": "album-index",
                    "KeyConditionExpression": boto3.dynamodb.conditions.Key('album').eq(album)
                }
                if filter_expression:
                    query_params["FilterExpression"] = filter_expression
                if expression_attribute_values:
                    query_params["ExpressionAttributeValues"] = expression_attribute_values
                if expression_attribute_names:
                    query_params["ExpressionAttributeNames"] = expression_attribute_names

                response = music_table.query(**query_params)

            elif year:
                # Use Scan with FilterExpression for year
                scan_params = {
                    'FilterExpression': '#yr = :year',
                    'ExpressionAttributeNames': {'#yr': 'year'},
                    'ExpressionAttributeValues': {':year': int(year)}
                }
                response = music_table.scan(**scan_params)
            else:
                query_results = "Please enter at least one search criterion."
                return render_template('main.html', username=current_user.username, query_results=query_results)

            # Fetch results and add pre-signed image URLs
            query_results = response.get('Items', [])
            for song in query_results:
                try:
                    presigned_url = get_presigned_s3_url(song['UID'])
                    song['img_url'] = presigned_url
                except Exception as e:
                    song['img_url'] = None  # If image is not found or error occurs

        except Exception as e:
            query_results = f"An error occurred while querying: {e}"

        if not query_results:
             query_results = f"Song NOT Found !"


   
    return render_template(
        'main.html',
        username=current_user.username,
        query_results=query_results,
        subscriptions=subscriptions,
        error=None # Rely on flash messages for user feedback
    )


@app.route('/logout')
@login_required  # Protect this route with Flask-Login
def logout():
    logout_user()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)  # Disable debug mode in production!
