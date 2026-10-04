from collector.transformer import map_state, map_all_states


def test_map_state():
    state = [
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

    result = map_state(state)

    assert result["icao24"] == "abc123"
    assert result["callsign"] == "TEST123"
    assert result["origin_country"] == "India"
    assert result["longitude"] == 78.4867
    assert result["latitude"] == 17.3850
    assert result["baro_altitude"] == 10000.0
    assert result["on_ground"] is False
    assert result["velocity"] == 250.0
    assert result["category"] == 0


def test_map_state_handles_missing_fields():
    state = [
        "abc123",
        "TEST123 ",
        "India",
    ]

    result = map_state(state)

    assert result["icao24"] == "abc123"
    assert result["callsign"] == "TEST123"
    assert result["origin_country"] == "India"
    assert result["longitude"] is None
    assert result["latitude"] is None
    assert result["velocity"] is None
    assert result["category"] is None


def test_map_all_states():
    states = [
        [
            "abc123",
            "TEST123 ",
            "India",
            1700000000,
            1700000010,
            78.4867,
            17.3850,
        ],
        [
            "def456",
            "TEST456 ",
            "France",
            1700000000,
            1700000010,
            2.3522,
            48.8566,
        ],
    ]

    result = map_all_states(states)

    assert len(result) == 2
    assert result[0]["icao24"] == "abc123"
    assert result[1]["icao24"] == "def456"