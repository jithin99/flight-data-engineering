from collector.opensky_client import OpenSkyClient


class FakeTokenManager:
    def __init__(self):
        self.access_token = "test-token"
        self.expires_at = 9999999999

    def get_token(self):
        return self.access_token


class FakeResponse:
    def __init__(self, status_code, data=None, headers=None):
        self.status_code = status_code
        self._data = data or {}
        self.headers = headers or {}

    def json(self):
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


def test_get_states_success(monkeypatch):
    token_manager = FakeTokenManager()
    client = OpenSkyClient(token_manager)

    fake_data = {
        "time": 1700000000,
        "states": [
            [
                "abc123",
                "TEST123 ",
                "India",
                1700000000,
                1700000010,
                78.4867,
                17.3850,
                10000.0,
                False,
                250.0,
                90.0,
                0.5,
                None,
                10100.0,
                "1234",
                False,
                0,
                0,
            ]
        ],
    }

    def fake_get(*args, **kwargs):
        return FakeResponse(200, fake_data)

    monkeypatch.setattr(client.session, "get", fake_get)

    result = client.get_states()

    assert result["time"] == 1700000000
    assert len(result["states"]) == 1
    assert result["states"][0][0] == "abc123"


def test_get_flight_events(monkeypatch):
    token_manager = FakeTokenManager()
    client = OpenSkyClient(token_manager)

    fake_data = {
        "time": 1700000000,
        "states": [
            [
                "abc123",
                "TEST123 ",
                "India",
                1700000000,
                1700000010,
                78.4867,
                17.3850,
                10000.0,
                False,
                250.0,
                90.0,
                0.5,
                None,
                10100.0,
                "1234",
                False,
                0,
                0,
            ]
        ],
    }

    monkeypatch.setattr(
        client,
        "get_states",
        lambda: fake_data,
    )

    events = client.get_flight_events()

    assert len(events) == 1
    assert events[0]["icao24"] == "abc123"
    assert events[0]["callsign"] == "TEST123"
    assert events[0]["source_timestamp"] == 1700000000