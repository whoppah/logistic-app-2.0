#backend/logistics/services/slack_service.py
import os
import requests
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from django.conf import settings


class SlackService:
    def __init__(self, bot_token=None, channel_id=None):
        self.token = bot_token or settings.SLACK_BOT_TOKEN
        if not self.token:
            raise RuntimeError("Missing SLACK_BOT_TOKEN in settings.")
        self.channel = channel_id or settings.SLACK_CHANNEL_ID
        if not self.channel:
            raise RuntimeError("Missing SLACK_CHANNEL_ID in settings.")
        self.client = WebClient(token=self.token)
        # where downloaded files go (if you ever call download_file)
        self.save_path = os.path.join(
            settings.BASE_DIR, "backend", "logistics", "slack"
        )
        os.makedirs(self.save_path, exist_ok=True)

    def _enrich_users(self, msgs):
        """
        Given a list of message dicts, batch-fetch each unique user's profile
        and attach `user_name` + `user_avatar` onto each msg.
        """
        # collect unique user IDs
        user_ids = {m["user"] for m in msgs if m.get("user")}
        profiles = {}
        for uid in user_ids:
            try:
                uresp = self.client.users_info(user=uid)
                prof = uresp["user"]["profile"]
                profiles[uid] = {
                    "name":   prof.get("display_name") or prof.get("real_name") or uid,
                    "avatar": prof.get("image_72"),
                }
            except SlackApiError:
                profiles[uid] = {"name": uid, "avatar": None}

        # attach
        for m in msgs:
            uid = m.get("user")
            if uid in profiles:
                m["user_name"]   = profiles[uid]["name"]
                m["user_avatar"] = profiles[uid]["avatar"]

        return msgs

    def get_latest_messages(self, limit=50):
        """
        Fetch the last `limit` messages from the channel, include reply counts.
        """
        try:
            resp = self.client.conversations_history(
                channel=self.channel,
                limit=limit,
                include_all_metadata=True,
                include_reply_count=True,
            )
            msgs = resp.get("messages", [])
            return self._enrich_users(msgs)
        except SlackApiError as e:
            err = e.response["error"]
            print(f"Error fetching messages: {err}")
            if err == "channel_not_found":
                # debug: list private channels
                try:
                    lst = self.client.conversations_list(
                        types="private_channel", limit=100
                    )
                    chans = {c["name"]: c["id"] for c in lst.get("channels", [])}
                    print("Bot is in these private channels:", chans)
                except SlackApiError as list_err:
                    print(
                        "Failed to list private channels:",
                        list_err.response["error"],
                    )
            return []

    def get_thread(self, thread_ts, limit=100):
        """
        Return parent + all replies up to `limit`, then attach user info.
        """
        try:
            resp = self.client.conversations_replies(
                channel=self.channel,
                ts=thread_ts,
                limit=limit,
            )
            msgs = resp.get("messages", [])
            return self._enrich_users(msgs)
        except SlackApiError as e:
            print(f"Error fetching thread: {e.response['error']}")
            return []

    def react_to_message(self, ts, emoji_name):
        """
        Add a reaction. (Slack itself will toggle if you re‐use the same emoji.)
        """
        try:
            self.client.reactions_add(
                channel=self.channel, timestamp=ts, name=emoji_name
            )
            print(f"Added :{emoji_name}: to message {ts}")
        except SlackApiError as e:
            print(f"Error adding reaction: {e.response['error']}")

    def remove_reaction(self, ts, emoji_name):
        try:
            self.client.reactions_remove(
                channel=self.channel, timestamp=ts, name=emoji_name
            )
            print(f"Removed :{emoji_name}: from message {ts}")
        except SlackApiError as e:
            print(f"Error removing reaction: {e.response['error']}")

    def download_file(self, file_id):
        try:
            file_info = self.client.files_info(file=file_id)
            file_url   = file_info["file"]["url_private"]
            file_name  = file_info["file"]["name"]
            headers    = {"Authorization": f"Bearer {self.token}"}
            resp       = requests.get(file_url, headers=headers)
            path       = os.path.join(self.save_path, file_name)
            if resp.status_code == 200:
                with open(path, "wb") as f:
                    f.write(resp.content)
                print(f"File downloaded: {file_name}")
                return file_name
            else:
                print("Failed to download the file.")
                return None
        except SlackApiError as e:
            print(f"Error fetching file info: {e.response['error']}")
            return None

    def extract_partner(self, message_text):
        import re

        match = re.search(r"Partner:\s*([\w_]+)", message_text)
        return match.group(1).lower() if match else None
