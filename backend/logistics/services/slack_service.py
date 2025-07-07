#backend/logistics/services/slack_service.py
import os
import re
import requests
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from django.conf import settings


class SlackService:
    def __init__(self, bot_token=None, channel_id=None):
        self.token = bot_token or settings.SLACK_BOT_TOKEN
        self.channel = channel_id or settings.SLACK_CHANNEL_ID
        self.client = WebClient(token=self.token)
        self.save_path = os.path.join(settings.BASE_DIR, "backend", "logistics", "slack")
        os.makedirs(self.save_path, exist_ok=True)

    def get_latest_messages(self, limit=10):
        try:
            response = self.client.conversations_history(channel=self.channel, limit=limit)
            return response.get("messages", [])
        except SlackApiError as e:
            print(f"Error fetching messages: {e.response['error']}")
            return []

    def download_file(self, file_id):
        try:
            file_info = self.client.files_info(file=file_id)
            file_url = file_info["file"]["url_private"]
            file_name = file_info["file"]["name"]
            headers = {"Authorization": f"Bearer {self.token}"}

            response = requests.get(file_url, headers=headers)
            full_path = os.path.join(self.save_path, file_name)

            if response.status_code == 200:
                with open(full_path, "wb") as f:
                    f.write(response.content)
                print(f"File downloaded: {file_name}")
                return os.path.splitext(file_name)[0]
            else:
                print("Failed to download the file.")
                return None
        except SlackApiError as e:
            print(f"Error fetching file info: {e.response['error']}")
            return None
            
    def get_thread(self, thread_ts, limit=50):
        """
        Return up to `limit` messages in the thread starting at thread_ts.
        """
        try:
            resp = self.client.conversations_replies(
                channel=self.channel,
                ts=thread_ts,
                limit=limit,
            )
            return resp.get("messages", [])
        except SlackApiError as e:
            print(f"Error fetching thread: {e.response['error']}")
            return []

    def react_to_message(self, ts, emoji_name):
        try:
            self.client.reactions_add(channel=self.channel, timestamp=ts, name=emoji_name)
            print(f"Added :{emoji_name}: to message {ts}")
        except SlackApiError as e:
            print(f"Error adding reaction: {e.response['error']}")

    def remove_reaction(self, ts, emoji_name):
        try:
            self.client.reactions_remove(channel=self.channel, timestamp=ts, name=emoji_name)
            print(f"Removed :{emoji_name}: from message {ts}")
        except SlackApiError as e:
            print(f"Error removing reaction: {e.response['error']}")

    def extract_partner(self, message_text):
        match = re.search(r'Partner:\s*([\w_]+)', message_text)
        return match.group(1).lower() if match else None

