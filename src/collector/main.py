import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from collector.auth import OpenSkyTokenManager
from collector.opensky_client import OpenSkyClient


load_dotenv()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SAMPLE_DIR = PROJECT_ROOT / "data" / "samples"
SAMPLE_FILE = SAMPLE_DIR / "opensky_sample.json"

POLL_INTERVAL_SECONDS = int(
    os.getenv("OPENSKY_POLL_INTERVAL_SECONDS", "30")
)


def save_sample(events):
    """Save the latest structured events as a local development sample."""

    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    sample = {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "aircraft_count": len(events),
        "events": events,
    }

    with SAMPLE_FILE.open("w", encoding="utf-8") as file:
        json.dump(sample, file, indent=2)

    logger.info("Sample saved to %s", SAMPLE_FILE)


def run_once(client: OpenSkyClient):
    """Execute one API collection cycle."""

    logger.info("Requesting aircraft states from OpenSky...")

    events = client.get_flight_events()

    logger.info("Received %s aircraft events.", len(events))

    if events:
        logger.info("First event:")
        logger.info(json.dumps(events[0], indent=2))

    save_sample(events)


def run():
    """Run the collector continuously."""

    token_manager = OpenSkyTokenManager()
    client = OpenSkyClient(token_manager)

    logger.info("OpenSky collector started.")
    logger.info(
        "Polling interval: %s seconds",
        POLL_INTERVAL_SECONDS,
    )

    while True:
        try:
            run_once(client)

        except KeyboardInterrupt:
            logger.info("Collector stopped by user.")
            break

        except Exception:
            logger.exception("Collection cycle failed.")

        logger.info(
            "Waiting %s seconds before next collection...",
            POLL_INTERVAL_SECONDS,
        )

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    run()