from collector.auth import OpenSkyTokenManager


def test_token_manager_gets_token(monkeypatch):
    manager = OpenSkyTokenManager()

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "access_token": "test-access-token",
                "expires_in": 1800,
            }

    def fake_post(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "collector.auth.requests.post",
        fake_post,
    )

    token = manager.get_token()

    assert token == "test-access-token"
    assert manager.access_token == "test-access-token"
    assert manager.expires_at > 0