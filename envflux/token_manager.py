#!/usr/bin/env python3

import json
import logging
import pathlib
import time

from platformdirs import user_cache_dir

APP_NAME = "envflux"
TOKEN_FILENAME = "token.json"

# Use OS-appropriate user cache directory
DEFAULT_TOKEN_PATH = pathlib.Path(user_cache_dir(APP_NAME)) / TOKEN_FILENAME

logger = logging.getLogger(__name__)

class TokenManager:
    """Manages token-based authentication for an Envoy instance.
    Handles loading, saving, validating, and refreshing tokens.
    """

    def __init__(self, envoy, path=None, buffer_seconds=600):
        self.envoy = envoy
        self.path = pathlib.Path(path) if path else DEFAULT_TOKEN_PATH
        self.buffer_seconds = buffer_seconds
        self.token_data = self._load_token()

    def _load_token(self):
        if self.path.is_file():
            try:
                with self.path.open("r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load token file: {e}")
        return None

    def _save_token(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("w") as f:
                json.dump(self.token_data, f)
        except Exception as e:
            logger.error(f"Failed to save token: {e}")

    def is_expiring_soon(self):
        if not self.token_data:
            return True
        expires = self.token_data.get("expire_timestamp", 0)
        return expires <= (time.time() + self.buffer_seconds)

    def _update_from_envoy(self):
        self.token_data = {
            "token": self.envoy.auth.token,
            "expire_timestamp": self.envoy.auth.expire_timestamp,
            "token_type": self.envoy.auth.token_type,
        }
        self._save_token()

    async def authenticate(self, username, password):
        """Authenticate with Envoy using a cached token if valid.
        Falls back to username/password if token is expired or rejected.
        """
        if self.token_data and not self.is_expiring_soon():
            logger.info("Trying cached token...")
            try:
                await self.envoy.authenticate(
                    username=username,
                    password=password,
                    token=self.token_data["token"]
                )
                logger.info("Authenticated using cached token.")
                return
            except Exception as e:
                logger.error(f"Token authentication failed: {e}. Falling back to username/password.")

        logger.info("Authenticating using username and password...")
        await self.envoy.authenticate(username=username, password=password)
        self._update_from_envoy()
        logger.info("Authenticated and new token saved.")

    async def refresh_if_needed(self):
        """Refresh the token if it's expiring soon. Saves the new token after refreshing.
        """
        if self.is_expiring_soon():
            logger.info("Token is expiring soon. Refreshing...")
            try:
                await self.envoy.auth.refresh()
                self._update_from_envoy()
                logger.info("Token refreshed and saved.")
            except Exception as e:
                logger.warning(f"Token refresh failed: {e}")
