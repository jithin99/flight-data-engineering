import json
import logging
import os
from typing import Any, Dict, Optional

from confluent_kafka import Producer
from dotenv import load_dotenv


load_dotenv()


logger = logging.getLogger(__name__)


class KafkaFlightProducer:
    """Publishes flight events to a Kafka topic."""

    def __init__(
        self,
        bootstrap_servers: Optional[str] = None,
        topic: Optional[str] = None,
    ):
        self.bootstrap_servers = (
            bootstrap_servers
            or os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        )

        self.topic = (
            topic
            or os.getenv("KAFKA_TOPIC", "flights")
        )

        self.producer = Producer(
            {
                "bootstrap.servers": self.bootstrap_servers,
            }
        )

    def delivery_report(self, err, message):
        """Handle Kafka message delivery result."""

        if err is not None:
            logger.error(
                "Kafka delivery failed: %s",
                err,
            )
        else:
            logger.info(
                "Kafka event delivered: topic=%s partition=%s offset=%s",
                message.topic(),
                message.partition(),
                message.offset(),
            )

    def publish_event(self, event: Dict[str, Any]):
        """Publish one flight event to Kafka."""

        payload = json.dumps(event)

        self.producer.produce(
            topic=self.topic,
            value=payload.encode("utf-8"),
            callback=self.delivery_report,
        )

        self.producer.poll(0)

    def flush(self):
        """Wait for outstanding Kafka messages."""

        remaining = self.producer.flush()

        if remaining > 0:
            logger.warning(
                "%s Kafka messages were not delivered.",
                remaining,
            )