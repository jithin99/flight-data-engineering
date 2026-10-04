import os
import time
from typing import Optional

import requests
from dotenv import load_dotenv


load_dotenv()


TOKEN_URL = (
    "https://auth.opensky-network.org/"
    "auth/realms/opensky-network/"
    "protocol/openid-connect/token"
)


class OpenSkyTokenManager:
    """Manages OpenSky OAuth2 access tokens."""

    def __init__(self):
        self.client_id = os.getenv("OPENSKY_CLIENT_ID")
        self.client_secret = os.getenv("OPENSKY_CLIENT_SECRET")

        if not self.client_id:
            raise ValueError("OPENSKY_CLIENT_ID is not set.")

        if not self.client_secret:
            raise ValueError("OPENSKY_CLIENT_SECRET is not set.")

        self.access_token: Optional[str] = None
        self.expires_at: float = 0

    def get_token(self) -> str:
        """
        Return a valid access token.

        Refreshes the token when it is missing or close to expiry.
        """

        if self.access_token and time.time() < self.expires_at:
            return self.access_token

        return self._request_new_token()

    def _request_new_token(self) -> str:
        """Request a new OAuth2 access token from OpenSky."""

        response = requests.post(
            TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=30,
        )

        response.raise_for_status()

        token_data = response.json()

        self.access_token = token_data["access_token"]

        expires_in = token_data.get("expires_in", 1800)

        # Refresh 30 seconds before actual expiry.
        self.expires_at = time.time() + expires_in - 30

        return self.access_token