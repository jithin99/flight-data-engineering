import logging
import time
from typing import Any, Dict, List, Optional

import requests

from collector.auth import OpenSkyTokenManager
from collector.transformer import map_all_states


logger = logging.getLogger(__name__)


OPEN_SKY_URL = "https://opensky-network.org/api/states/all"


class OpenSkyClient:
    """Client for retrieving aircraft state data from OpenSky."""

    def __init__(self, token_manager: OpenSkyTokenManager):
        self.token_manager = token_manager
        self.session = requests.Session()

    def get_states(self) -> Dict[str, Any]:
        """Retrieve the latest aircraft states from OpenSky."""

        token = self.token_manager.get_token()

        headers = {
            "Authorization": f"Bearer {token}",
        }

        params = {
            # Required to receive the extended state information,
            # including aircraft category.
            "extended": 1,
        }

        response = self.session.get(
            OPEN_SKY_URL,
            headers=headers,
            params=params,
            timeout=30,
        )

        # Token may have expired unexpectedly.
        if response.status_code == 401:
            logger.warning("Access token rejected. Refreshing token.")

            self.token_manager.access_token = None
            self.token_manager.expires_at = 0

            token = self.token_manager.get_token()

            headers["Authorization"] = f"Bearer {token}"

            response = self.session.get(
                OPEN_SKY_URL,
                headers=headers,
                params=params,
                timeout=30,
            )

        # API quota/rate-limit handling.
        if response.status_code == 429:
            retry_after = response.headers.get(
                "X-Rate-Limit-Retry-After-Seconds"
            )

            if retry_after:
                logger.warning(
                    "OpenSky rate limit reached. Retry after %s seconds.",
                    retry_after,
                )

                time.sleep(int(retry_after))

            response.raise_for_status()

        response.raise_for_status()

        return response.json()

    def get_flight_events(self) -> List[Dict[str, Any]]:
        """
        Retrieve and transform the latest OpenSky state vectors
        into structured flight events.
        """

        data = self.get_states()

        states = data.get("states") or []

        events = map_all_states(states)

        response_timestamp = data.get("time")

        for event in events:
            event["source_timestamp"] = response_timestamp

        return events