import requests
import time

from keep_alive import keep_alive
keep_alive()

WEBHOOK_URL = "https://discord.com/api/webhooks/1116120565955182722/jCrzUqFdd29XD_xMzqIFfgHImP_coEi4TzsQEgCjFXx2F5ReW-xiBR2Q5sbOPf9EPZUm"
PLACE_ID = "3237168"  # Replace with the actual place ID

# Store previous state
previous_state = {}


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

def search_player_in_game(user_id, place_id):
    cursor = None
    while True:
        servers = get_servers(place_id, cursor)
        if not servers:
            print("Failed to retrieve servers.")
            return None
        
        cursor = servers.get("nextPageCursor")

        for server in servers.get("data", []):
            # We need to check if the server data includes player info
            playing = server.get("playing", [])
            if isinstance(playing, list) and user_id in playing:
                return server.get("id")

        if not cursor:
            break

    return None


def get_username(user_id):
    url = f"https://users.roblox.com/v1/users/{user_id}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data.get('name', 'Unknown User')
        else:
            return 'Unknown User'
    except requests.RequestException as e:
        print(f"An error occurred while fetching username: {e}")
        return 'Unknown User'

def send_to_discord(message):
    data = {
        "content": message
    }
    try:
        response = requests.post(WEBHOOK_URL, json=data)
        if response.status_code == 204:
            print("Successfully sent to Discord.")
        else:
            print(f"Failed to send to Discord: {response.status_code}")
    except requests.RequestException as e:
        print(f"An error occurred while sending to Discord: {e}")

def get_presence(user_ids):
    url = "https://presence.roblox.com/v1/presence/users"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "userIds": user_ids
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            presence_data = response.json()
            for presence in presence_data.get('userPresences', []):
                user_id = presence.get('userId', 'N/A')
                username = get_username(user_id)
                presence_type = presence.get('userPresenceType', 'N/A')

                presence_type_text = {
                    0: "Offline",
                    1: "Online",
                    2: "In-Game",
                    3: "In-Studio"
                }.get(presence_type, "Unknown")

                if presence_type == 2:  # If user is in-game
                    if user_id in previous_state and previous_state[user_id] != 'In-Game':
                        # User state changed to in-game
                        message = (
                            f"**Username:** {username} (User ID: {user_id})\n"
                            f"**Is now** {presence_type_text}\n"
                        )
                        send_to_discord(message)
                    
                    # Update previous state
                    previous_state[user_id] = 'In-Game'
                    
                    # Now search for the user in the game
                    print(f"User {user_id} is in-game. Scanning servers...")
                    server_id = search_player_in_game(user_id, PLACE_ID)
                    if server_id:
                        message = (
                            f"**User Found in Game!**\n"
                            f"**Username:** {username} (User ID: {user_id})\n"
                            f"**Server ID:** {server_id}\n"
                            f"**DeepLink:** roblox://experiences/start?placeId={PLACE_ID}&gameInstanceId={server_id}"
                        )
                        send_to_discord(message)
                else:
                    # If the user was previously in-game and now they are not
                    if user_id in previous_state and previous_state[user_id] == 'In-Game':
                        message = (
                            f"**Username:** {username} (User ID: {user_id})\n"
                            f"**Has left the game.**\n"
                        )
                        send_to_discord(message)

                    # Update previous state
                    previous_state[user_id] = 'Not In-Game'
        else:
            print(f"Failed to retrieve presence data: {response.status_code}")
    except requests.RequestException as e:
        print(f"An error occurred while fetching presence data: {e}")


# Example call
if __name__ == "__main__":
    user_ids = [3078804436,520944, 43247021, 137621, 1135910299, 295337577, 2350183594]  # Replace with actual user IDs as needed
    while True:
        get_presence(user_ids)
        time.sleep(5)  # Check every 5 seconds
