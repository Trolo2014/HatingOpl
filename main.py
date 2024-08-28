import requests
import time

from keep_alive import keep_alive
keep_alive()

WEBHOOK_URL = "https://discord.com/api/webhooks/1116120565955182722/jCrzUqFdd29XD_xMzqIFfgHImP_coEi4TzsQEgCjFXx2F5ReW-xiBR2Q5sbOPf9EPZUm"

# Store previous state
previous_state = {}

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

                current_state = f"{presence_type_text}"

                if user_id in previous_state:
                    if previous_state[user_id] != current_state:
                        message = (
                            f"**Username:** {username} (User ID: {user_id})\n"
                            f"**Presence Type:** {current_state}\n"
                        )
                        send_to_discord(message)
                else:
                    if presence_type != 0:  # Only notify if not offline
                        message = (
                            f"**Username:** {username} (User ID: {user_id})\n"
                            f"**Presence Type:** {current_state}\n"
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
    user_ids = [5419521266, 520944, 43247021, 137621, 1135910299, 295337577, 2350183594]  # Replace with actual user IDs as needed
    while True:
        get_presence(user_ids)
        time.sleep(60)  # Check every 60 seconds
