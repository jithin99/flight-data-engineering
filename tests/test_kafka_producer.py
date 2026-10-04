from collector.kafka_producer import KafkaFlightProducer


class FakeProducer:
    """Fake Kafka producer used for unit testing."""

    def __init__(self, config):
        self.config = config
        self.messages = []
        self.flushed = False

    def produce(self, topic, value, callback):
        self.messages.append(
            {
                "topic": topic,
                "value": value,
                "callback": callback,
            }
        )

    def poll(self, timeout):
        pass

    def flush(self):
        self.flushed = True
        return 0


def test_kafka_producer_configuration(monkeypatch):
    """Kafka producer should use configuration from environment."""

    monkeypatch.setenv(
        "KAFKA_BOOTSTRAP_SERVERS",
        "test-server:9092",
    )
    monkeypatch.setenv(
        "KAFKA_TOPIC",
        "test-flights",
    )

    monkeypatch.setattr(
        "collector.kafka_producer.Producer",
        FakeProducer,
    )

    producer = KafkaFlightProducer()

    assert producer.bootstrap_servers == "test-server:9092"
    assert producer.topic == "test-flights"


def test_publish_event(monkeypatch):
    """A flight event should be converted to JSON and published."""

    monkeypatch.setattr(
        "collector.kafka_producer.Producer",
        FakeProducer,
    )

    producer = KafkaFlightProducer()

    event = {
        "icao24": "test123",
        "callsign": "TEST001",
        "origin_country": "India",
    }

    producer.publish_event(event)

    assert len(producer.producer.messages) == 1

    message = producer.producer.messages[0]

    assert message["topic"] == "flights"
    assert b'"icao24": "test123"' in message["value"]


def test_flush(monkeypatch):
    """Flush should wait for outstanding Kafka messages."""

    monkeypatch.setattr(
        "collector.kafka_producer.Producer",
        FakeProducer,
    )

    producer = KafkaFlightProducer()

    producer.flush()

    assert producer.producer.flushed is True