from typing import Any, Dict, List, Optional


def get_field(state: List[Any], index: int) -> Optional[Any]:
    """Safely retrieve a field from an OpenSky state vector."""

    if len(state) > index:
        return state[index]

    return None


def map_state(state: List[Any]) -> Dict[str, Any]:
    """
    Convert an OpenSky positional state vector
    into a structured flight event.
    """

    callsign = get_field(state, 1)

    return {
        "icao24": get_field(state, 0),
        "callsign": callsign.strip() if callsign else None,
        "origin_country": get_field(state, 2),
        "time_position": get_field(state, 3),
        "last_contact": get_field(state, 4),
        "longitude": get_field(state, 5),
        "latitude": get_field(state, 6),
        "baro_altitude": get_field(state, 7),
        "on_ground": get_field(state, 8),
        "velocity": get_field(state, 9),
        "true_track": get_field(state, 10),
        "vertical_rate": get_field(state, 11),
        "sensors": get_field(state, 12),
        "geo_altitude": get_field(state, 13),
        "squawk": get_field(state, 14),
        "spi": get_field(state, 15),
        "position_source": get_field(state, 16),
        "category": get_field(state, 17),
    }


def map_all_states(states: List[List[Any]]) -> List[Dict[str, Any]]:
    """Convert all OpenSky state vectors into structured events."""

    return [map_state(state) for state in states]