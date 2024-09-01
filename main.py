import requests
import time

# Discord Webhook URL
WEBHOOK_URL = "https://discord.com/api/webhooks/1274437598374531234/VaxESeur0SZaSIQzWqH7pmjrZcctBQxLvF-aOSVeypfqKT5w-60CB9-_ruuiKxZYsyJg"

# Place ID for the game
PLACE_ID = "3237168"  # Replace with the actual place ID

previous_state = {}

# Function to send messages to Discord webhook
def send_to_discord(content, embed=None):
    data = {"content": content}
    if embed:
        data["embeds"] = [embed]
    try:
        response = requests.post(WEBHOOK_URL, json=data)
        if response.status_code == 204:
            print("Successfully sent to Discord.")
        elif response.status_code != 429:  # Ignore rate limit errors
            print(f"Failed to send to Discord: {response.status_code}")
    except requests.RequestException as e:
        print(f"An error occurred while sending to Discord: {e}")

# Function to get user ID from username
def get_user_id(username):
    url = "https://users.roblox.com/v1/usernames/users"
    params = {"usernames": [username]}
    try:
        response = requests.post(url, json=params)
        response.raise_for_status()
        data = response.json()
        if data and 'data' in data and len(data['data']) > 0:
            user_id = data['data'][0]['id']
            return user_id
        send_to_discord(f"**Error:** Failed to get user ID for username: {username}.")
        return None
    except requests.RequestException as e:
        send_to_discord(f"**Error:** {e}")
        return None

# Function to get avatar thumbnail URL
def get_avatar_thumbnail(user_id):
    url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&format=Png&size=150x150"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if 'data' in data and len(data['data']) > 0:
            return data['data'][0]['imageUrl']
        send_to_discord(f"**Error:** Failed to get avatar thumbnail for user ID: {user_id}.")
        return None
    except requests.RequestException as e:
        send_to_discord(f"**Error:** {e}")
        return None

# Function to get game servers
def get_servers(place_id, cursor=None):
    url = f"https://games.roblox.com/v1/games/{place_id}/servers/Public?limit=100"
    if cursor:
        url += f"&cursor={cursor}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        send_to_discord(f"**Error:** {e}")
        return None

# Function to batch fetch thumbnails
def fetch_thumbnails(tokens):
    body = [
        {
            "requestId": f"0:{token}:AvatarHeadshot:150x150:png:regular",
            "type": "AvatarHeadShot",
            "targetId": 0,
            "token": token,
            "format": "png",
            "size": "150x150"
        }
        for token in tokens
    ]
    url = "https://thumbnails.roblox.com/v1/batch"
    try:
        response = requests.post(url, json=body)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        send_to_discord(f"**Error:** {e}")
        return None

# Function to search for player
def search_player(place_id, username):
    user_id = get_user_id(username)
    if not user_id:
        return "User not found", None

    target_thumbnail_url = get_avatar_thumbnail(user_id)
    if not target_thumbnail_url:
        return "Failed to get avatar thumbnail", None

    cursor = None
    all_player_tokens = []
    server_data = []

    while True:
        servers = get_servers(place_id, cursor)
        if not servers:
            return "Failed to get servers", None

        cursor = servers.get("nextPageCursor")

        for server in servers.get("data", []):
            tokens = server.get("playerTokens", [])
            all_player_tokens.extend(tokens)
            server_data.extend([(token, server) for token in tokens])

        if not cursor:
            break

    chunk_size = 100
    for i in range(0, len(all_player_tokens), chunk_size):
        chunk = all_player_tokens[i:i + chunk_size]
        thumbnails = fetch_thumbnails(chunk)
        if not thumbnails:
            return "Failed to fetch thumbnails", None

        for thumb in thumbnails.get("data", []):
            if thumb["imageUrl"] == target_thumbnail_url:
                for token, server in server_data:
                    if token == thumb["requestId"].split(":")[1]:
                        return "Player found", server.get("id")

    return "Player not found", None

# Function to get user presence
def get_user_presence(user_ids):
    url = "https://presence.roblox.com/v1/presence/users"
    headers = {"Content-Type": "application/json"}
    data = {"userIds": user_ids}
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return response.json().get('userPresences', [])
        else:
            send_to_discord(f"**Error:** Failed to retrieve presence data: {response.status_code}")
            return []
    except requests.RequestException as e:
        send_to_discord(f"**Error:** {e}")
        return []

# Function to get username from user ID
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
        send_to_discord(f"**Error:** {e}")
        return 'Unknown User'

def main():
    user_ids = [520944, 43247021, 137621, 1135910299, 295337577, 2350183594]  # Replace with actual user IDs

    while True:
        # Request presence for all user IDs
        presence_data = get_user_presence(user_ids)

        for presence in presence_data:
            user_id = presence.get('userId')
            presence_type = presence.get('userPresenceType')
            username = get_username(user_id)  # Get the username for the user ID
            thumbnail_url = get_avatar_thumbnail(user_id)  # Get the avatar thumbnail URL

            if presence_type == 2:  # User is in-game
                if user_id not in previous_state or previous_state[user_id] != 'In-Game':
                    status, server_id = search_player(PLACE_ID, username)
                    if server_id:
                        embed = {
                            "title": "User Found in Game!",
                            "thumbnail": {
                                "url": thumbnail_url
                            },
                            "fields": [
                                {"name": "Username", "value": f"{username}", "inline": True},
                                {"name": "Server ID", "value": server_id, "inline": True},
                                {"name": "DeepLink", "value": f"roblox://experiences/start?placeId={PLACE_ID}&gameInstanceId={server_id}", "inline": False}
                            ]
                        }
                        send_to_discord("", embed)
                        previous_state[user_id] = 'In-Game'
                else:
                    previous_state[user_id] = 'In-Game'
            else:
                if user_id in previous_state and previous_state[user_id] == 'In-Game':
                    embed = {
                        "title": "User Left the Game",
                        "thumbnail": {
                            "url": thumbnail_url
                        },
                        "fields": [
                            {"name": "Username", "value": f"{username}", "inline": False}
                        ]
                    }
                    send_to_discord("", embed)
                previous_state[user_id] = 'Not In-Game'

        time.sleep(15)  # Check every 10 seconds

if __name__ == "__main__":
    main()
