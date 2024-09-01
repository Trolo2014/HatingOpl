import requests
import aiohttp
import asyncio
import time

from keep_alive import keep_alive
keep_alive()

WEBHOOK_URL = "https://discord.com/api/webhooks/1116120565955182722/jCrzUqFdd29XD_xMzqIFfgHImP_coEi4TzsQEgCjFXx2F5ReW-xiBR2Q5sbOPf9EPZUm"
PLACE_ID = "3237168"  # Replace with the actual place ID

previous_state = {}

async def get_avatar_thumbnail(user_id, retries=5, delay=5):
    url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&format=Png&size=150x150"
    async with aiohttp.ClientSession() as session:
        for attempt in range(retries):
            try:
                async with session.get(url) as response:
                    response.raise_for_status()
                    data = await response.json()
                    if 'data' in data and len(data['data']) > 0:
                        return data['data'][0]['imageUrl']
                    return None
            except aiohttp.ClientError as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(delay)
    return None

async def fetch_thumbnails(tokens):
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
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=body) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            print(f"Error fetching thumbnails: {e}")
            return None

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
            tokens = server.get("playerTokens", [])
            if user_id in tokens:
                return server.get("id")

        if not cursor:
            break

    return None

def get_user_presence(user_ids):
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
            return response.json().get('userPresences', [])
        else:
            print(f"Failed to retrieve presence data: {response.status_code}")
            return []
    except requests.RequestException as e:
        print(f"An error occurred while fetching presence data: {e}")
        return []

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

async def main():
    user_ids = [3078804436, 520944, 43247021, 137621, 1135910299, 295337577, 2350183594]  # Replace with actual user IDs

    while True:
        # Request presence for all user IDs
        presence_data = get_user_presence(user_ids)
        
        for presence in presence_data:
            user_id = presence.get('userId')
            presence_type = presence.get('userPresenceType')
            username = get_username(user_id)  # Get the username for the user ID

            if presence_type == 2:  # User is in-game
                if user_id not in previous_state or previous_state[user_id] != 'In-Game':
                    server_id = search_player_in_game(user_id, PLACE_ID)
                    if server_id:
                        message = (
                            f"**User Found in Game!**\n"
                            f"**Username:** {username} (User ID: {user_id})\n"
                            f"**Server ID:** {server_id}\n"
                            f"**DeepLink:** roblox://experiences/start?placeId={PLACE_ID}&gameInstanceId={server_id}"
                        )
                        send_to_discord(message)
                        previous_state[user_id] = 'In-Game'
                else:
                    previous_state[user_id] = 'In-Game'
            else:
                if user_id in previous_state and previous_state[user_id] == 'In-Game':
                    message = (
                        f"**Username:** {username} (User ID: {user_id})\n"
                        f"**Has left the game.**\n"
                    )
                    send_to_discord(message)
                previous_state[user_id] = 'Not In-Game'

        await asyncio.sleep(5)  # Check every 30 seconds

if __name__ == "__main__":
    asyncio.run(main())
