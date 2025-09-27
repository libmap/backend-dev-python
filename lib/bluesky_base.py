import json
import logging
import time
import threading
from urllib.parse import urlencode
import websocket
from datetime import datetime
from .bluesky_did_resolver import did_resolver

class BlueSkyStreamListener:
    def __init__(self, keywords, callback_func, reconnect_attempts=10, reconnect_delay=5):
        self.endpoint = 'wss://jetstream2.us-west.bsky.network/subscribe'
        self.wanted_collections = ['app.bsky.feed.post']
        self.keywords = keywords
        self.callback_func = callback_func
        self.ws = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = reconnect_attempts
        self.reconnect_delay = reconnect_delay
        self.should_run = True

    def _build_url(self):
        params = [('wantedCollections', collection) for collection in self.wanted_collections]
        query_string = urlencode(params)
        return f"{self.endpoint}?{query_string}"

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            self._process_message(data)
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing Bluesky message: {e}")
        except Exception as e:
            logging.error(f"Error processing Bluesky message: {e}")

    def _process_message(self, message):
        if message.get('kind') == 'commit' and message.get('commit'):
            commit = message['commit']
            operation = commit.get('operation', '')

            # Handle deletion events
            if operation == 'delete':
                self._handle_deletion(message)
                return

            # Handle creation/update events (existing logic)
            if commit.get('record') and operation == 'create':
                record = commit['record']

                if record.get('text'):
                    text = record['text'].lower()
                    matched_keywords = [keyword for keyword in self.keywords if keyword.lower() in text]

                    if matched_keywords:
                        # Extract ID from the message - use rkey which is the record key
                        post_id = commit.get('rkey', '')

                        # Construct the proper AT-URI
                        at_uri = f"at://{message.get('did', '')}/app.bsky.feed.post/{post_id}"

                        # Resolve DID to actual handle
                        did = message.get('did', '')
                        resolved_handle = did_resolver.resolve_did_to_handle(did)

                        # Extract reply information if this is a reply
                        in_reply_to_id = None
                        in_reply_to_account_id = None
                        if 'reply' in record and record['reply'].get('parent'):
                            parent_uri = record['reply']['parent'].get('uri', '')
                            if parent_uri.startswith('at://'):
                                # Parse AT-URI to extract DID and post ID
                                # Format: at://did:plc:xxxxx/app.bsky.feed.post/postid
                                parts = parent_uri.split('/')
                                if len(parts) >= 4:
                                    parent_did = parts[2]  # The DID part
                                    in_reply_to_id = parts[-1]  # The post ID part
                                    in_reply_to_account_id = parent_did

                        # Convert to a format similar to Mastodon toot
                        bluesky_post = {
                            'id': post_id,
                            'content': record['text'],
                            'created_at': datetime.fromtimestamp(message.get('time_us', 0) / 1000000).isoformat(),
                            'account': {
                                'acct': did,
                                'username': resolved_handle.replace('@', '') if resolved_handle.startswith('@') else resolved_handle,
                                'display_name': resolved_handle
                            },
                            'uri': at_uri,
                            'url': f"https://bsky.app/profile/{message.get('did', '')}/post/{post_id}",
                            'platform': 'bluesky',
                            'matched_keywords': matched_keywords,
                            'raw_record': record
                        }

                        # Add reply fields if this is a reply
                        if in_reply_to_id:
                            bluesky_post['in_reply_to_id'] = in_reply_to_id
                            bluesky_post['in_reply_to_account_id'] = in_reply_to_account_id

                        self.callback_func(bluesky_post)

    def _handle_deletion(self, message):
        """Handle Bluesky post deletion events - only for posts we've captured"""
        commit = message.get('commit', {})
        post_id = commit.get('rkey', '')

        if post_id:
            # Only process deletions for posts we actually have stored
            # The deletion callback will check if the post exists locally
            if hasattr(self, 'deletion_callback') and self.deletion_callback:
                self.deletion_callback(post_id)

    def set_deletion_callback(self, callback_func):
        """Set a callback function to handle deletions"""
        self.deletion_callback = callback_func

    def on_error(self, ws, error):
        logging.error(f"Bluesky WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        logging.warning("Bluesky connection closed")
        if self.should_run:
            self._reconnect()

    def on_open(self, ws):
        logging.info("Connected to Bluesky Jetstream")
        self.reconnect_attempts = 0

    def _reconnect(self):
        if self.reconnect_attempts < self.max_reconnect_attempts and self.should_run:
            self.reconnect_attempts += 1
            logging.info(f"Reconnecting to Bluesky in {self.reconnect_delay}s (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})")
            time.sleep(self.reconnect_delay)
            self.start_stream()
        else:
            logging.error("Max Bluesky reconnection attempts reached")

    def start_stream(self):
        if not self.should_run:
            return

        try:
            url = self._build_url()
            logging.info(f"Connecting to Bluesky: {url}")

            self.ws = websocket.WebSocketApp(
                url,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close
            )

            self.ws.run_forever()
        except Exception as e:
            logging.error(f"Error starting Bluesky stream: {e}")
            if self.should_run:
                self._reconnect()

    def stop_stream(self):
        self.should_run = False
        if self.ws:
            self.ws.close()