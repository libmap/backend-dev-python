import requests
import logging
import json
import time
from datetime import datetime, timedelta

class BlueSkyDIDResolver:
    def __init__(self):
        self.cache = {}
        self.cache_expiry = {}
        self.cache_duration = timedelta(hours=24)  # Cache for 24 hours

    def resolve_did_to_handle(self, did):
        """
        Resolve a DID to a Bluesky handle using AT Protocol

        Args:
            did (str): The DID to resolve (e.g., 'did:plc:adsquh2z4vzbpeelyvkq4rbl')

        Returns:
            str: The resolved handle (e.g., '@username.bsky.social') or formatted DID if resolution fails
        """
        # Check cache first
        if self._is_cached(did):
            return self.cache[did]

        try:
            # Use AT Protocol's com.atproto.identity.resolveHandle API
            # But we need to resolve DID to handle, so we use the directory service

            # Try multiple resolution methods
            handle = self._resolve_via_plc_directory(did)
            if not handle:
                handle = self._resolve_via_bsky_api(did)

            if handle:
                # Cache the result
                self._cache_result(did, handle)
                return handle
            else:
                # Fallback: format the DID nicely
                fallback = self._format_did_fallback(did)
                self._cache_result(did, fallback)
                return fallback

        except Exception as e:
            logging.warning(f"Failed to resolve DID {did}: {e}")
            fallback = self._format_did_fallback(did)
            self._cache_result(did, fallback)
            return fallback

    def _resolve_via_plc_directory(self, did):
        """Try to resolve via PLC directory"""
        try:
            # PLC directory API
            url = f"https://plc.directory/{did}"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                # Look for the handle in the service endpoints
                if 'alsoKnownAs' in data:
                    for aka in data['alsoKnownAs']:
                        if aka.startswith('at://'):
                            handle = aka.replace('at://', '')
                            return f"@{handle}"

        except Exception as e:
            logging.debug(f"PLC directory resolution failed for {did}: {e}")

        return None

    def _resolve_via_bsky_api(self, did):
        """Try to resolve via Bluesky's public API"""
        try:
            # Use Bluesky's public API to get profile
            url = f"https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile"
            params = {'actor': did}
            response = requests.get(url, params=params, timeout=5)

            if response.status_code == 200:
                data = response.json()
                if 'handle' in data:
                    return f"@{data['handle']}"

        except Exception as e:
            logging.debug(f"Bluesky API resolution failed for {did}: {e}")

        return None

    def _format_did_fallback(self, did):
        """Format DID as a more readable fallback"""
        if did.startswith('did:plc:'):
            # Take first 8 characters of the identifier
            identifier = did.split(':')[-1][:8]
            return f"@{identifier}...bsky"
        return did

    def _is_cached(self, did):
        """Check if DID is in cache and not expired"""
        if did not in self.cache:
            return False

        if did in self.cache_expiry:
            if datetime.now() > self.cache_expiry[did]:
                # Cache expired, remove it
                del self.cache[did]
                del self.cache_expiry[did]
                return False

        return True

    def _cache_result(self, did, handle):
        """Cache the resolution result"""
        self.cache[did] = handle
        self.cache_expiry[did] = datetime.now() + self.cache_duration

    def clear_cache(self):
        """Clear the entire cache"""
        self.cache.clear()
        self.cache_expiry.clear()

# Global instance for reuse
did_resolver = BlueSkyDIDResolver()