import requests
import time
import asyncio

WEBHOOK_URL = "https://discord.com/api/webhooks/1116120565955182722/jCrzUqFdd29XD_xMzqIFfgHImP_coEi4TzsQEgCjFXx2F5ReW-xiBR2Q5sbOPf9EPZUm"

# Store previous state and floors state
previous_state = {}
floors_sent = {}

# Define the specific place ID (game) to track
SPECIFIC_PLACE_ID = 1234567890  # Replace with the actual place ID

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

async def get_servers(place_id, cursor=None, retries=10):
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
            await asyncio.sleep(2.5)  # Wait before retrying
    return None

async def search_for_user_in_game(user_id, place_id):
    cursor = None
    while True:
        servers = await get_servers(place_id, cursor)
        if not servers:
            return False  # Failed to get server data after retries

        for server in servers.get("data", []):
            for player in server.get("players", []):
                if player.get("userId") == user_id:
                    return True  # User is found in the game

        cursor = servers.get("nextPageCursor")
        if not cursor:
            break  # No more servers to search through

    return False  # User not found in any server of the game

async def get_presence(user_ids):
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

                current_state = f"Presence Type: {presence_type}"

                # Check if the user is in the specific game
                is_in_specific_game = await search_for_user_in_game(user_id, SPECIFIC_PLACE_ID)

                if is_in_specific_game and not floors_sent.get(user_id, False):
                    # Send the floors message
                    message = (
                        f"**Username:** {username} (User ID: {user_id})\n"
                        f"**Is now in the specific game (Place ID: {SPECIFIC_PLACE_ID})**\n"
                        f"**Floors:**"
                    )
                    send_to_discord(message)
                    floors_sent[user_id] = True  # Mark that we've sent the floors message for this user
                elif not is_in_specific_game:
                    floors_sent[user_id] = False  # Reset if the user leaves the specific game

                # Update the message if presence changes
                if user_id in previous_state:
                    if previous_state[user_id] != current_state:
                        message = (
                            f"**Username:** {username} (User ID: {user_id})\n"
                            f"**Is {current_state}**\n"
                        )
                        send_to_discord(message)
                else:
                    if presence_type != 0:  # Only notify if not offline
                        message = (
                            f"**Username:** {username} (User ID: {user_id})\n"
                            f"**Is {current_state}**\n"
                        )
                        send_to_discord(message)

                # Update previous state
                previous_state[user_id] = current_state
        else:
            print(f"Failed to retrieve presence data: {response.status_code}")
    except requests.RequestException as e:
        print(f"An error occurred while fetching presence data: {e}")

# Example call
if __name__ == "__main__":
    user_ids = [520944, 43247021, 137621, 1135910299, 295337577, 2350183594]  # Replace with actual user IDs as needed
    while True:
        asyncio.run(get_presence(user_ids))
        time.sleep(30)  # Check every 30 seconds
