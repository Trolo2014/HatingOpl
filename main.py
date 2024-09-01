import requests
import time
import json

WEBHOOK_URL = "https://discord.com/api/webhooks/1116120565955182722/jCrzUqFdd29XD_xMzqIFfgHImP_coEi4TzsQEgCjFXx2F5ReW-xiBR2Q5sbOPf9EPZUm"
USER_IDS = [520944, 43247021, 137621, 1135910299, 295337577, 2350183594]  # Replace with actual user IDs
PLACE_ID = "1234567890"  # Replace with actual place ID
PREVIOUS_STATE = {}

# Function to get presence data
def get_presence(user_ids):
    url = "https://presence.roblox.com/v1/presence/users"
    headers = {"Content-Type": "application/json"}
    data = {"userIds": user_ids}
    
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json().get('userPresences', [])
    except requests.RequestException as e:
        print(f"An error occurred while fetching presence data: {e}")
        return []

# Function to get game servers
def get_servers(place_id, cursor=None, retries=10):
    url = f"https://games.roblox.com/v1/games/{place_id}/servers/Public?limit=100"
    if cursor:
        url += f"&cursor={cursor}"
    for attempt in range(retries):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(2.5)
    return None

# Function to search for a player in a specific game
def search_player_in_game(user_id, place_id):
    cursor = None
    while True:
        servers = get_servers(place_id, cursor)
        if not servers:
            print("Failed to retrieve servers.")
            return None
        
        cursor = servers.get("nextPageCursor")

        for server in servers.get("data", []):
            if user_id in server.get("playing", []):
                return server.get("id")

        if not cursor:
            break

    return None

# Function to send a message using webhook
def send_webhook_message(content):
    data = {
        "content": content
    }
    try:
        response = requests.post(WEBHOOK_URL, json=data)
        response.raise_for_status()
        print("Message sent successfully.")
    except requests.RequestException as e:
        print(f"Failed to send message: {e}")

# Main function to monitor users
def monitor_users():
    while True:
        presence_data = get_presence(USER_IDS)
        
        update_content = "User Status Updates:\n"
        
        for presence in presence_data:
            user_id = presence.get('userId')
            username = presence.get('userName')
            presence_type = presence.get('userPresenceType')

            if presence_type == 2:  # User is in-game
                if PREVIOUS_STATE.get(user_id) != 'In-Game':
                    update_content += f"**{username}** is now in a game. Checking...\n"
                    job_id = search_player_in_game(user_id, PLACE_ID)
                    if job_id:
                        update_content += (
                            f"**{username}** found in game with PlaceID: {PLACE_ID}\n"
                            f"DeepLink: roblox://experiences/start?placeId={PLACE_ID}&gameInstanceId={job_id}\n"
                        )
                    else:
                        update_content += f"**{username}** not found in game.\n"

                PREVIOUS_STATE[user_id] = "In-Game" if presence_type == 2 else "Not In-Game"
            else:
                PREVIOUS_STATE[user_id] = "Not In-Game"

        send_webhook_message(update_content)
        time.sleep(30)  # Check every 30 seconds

# Run the monitoring function
if __name__ == "__main__":
    monitor_users()
