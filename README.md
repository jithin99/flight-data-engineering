# Real-Time Flight Data Engineering Platform

A real-time data engineering project that collects live aircraft data from the **OpenSky Network**, streams the events through **Apache Kafka**, processes them using **Databricks Lakeflow Declarative Pipelines**, and exposes the resulting analytics through a **Databricks dashboard**.

I built this project to understand what an end-to-end streaming data platform looks like in practice — starting from an external REST API, moving through a streaming platform, processing the data using a Lakehouse architecture, and finally serving analytics through a dashboard.

---

## Architecture

```text
OpenSky Network
       │
       │ REST API
       ▼
Python API Collector
       │
       │ Aircraft Events
       ▼
Apache Kafka
(Confluent Cloud)
       │
       │ Streaming Events
       ▼
Databricks Bronze
Raw Flight Events
       │
       ▼
Lakeflow Declarative Pipeline
       │
       ▼
Databricks Silver
Cleaned & Validated Events
       │
       ▼
Gold Layer
       │
       ├──────────────┬────────────────┐
       ▼              ▼                ▼
Current Aircraft  Country Metrics  Time-Series Metrics
       │              │                │
       └──────────────┴────────────────┘
                      │
                      ▼
             Databricks Dashboard
```

---

## What I Built

The project starts with live aircraft state data from the **OpenSky Network API**.

A Python collector authenticates with OpenSky, retrieves aircraft state information, converts the positional API response into structured aircraft events, and publishes each event to Kafka.

Databricks consumes those Kafka events and processes them through a **Bronze → Silver → Gold** architecture.

```text
OpenSky REST API
        ↓
Python Collector
        ↓
Confluent Kafka
        ↓
Bronze
        ↓
Silver
        ↓
Gold
        ↓
Databricks Dashboard
```

---

## 1. Data Collection — OpenSky Network

OpenSky provides live aircraft state information through a REST API.

The collector retrieves fields such as:

- ICAO24 aircraft identifier
- Callsign
- Origin country
- Latitude
- Longitude
- Barometric altitude
- Geometric altitude
- Velocity
- Heading
- Vertical rate
- Ground status
- Position timestamp
- Last contact timestamp
- Aircraft category

The API response contains aircraft information as positional arrays, so the collector converts those arrays into named JSON events before publishing them downstream.

---

## 2. Authentication

The collector uses **OAuth2 Client Credentials** authentication with OpenSky.

The Python authentication component handles:

- Access token generation
- Token expiration
- Token refresh
- Bearer authentication
- Authentication failures

Credentials are loaded from environment variables and are never stored directly in the source code.

---

## 3. Python Collector

The Python collector is responsible for the external ingestion layer.

Its responsibilities include:

1. Authenticate with OpenSky
2. Request aircraft state information
3. Parse the API response
4. Convert positional arrays into structured events
5. Publish each aircraft event to Kafka
6. Wait for the configured polling interval
7. Repeat

The collector is intentionally kept separate from Databricks.

This means Databricks does not need to continuously call the external REST API itself.

---

## 4. Why Kafka?

OpenSky provides data through a REST API rather than a native event stream.

Instead of directly coupling Databricks to the API, I introduced Kafka between the ingestion and processing layers.

```text
OpenSky API
     ↓
Python Collector
     ↓
Kafka
     ↓
Databricks
```

Kafka acts as the streaming transport layer and separates the external API ingestion process from downstream data processing.

For this project, Kafka is hosted using **Confluent Cloud**.

This architecture also makes it easier to independently scale or replace the producer and consumer components in the future.

---

# Databricks Lakehouse

## 5. Bronze Layer

The Bronze layer receives the raw Kafka events.

```text
Kafka
  ↓
source_data.flight_bronze.flight_events
```

The goal of Bronze is to preserve the incoming event payload before applying business transformations.

This provides a raw source that downstream transformations can build upon.

---

## 6. Silver Layer

The Silver layer converts the raw Kafka payload into structured and validated flight events.

The Silver pipeline performs:

- JSON parsing
- Explicit schema enforcement
- Callsign cleanup
- Unix timestamp conversion
- Event timestamp creation
- Position timestamp creation
- Last-contact timestamp creation
- Coordinate validation
- ICAO24 validation
- Deduplication
- Event-time watermarking
- Ingestion timestamp generation

The resulting dataset is:

```text
flight_events_silver
```

---

## Data Quality Expectations

Lakeflow Declarative Pipeline expectations are used to validate incoming records.

Examples include checking that:

```text
ICAO24 is not null

-180 <= longitude <= 180

-90 <= latitude <= 90
```

Records that fail the configured expectations can be prevented from progressing into the clean Silver dataset.

---

## Streaming Deduplication

Aircraft states may appear repeatedly while the collector continues polling OpenSky.

The Silver pipeline therefore performs deduplication using aircraft identity and event information.

A watermark is also applied to the event timestamp.

```text
Watermark: 10 minutes
```

This allows the pipeline to reason about event time while preventing streaming state from growing indefinitely.

---

# Gold Layer

The Gold layer is designed around the analytical questions required by the dashboard.

Instead of creating one large table for every use case, the project contains separate Gold datasets for different analytical purposes.

```text
flight_events_silver
        │
        ├───────────────┬────────────────────┐
        ▼               ▼                    ▼
flight_current_   flight_country_    flight_activity_
aircraft          metrics            timeseries
```

---

## 7. Current Aircraft

### `flight_current_aircraft`

This materialized view contains the latest known state for each aircraft.

Fields include:

- ICAO24
- Callsign
- Origin country
- Latitude
- Longitude
- Barometric altitude
- Geometric altitude
- Velocity
- Heading
- Vertical rate
- Ground status
- Event timestamp
- Ingestion timestamp

The latest complete aircraft state is selected using the event timestamp.

This dataset powers the **aircraft location map** and latest-aircraft table in the dashboard.

---

## 8. Country Metrics

### `flight_country_metrics`

This Gold dataset aggregates flight activity by origin country.

Metrics include:

- Unique aircraft count
- Airborne observations
- Ground observations
- Average barometric altitude
- Average geometric altitude
- Average velocity

This dataset powers the country-level analytics in the dashboard.

---

## 9. Flight Activity Time Series

### `flight_activity_timeseries`

The time-series Gold dataset aggregates flight activity into **five-minute windows**.

Metrics include:

- Aircraft observations
- Unique aircraft
- Airborne observations
- Ground observations
- Average altitude
- Average velocity

This makes it possible to analyze how aircraft activity changes over time rather than only looking at cumulative totals.

---

# Databricks Dashboard

The final Gold datasets are consumed by a **Databricks dashboard**.

The dashboard includes:

### Real-Time Overview

- Unique Aircraft Observed
- Airborne Observations
- Ground Observations
- Average Flight Velocity
- Average Flight Altitude

### Current Aircraft Positions

A world map plots the latest known aircraft locations using latitude and longitude.

### Latest Aircraft State

A detailed table shows:

- Callsign
- ICAO24
- Origin country
- Latitude
- Longitude
- Altitude
- Velocity
- Ground status
- Event timestamp

### Country Analytics

The dashboard contains visualizations for:

- Top countries by aircraft activity
- Airborne vs ground observations
- Average velocity by country
- Average altitude by country
- Detailed country metrics

### Time-Series Analytics

The dashboard also contains:

- Unique aircraft over time
- Airborne vs ground observations over time
- Average flight velocity over time

---

## Using Databricks Genie for the Dashboard

I used **Databricks Genie** to help build and configure the visualization layer.

Rather than manually creating every visualization, I provided Genie with a structured prompt describing:

- The available Gold datasets
- The meaning of each dataset
- Required KPIs
- Required visualizations
- Aircraft map requirements
- Dashboard filters
- Time-series requirements
- Metric semantics
- Dashboard layout

Genie used those requirements to generate and configure the dashboard visualizations.

The underlying data architecture, streaming pipeline, Silver transformations, Gold data models, metrics, and datasets were implemented separately before the dashboard was created.

This was useful for experimenting with how natural-language tools can sit on top of a well-designed analytical data model.

The dashboard is configured with a **daily refresh schedule** to keep compute usage reasonable for the development environment.

---

# Technology Stack

| Technology | Purpose |
|---|---|
| Python | API collection and event transformation |
| OpenSky Network | Live aircraft data source |
| Apache Kafka | Streaming event transport |
| Confluent Cloud | Managed Kafka infrastructure |
| Databricks | Data engineering and analytics platform |
| Lakeflow Declarative Pipelines | Declarative data processing |
| PySpark | Data transformations |
| Delta Lake | Lakehouse storage |
| Unity Catalog | Data organization and governance |
| Databricks Asset Bundles | Deployment and resource configuration |
| Databricks Genie | AI-assisted dashboard development |
| Databricks Dashboards | Analytics and visualization |
| Git / GitHub | Version control |

---

# Project Structure

```text
flight-data-engineering/
│
├── src/
│   └── collector/
│       ├── __init__.py
│       ├── auth.py
│       ├── kafka_producer.py
│       ├── main.py
│       ├── opensky_client.py
│       └── transformer.py
│
├── databricks/
│   ├── resources/
│   │   ├── analytics_pipeline.yml
│   │   ├── kafka_pipeline.yml
│   │   └── ...
│   │
│   └── src/
│       └── analytics/
│           └── flight_analytics.py
│
├── data/
│   └── samples/
│
├── tests/
│   ├── test_auth.py
│   ├── test_kafka_producer.py
│   ├── test_opensky_client.py
│   └── test_transformer.py
│
├── .env.example
├── .gitignore
├── databricks.yml
├── requirements.txt
└── README.md
```

---

# Running the Project

## 1. Clone the Repository

```bash
git clone https://github.com/jithin99/flight-data-engineering.git

cd flight-data-engineering
```

---

## 2. Create a Virtual Environment

```bash
python3 -m venv .venv

source .venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Create a `.env` file based on:

```text
.env.example
```

Configure your own OpenSky and Kafka credentials.

Example variable names:

```env
OPENSKY_CLIENT_ID=your_client_id
OPENSKY_CLIENT_SECRET=your_client_secret
OPENSKY_POLL_INTERVAL_SECONDS=90

KAFKA_BOOTSTRAP_SERVERS=your_bootstrap_server
KAFKA_TOPIC=flights
KAFKA_API_KEY=your_api_key
KAFKA_API_SECRET=your_api_secret
```

> **Never commit the `.env` file or real credentials to GitHub.**

---

## 5. Start the Collector

Run:

```bash
python src/collector/main.py
```

The collector will:

```text
Authenticate with OpenSky
        ↓
Fetch aircraft states
        ↓
Transform aircraft records
        ↓
Publish events to Kafka
        ↓
Wait for polling interval
        ↓
Repeat
```

---

# Databricks Deployment

The Databricks resources are managed using bundle configuration.

Authenticate with Databricks and validate the project:

```bash
databricks bundle validate -t dev
```

Deploy:

```bash
databricks bundle deploy -t dev
```

The deployed architecture processes:

```text
Kafka
  ↓
Bronze
  ↓
Silver
  ↓
Gold
```

---

# Testing

Unit tests cover the main Python ingestion components, including:

- OpenSky authentication
- OpenSky API client
- Aircraft event transformation
- Kafka producer

Run the tests with:

```bash
pytest
```

---

# Security

No credentials are intentionally stored in the repository.

Sensitive values such as:

```text
OpenSky Client ID
OpenSky Client Secret
Kafka API Key
Kafka API Secret
```

are provided through environment variables.

The local `.env` file is excluded using `.gitignore`.

Only placeholder values should be included in `.env.example`.

---

# Key Engineering Decisions

## Why separate the API collector from Databricks?

The OpenSky API and Databricks serve different responsibilities.

The Python collector handles external API communication while Kafka provides a streaming boundary between ingestion and processing.

This avoids tightly coupling Databricks to the external REST API.

---

## Why Bronze, Silver and Gold?

Each layer has a clear responsibility.

```text
Bronze
Raw events
   ↓
Silver
Cleaned + validated events
   ↓
Gold
Analytics-ready datasets
```

Keeping these responsibilities separate makes the pipeline easier to understand, debug and extend.

---

## Why Declarative Pipelines?

One of the main goals of this project was to explore **Lakeflow Declarative Pipelines**.

Instead of manually orchestrating every transformation, datasets and their dependencies are declared and Databricks manages the resulting dependency graph.

This provided a natural way to work with:

- Streaming tables
- Materialized views
- Data quality expectations
- Incremental processing
- Pipeline lineage
- Watermarking
- Deduplication

---

# What I Learned

Building this project helped me understand that a real-time pipeline is much more than continuously moving data from one system to another.

I worked with the complete flow:

```text
External API
     ↓
Authentication
     ↓
Python Ingestion
     ↓
Kafka
     ↓
Streaming Processing
     ↓
Data Quality
     ↓
Lakehouse
     ↓
Analytical Data Modeling
     ↓
Dashboard
```

Some of the main concepts I explored were:

- REST API ingestion
- OAuth2 authentication
- Kafka producers and topics
- Streaming ingestion
- Bronze/Silver/Gold architecture
- PySpark
- Delta Lake
- Unity Catalog
- Lakeflow Declarative Pipelines
- Streaming tables
- Materialized views
- Data quality expectations
- Event-time processing
- Watermarking
- Deduplication
- Gold-layer data modeling
- Databricks dashboards
- AI-assisted dashboard development with Genie
- Databricks Asset Bundles
- Serverless compute
- Git-based development

The biggest takeaway was understanding why each component exists and keeping ingestion, transport, transformation and analytics as separate responsibilities.

---

# Future Improvements

There are several directions in which this project could be extended:

- Regional flight-density analytics
- Route and trajectory analysis
- Historical flight trend analysis
- Aircraft anomaly detection
- More sophisticated late-data handling
- Streaming alerts
- Additional aviation data sources
- CI/CD automation
- Pipeline observability and monitoring
- Longer-term historical storage
- Additional Gold models

---

# Project Status

**Core end-to-end pipeline completed.**

Current implementation:

```text
OpenSky Network
       ↓
Python Collector
       ↓
Apache Kafka / Confluent Cloud
       ↓
Databricks Bronze
       ↓
Databricks Silver
       ↓
Databricks Gold
       ↓
Databricks Dashboard
```

The goal of this project was not just to create a visualization of flight data.

The main focus was understanding and implementing the **data engineering architecture behind a real-time analytics system**.

<img width="525" height="272" alt="image" src="https://github.com/user-attachments/assets/f049fc75-abf7-45e2-9308-1a86cae3c7d6" />
<img width="1556" height="853" alt="image" src="https://github.com/user-attachments/assets/435d160d-d87b-41ba-aeb7-9aec791937b8" />
<img width="1556" height="853" alt="image" src="https://github.com/user-attachments/assets/775435ce-e044-46c3-a928-cf0da4af1104" />
<img width="1556" height="853" alt="image" src="https://github.com/user-attachments/assets/919479f3-7cb6-44aa-83e3-23f70395cfb1" />



