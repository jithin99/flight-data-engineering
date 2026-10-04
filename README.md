# Real-Time Flight Data Engineering

A production-style data engineering project that collects live aircraft
state data from the OpenSky Network and builds a real-time data pipeline.

The project is designed to demonstrate:

- REST API ingestion
- OAuth2 authentication
- Python-based data collection
- Streaming data architecture
- Databricks Declarative Pipelines
- Bronze / Silver / Gold data layers
- Data quality and streaming concepts
- Analytical flight data

---

## Architecture

The target architecture is:

OpenSky Network
        ↓
Python API Collector
        ↓
Kafka / Azure Event Hubs
        ↓
Databricks
        ↓
Bronze
        ↓
Silver
        ↓
Gold
        ↓
Dashboard


The Python collector is intentionally separated from Databricks.
The collector handles external REST API ingestion, while Databricks
will later handle stream processing and analytics.

---

## Current Progress

### Phase 1 — OpenSky API Collector

Completed:

- OpenSky REST API integration
- OAuth2 client-credentials authentication
- Automatic access-token management
- Automatic token refresh
- OpenSky `/states/all` ingestion
- Extended aircraft state information
- Positional state-vector transformation
- Structured flight event generation
- Configurable polling interval
- HTTP error handling
- Rate-limit handling
- Local JSON sample generation
- Automated unit tests

Current collector flow:

OpenSky REST API
        ↓
OAuth2 Authentication
        ↓
OpenSky Client
        ↓
State Vector Transformation
        ↓
Structured Flight Events
        ↓
Local JSON Sample


---

## Project Structure

```text
flight-data-engineering/
│
├── src/
│   └── collector/
│       ├── __init__.py
│       ├── auth.py
│       ├── main.py
│       ├── opensky_client.py
│       └── transformer.py
│
├── databricks/
│
├── data/
│   └── samples/
│
├── tests/
│   ├── test_auth.py
│   ├── test_opensky_client.py
│   └── test_transformer.py
│
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
