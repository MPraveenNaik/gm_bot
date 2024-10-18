import os
import requests # type: ignore
import random
import time
import re
from dotenv import load_dotenv # type: ignore
import logging

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants
MAX_REPLIES = 20

# Access environment variables
required_env_vars = {
    "AUTH_URL": os.getenv("AUTH_URL"),
    "PROFILE_API_URL": os.getenv("PROFILE_API_URL"),
    "FEED_API_URL": os.getenv("FEED_API_URL"),
    "POST_MESSAGE_URL": os.getenv("POST_MESSAGE_URL"),
    "USERNAME": os.getenv("USERNAME"),
    "PASSWORD": os.getenv("PASSWORD"),
    "CLIENT_ID": os.getenv("CLIENT_ID"),
    "BEARER_TOKEN": os.getenv("BEARER_TOKEN")
}

# Check for missing environment variables
missing_vars = [var_name for var_name, var_value in required_env_vars.items() if not var_value]
if missing_vars:
    logger.error(f"The following environment variables are missing: {', '.join(missing_vars)}")
    raise EnvironmentError("Required environment variables are missing.")

# Assigning the environment variables to local variables after validation
AUTH_URL = required_env_vars["AUTH_URL"]
PROFILE_API_URL = required_env_vars["PROFILE_API_URL"]
FEED_API_URL = required_env_vars["FEED_API_URL"]
POST_MESSAGE_URL = required_env_vars["POST_MESSAGE_URL"]
USERNAME = required_env_vars["USERNAME"]
PASSWORD = required_env_vars["PASSWORD"]
CLIENT_ID = required_env_vars["CLIENT_ID"]
BEARER_TOKEN = required_env_vars["BEARER_TOKEN"]

def get_bearer_token():
    """Generate a bearer token using the Auth0 authentication endpoint."""
    try:
        response = requests.post(
            AUTH_URL,
            headers={"Content-Type": "application/json"},
            json={
            "grant_type": "http://auth0.com/oauth/grant-type/password-realm",
            "realm": "Username-Password-Authentication",
            "username": USERNAME,
            "password": PASSWORD,
            "client_id": CLIENT_ID,
            "scope": "openid profile email offline_access follows.read update:current_user_identities"
        }
        )
        response.raise_for_status()
        token = response.json().get("access_token")
        logger.info("Successfully obtained bearer token.")
        return token
    except requests.RequestException as e:
        logger.error(f"Error obtaining bearer token: {e}")
        return None
def get_bearer_token():
    """Get a bearer token from the environment variable or fetch from the Auth0 authentication endpoint."""
    if BEARER_TOKEN:
        logger.info("Bearer token found in environment. Using the existing token.")
        return BEARER_TOKEN

    logger.info("ACCESS TOKEN DOESN'T EXIST IN ENV, FETCHING FROM OAUTH")

    try:
        # Validate environment variables
        if not AUTH_URL or not USERNAME or not PASSWORD or not CLIENT_ID:
            missing_vars = []
            if not AUTH_URL:
                missing_vars.append("AUTH_URL")
            if not USERNAME:
                missing_vars.append("USERNAME")
            if not PASSWORD:
                missing_vars.append("PASSWORD")
            if not CLIENT_ID:
                missing_vars.append("CLIENT_ID")
            raise Exception(f"Missing required environment variables: {', '.join(missing_vars)}")

        # Request payload for authentication
        payload = {
            "grant_type": "http://auth0.com/oauth/grant-type/password-realm",
            "realm": "Username-Password-Authentication",
            "username": USERNAME,
            "password": PASSWORD,
            "client_id": CLIENT_ID,
            "scope": "openid profile email offline_access follows.read update:current_user_identities"
        }

        # Send POST request to obtain the bearer token
        response = requests.post(
            AUTH_URL,
            headers={"Content-Type": "application/json"},
            json=payload
        )
        response.raise_for_status()  # Raise an error for HTTP error codes

        token = response.json().get("access_token")
        if token:
            logger.info("Successfully obtained bearer token.")
            return token
        else:
            logger.error("No access token found in the response.")
            return None

    except requests.RequestException as e:
        logger.error(f"Error obtaining bearer token: {e}")
        return None

def get_profile(token):
    """Fetch the user profile using the bearer token."""
    try:
        response = requests.get(
            PROFILE_API_URL,
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        profile = response.json()
        logger.info("Successfully retrieved profile.")
        return profile.get("handle")
    except requests.RequestException as e:
        logger.error(f"Error fetching profile: {e}")
        return None

def get_feed(token):
    """Fetch the feed with the specified parameters."""
    try:
        response = requests.get(
            f"{FEED_API_URL}?pagenumber=0&amount_per_page=50&sorting=trending",
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        feed = response.json()
        logger.info("Successfully retrieved feed.")
        return feed
    except requests.RequestException as e:
        logger.error(f"Error fetching feed: {e}")
        return []

def post_message_with_file(token, message_id):
    """Post a message with a random greeting and a file attachment."""
    try:
        # Random greeting
        text_content = random.choice(["GM", "Good Morning", "Have a great day!"])

        # File paths (JPEG and GIF)
        file_paths = [
            "200w.gif",
            "gm1.jpeg"
        ]

        # Randomly select a file path
        selected_file_path = random.choice(file_paths)
        file_name = os.path.basename(selected_file_path)

        # Determine file type (MIME type)
        mime_type = "image/jpeg" if selected_file_path.lower().endswith(".jpeg") else "image/gif"

        # Prepare files parameter for the request
        files = [
            ('Files', (file_name, open(selected_file_path, 'rb'), mime_type))
        ]

        # Form data
        form_data = {
            'TextContent': text_content,
            'ReplyOnMessageId': str(message_id),
            'sendToX': '0',
            'msgOrigin': '0'
        }

        # Send POST request
        response = requests.post(
            POST_MESSAGE_URL,
            headers={'Authorization': f'Bearer {token}'},
            data=form_data,
            files=files
        )

        response.raise_for_status()
        logger.info(f"Successfully replied to message ID {message_id} with file {file_name}.")
    except requests.RequestException as e:
        logger.error(f"Error posting message with file: {e}")
    except FileNotFoundError:
        logger.error(f"The file {selected_file_path} was not found.")
    finally:
        # Ensure the file is closed after being opened
        if 'files' in locals():
            for _, file_info in files:
                file_info[1].close()

def main():
    # Step 1: Get a bearer token
    token = get_bearer_token()
    if not token:
        logger.error("Failed to obtain a bearer token. Exiting.")
        return

    # Step 2: Get the user's handle
    user_handle = get_profile(token)
    if not user_handle:
        logger.error("Failed to get the user's handle. Exiting.")
        return

    # Step 3: Fetch the feed
    feed = get_feed(token)
    if not feed:
        logger.error("Failed to retrieve the feed. Exiting.")
        return

    # Step 4: Find posts mentioning 'good morning', 'gm', or 'g m'
    reply_count = 0
    pattern = re.compile(r'\b(?:good morning|gm|g m)\b', re.IGNORECASE)
    for post in feed:
        message_id = post.get("id")
        writer_handle = post.get("writerHandle")
        text_content = post.get("textContent")

        # Check conditions for replying
        if writer_handle.lower() != user_handle.lower() and pattern.search(text_content):
            # Generate a random delay (2 to 5 minutes)
            delay_minutes = random.randint(2, 5)
            logger.info(f"Waiting for {delay_minutes} minutes before replying.")
            time.sleep(delay_minutes * 60)
       
            post_message_with_file(token, message_id)
            reply_count += 1

    logger.info(f"Number of replies made: {reply_count}")

if __name__ == "__main__":
    main()
