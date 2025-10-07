# IoT Platform Documentation - VM 113 (Container ID: 113)

**Platform Name:** SenseMy IoT Pipeline
**Version:** 4.0
**Location:** `CT 113 (10.44.1.13) /opt/iot-platform`
**Last Updated:** 2025-10-07
**Documentation Generated:** 2025-10-07

---

## Table of Contents

1. [Platform Overview](#platform-overview)
2. [Architecture](#architecture)
3. [Services](#services)
4. [Network Configuration](#network-configuration)
5. [Database Configuration](#database-configuration)
6. [External Integrations](#external-integrations)
7. [Deployment Details](#deployment-details)
8. [API Endpoints](#api-endpoints)
9. [Monitoring & Health Checks](#monitoring--health-checks)

---

## Platform Overview

The SenseMy IoT Platform is a comprehensive multi-service microservices architecture designed for ingesting, transforming, analyzing, and visualizing IoT sensor data from multiple LoRaWAN Network Servers (LNS).

### Key Features

- Multi-LNS support (Actility, Netmore, The Things Industries, ChirpStack)
- Real-time data ingestion and transformation
- Environmental analytics (temperature, humidity, CO2)
- Device and gateway management
- Location-based hierarchical organization
- Web-based UI frontend

### Technology Stack

- **Backend:** Python 3.11, FastAPI, Uvicorn
- **Frontend:** React/Vite, Nginx
- **Databases:** PostgreSQL (on separate host: 10.44.1.12)
- **Containerization:** Docker, Docker Compose
- **Reverse Proxy:** Traefik (external, managed in separate project)
- **Messaging:** MQTT (for ChirpStack integration)

---

## Architecture

### Service Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     External Networks                           │
│           (Actility, Netmore, TTI, ChirpStack)                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Reverse Proxy                              │
│            (Traefik - External Container)                       │
│   HTTPS Termination, SSL Certs, Domain Routing                │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌──────────────────┐          ┌──────────────────┐
│  sensemy_network │          │  charliehub_net  │
│  (172.18.0.0/16) │          │  (Bridge)        │
└────────┬─────────┘          └──────────────────┘
         │
         │  All services connected to both networks
         │
    ┌────┴────┬─────────┬─────────┬─────────┬──────────┐
    ▼         ▼         ▼         ▼         ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ Ingest │ │Transform│ │Analytics│ │   UI   │ │Adminer │
│Service │ │Service  │ │Service  │ │Frontend│ │   UI   │
│:8100   │ │:9101    │ │:7000    │ │:8801   │ │:8180   │
└───┬────┘ └───┬─────┘ └────┬────┘ └────────┘ └────────┘
    │          │             │
    └──────────┴─────────────┘
               │
               ▼
    ┌──────────────────────┐
    │  PostgreSQL Database │
    │   10.44.1.12:5432   │
    │  - ingest_db        │
    │  - transform_db     │
    │  - microshare_db    │
    └──────────────────────┘
```

### Data Flow

1. **Ingestion:** LoRaWAN uplinks received by Ingest Service from various LNS providers
2. **Storage:** Raw uplinks stored in `ingest_db`
3. **Transformation:** Transform Service processes and normalizes data
4. **Analytics:** Analytics Service provides aggregations and environmental insights
5. **Presentation:** UI Frontend displays dashboards, devices, locations, and gateways

---

## Services

### 1. Ingest Service

**Container:** `ingest-service`
**Image:** `iot-platform-ingest-service`
**Port Mapping:** `8100:8000`
**Network IP:** 172.18.0.2
**Version:** 0.9.0
**Status:** Running (13 hours uptime)

#### Purpose

Receives LoRaWAN uplink messages from multiple network servers and stores them in the ingest database.

#### Supported LNS Providers

- **Actility** (ThingPark)
- **Netmore**
- **The Things Industries (TTI)**
- **ChirpStack** (with MQTT publish capability)

#### Key Features

- Auto-detection of LNS type from payload structure
- Deduplication based on DevEUI + timestamp
- Payload normalization to common schema
- MQTT publishing for ChirpStack integration
- Forwards data to Transform Service

#### API Endpoints

- `POST /uplink?source={lns_type}` - Receive uplink messages

#### Files

- Main: `/opt/iot-platform/01-ingest-server/app/main.py`
- Parsers: `/opt/iot-platform/01-ingest-server/app/parsers/`
  - `actility_parser.py`
  - `netmore_parser.py`
  - `tti_parser.py`
  - `chirpstack_parser.py`
- Forwarders: `/opt/iot-platform/01-ingest-server/app/forwarders/`
  - `transform_forwarder.py`
  - `mqtt_publisher.py`

#### Database

- **Database:** `ingest_db` on 10.44.1.12
- **User:** `iotuser`
- **Tables:** Raw uplink storage with DevEUI, payload, timestamps, metadata

#### External Access

- **Domain:** `https://dev.sensemy.cloud`
- **Webhook URLs:**
  - Actility: `https://dev.sensemy.cloud/uplink?source=actility`
  - Netmore: `https://dev.sensemy.cloud/uplink?source=netmore`

---

### 2. Transform Service

**Container:** `transform-service`
**Image:** `iot-platform-transform-service`
**Port Mapping:** `9101:9001`
**Network IP:** 172.18.0.5
**Version:** 0.1.6
**Status:** Running (6 days uptime)

#### Purpose

Processes raw uplink data, unpacks payloads, maintains device registry, and provides REST API for device/location/gateway management.

#### Key Features

- Payload unpacking using device-type-specific decoders
- Device, location, and gateway CRUD operations
- Hierarchical location tree management
- Gateway configuration management
- CORS-enabled API for frontend

#### API Endpoints (v1)

- `/v1/locations/*` - Location management
- `/v1/devices/*` - Device management
- `/v1/gateways/*` - Gateway management
- `/process-uplink` - Uplink processing
- `/health` - Health check

#### Files

- Main: `/opt/iot-platform/02-transform/app/main.py`
- Routers: `/opt/iot-platform/02-transform/app/routers/`
- Unpackers: `/opt/iot-platform/02-transform/app/unpackers/`
- Services: `/opt/iot-platform/02-transform/app/services/`

#### Database

- **Database:** `transform_db` on 10.44.1.12
- **User:** `iotuser`
- **Tables:** Devices, locations, gateways, processed uplinks

#### External Access

- **Domain:** `https://api3.sensemy.cloud`
- **CORS Origin:** `https://app2.sensemy.cloud`

---

### 3. Analytics Service

**Container:** `analytics-service`
**Image:** `iot-platform-analytics-service`
**Port Mapping:** `7000:7000`
**Network IP:** 172.18.0.7
**Version:** 2.0.0
**Status:** Running (6 days uptime)

#### Purpose

Provides analytics aggregations, environmental monitoring (temperature, humidity, CO2), device health monitoring, and data dictionary normalization.

#### Key Features

- Environmental analytics with hourly/latest data
- Device health monitoring (battery, connectivity)
- Occupancy analytics
- Sensor capability mapping
- Metrics comparison endpoints
- Data dictionary with units and precision

#### API Endpoints (v1)

- `/v1/aggregations/*` - General aggregations
- `/v1/aggregations/analytics/occupancy` - Occupancy data
- `/v1/environment/latest` - Latest environmental readings
- `/v1/environment/hourly` - Hourly averages
- `/v1/environment/health` - Device health metrics
- `/v1/environment/summary` - Summary statistics
- `/v1/environment/metrics/{temperature,humidity,co2}` - Metric-specific endpoints
- `/v1/environment/sensors/capabilities` - Sensor capabilities
- `/v1/environment/metrics/compare` - Metric comparisons
- `/health` - Health check

#### Files

- Main: `/opt/iot-platform/03-analytics/app/main.py`
- Routers: `/opt/iot-platform/03-analytics/app/routers/`
  - `aggregations.py`
  - `environmental.py`

#### Database

- Uses `transform_db` analytics schema on 10.44.1.12

#### External Access

- **Domain:** `https://analytics.sensemy.cloud`
- **CORS Origin:** `https://app2.sensemy.cloud`

---

### 4. UI Frontend

**Container:** `ui-frontend`
**Image:** `iot-platform-ui-frontend`
**Port Mapping:** `8801:80`
**Network IP:** 172.18.0.6
**Version:** 4.0.0
**Status:** Running (6 days uptime, healthy)

#### Purpose

React-based web application providing user interface for device management, location hierarchy, gateway configuration, and analytics visualization.

#### Key Features

- Device listing and management
- Location tree visualization and management
- Gateway configuration
- Analytics dashboards
- Environmental monitoring UI
- Responsive design with Tailwind CSS

#### Technology Stack

- React with Vite
- Tailwind CSS
- Nginx web server
- Read-only container with tmpfs for runtime

#### Files

- Source: `/opt/iot-platform/10-ui-frontend/sensemy-platform/src/`
- Build: `/opt/iot-platform/10-ui-frontend/sensemy-platform/dist/`
- Nginx Config: `/opt/iot-platform/10-ui-frontend/sensemy-platform/nginx.conf`

#### Configuration

- **Environment:** Production
- **API Base:** `https://api3.sensemy.cloud/v1`
- **Static Path:** `/app/src`

#### External Access

- **Domain:** `https://app2.sensemy.cloud`

#### Health Check

- Endpoint: `http://127.0.0.1/healthz`
- Interval: 10s
- Timeout: 3s
- Retries: 5

---

### 5. Adminer UI

**Container:** `adminer-ui`
**Image:** `iot-platform-adminer-ui`
**Port Mapping:** `8180:8080`
**Network IP:** 172.18.0.3
**Status:** Running (6 days uptime)

#### Purpose

Web-based database administration tool (Adminer) for managing PostgreSQL databases.

#### Features

- Database browsing and querying
- Table management
- SQL execution
- Pre-configured connections to ingest and transform databases

#### Files

- Dockerfile: `/opt/iot-platform/88-tools/adminer-custom/Dockerfile`

#### Configuration

- Pre-configured with credentials for `ingest_db` and `transform_db`

#### External Access

- **Domain:** `https://adminer.charliehub.net`

---

## Network Configuration

### Docker Networks

#### 1. sensemy_network

- **Type:** Bridge
- **Subnet:** 172.18.0.0/16
- **Gateway:** 172.18.0.1
- **Purpose:** Primary network for SenseMy IoT services

**Connected Containers:**

- ingest-service (172.18.0.2)
- adminer-ui (172.18.0.3)
- transform-service (172.18.0.5)
- ui-frontend (172.18.0.6)
- analytics-service (172.18.0.7)

#### 2. charliehub_net

- **Type:** Bridge
- **Purpose:** External network for integration with reverse proxy (Traefik)

All services are connected to **both** networks to enable:

- Internal service-to-service communication (sensemy_network)
- External access through reverse proxy (charliehub_net)

### Port Mappings

| Service | Container Port | Host Port | Protocol | External Domain |
| --- | --- | --- | --- | --- |
| Ingest | 8000 | 8100 | HTTP | dev.sensemy.cloud |
| Transform | 9001 | 9101 | HTTP | api3.sensemy.cloud |
| Analytics | 7000 | 7000 | HTTP | analytics.sensemy.cloud |
| UI Frontend | 80  | 8801 | HTTP | app2.sensemy.cloud |
| Adminer | 8080 | 8180 | HTTP | adminer.charliehub.net |

---

## Database Configuration

### PostgreSQL Host

**Server:** `10.44.1.12:5432`
**User:** `iotuser`
**Password:** `secret`

### Databases

#### 1. ingest_db

- **Purpose:** Raw uplink storage from LoRaWAN network servers
- **Used by:** Ingest Service
- **Tables:**
  - Uplinks (deveui, payload, received_at, source, metadata)

#### 2. transform_db

- **Purpose:** Processed data, device registry, location hierarchy, gateway configs
- **Used by:** Transform Service, Analytics Service
- **Schemas/Tables:**
  - Devices
  - Locations (hierarchical)
  - Gateways
  - Processed uplinks
  - Analytics aggregations

#### 3. microshare_db

- **Purpose:** Microshare integration data
- **Used by:** Transform Service (future use)
- **Host:** Same as transform_db (10.44.1.12)

---

## External Integrations

### 1. LoRaWAN Network Servers

#### Actility ThingPark

- **Webhook URL:** `https://dev.sensemy.cloud/uplink?source=actility`
- **Format:** Actility JSON uplink format
- **Parser:** `actility_parser.py`

#### Netmore

- **Webhook URL:** `https://dev.sensemy.cloud/uplink?source=netmore`
- **Format:** Netmore JSON array format
- **Parser:** `netmore_parser.py`

#### The Things Industries (TTI)

- **Webhook URL:** `https://dev.sensemy.cloud/uplink?source=tti`
- **Format:** TTI JSON uplink format
- **Parser:** `tti_parser.py`

#### ChirpStack

- **Webhook URL:** `https://dev.sensemy.cloud/uplink?source=chirpstack`
- **Format:** ChirpStack JSON uplink format
- **Parser:** `chirpstack_parser.py`
- **MQTT Publishing:** Enabled (publishes to `application/{app_id}/device/{dev_eui}/event/up`)
- **Application ID:** `345b028b-9f0a-4c56-910c-6a05dc2dc22f`

### 2. Reverse Proxy (Traefik)

- **Location:** `~/charliehub/reverse-proxy/` (separate project)
- **Purpose:** HTTPS termination, SSL certificates, domain routing
- **Integration:** Via Traefik labels on each service

---

## Deployment Details

### Deployment Method

- **Orchestration:** Docker Compose
- **Compose File:** `/opt/iot-platform/docker-compose.yml`
- **Environment:** `/opt/iot-platform/.env`

### Service Restart Policy

All services configured with `restart: unless-stopped`

### Volume Mounts

- **Ingest Service:**
  
  - `./01-ingest-server/app:/app` (source code)
  - `./01-ingest-server/initdb:/docker-entrypoint-initdb.d`
  - `./01-ingest-server/tools:/app/tools`
- **Transform Service:**
  
  - `./02-transform/app:/app` (source code)
  - `./02-transform/initdb:/docker-entrypoint-initdb.d`
- **Analytics Service:**
  
  - `./03-analytics/app:/app` (source code)
- **UI Frontend:**
  
  - Read-only filesystem with tmpfs for runtime:
    - `/var/run`
    - `/var/cache/nginx`
    - `/var/tmp`

### Build Context

Each service has its own Dockerfile in respective subdirectories:

- `01-ingest-server/Dockerfile`
- `02-transform/Dockerfile`
- `03-analytics/Dockerfile`
- `10-ui-frontend/sensemy-platform/Dockerfile`
- `88-tools/adminer-custom/Dockerfile`

---

## API Endpoints

### Ingest Service (dev.sensemy.cloud)

```
POST /uplink?source={actility|netmore|tti|chirpstack}
  - Receive LoRaWAN uplink messages
  - Auto-detects LNS if source not provided
  - Returns: 200 OK on success
```

### Transform Service (api3.sensemy.cloud)

```
GET  /health
  - Health check

POST /process-uplink
  - Process and transform uplink data

Locations:
GET    /v1/locations
POST   /v1/locations
GET    /v1/locations/{id}
PUT    /v1/locations/{id}
DELETE /v1/locations/{id}

Devices:
GET    /v1/devices
POST   /v1/devices
GET    /v1/devices/{id}
PUT    /v1/devices/{id}
DELETE /v1/devices/{id}

Gateways:
GET    /v1/gateways
POST   /v1/gateways
GET    /v1/gateways/{id}
PUT    /v1/gateways/{id}
DELETE /v1/gateways/{id}
```

### Analytics Service (analytics.sensemy.cloud)

```
GET /health
  - Health check with service info

GET /
  - Service information and endpoint listing

Aggregations:
GET /v1/aggregations/*
GET /v1/aggregations/analytics/occupancy

Environmental:
GET /v1/environment/latest
  - Latest environmental readings

GET /v1/environment/hourly
  - Hourly averages

GET /v1/environment/health
  - Device health metrics (battery, connectivity)

GET /v1/environment/summary
  - Summary statistics

GET /v1/environment/metrics/temperature
GET /v1/environment/metrics/humidity
GET /v1/environment/metrics/co2
  - Metric-specific endpoints

GET /v1/environment/sensors/capabilities
  - Sensor capabilities mapping

GET /v1/environment/metrics/compare
  - Metric comparisons
```

### UI Frontend (app2.sensemy.cloud)

```
GET /healthz
  - Health check endpoint

Static web application serving React SPA
```

---

## Monitoring & Health Checks

### Service Health Endpoints

| Service | Endpoint | Interval | Timeout | Retries |
| --- | --- | --- | --- | --- |
| Ingest | (none) | -   | -   | -   |
| Transform | GET /health | -   | -   | -   |
| Analytics | GET /health | -   | -   | -   |
| UI Frontend | GET /healthz | 10s | 3s  | 5   |
| Adminer | (none) | -   | -   | -   |

### Container Status (as of 2025-10-07)

- **ingest-service:** Up 13 hours
- **transform-service:** Up 6 days
- **analytics-service:** Up 6 days
- **ui-frontend:** Up 6 days (healthy)
- **adminer-ui:** Up 6 days

### System Processes

Running on the host container (CT 113):

- `systemd` (PID 1) - init system
- `containerd` - container runtime
- `dockerd` - Docker daemon
- `cron` - multiple cron daemons for scheduled tasks
- `postfix` - mail server (qmgr, pickup processes)
- `nginx` - web server (4 worker processes)
- `uvicorn` - FastAPI servers (multiple instances)
- `php` - Adminer PHP server
- `python3.11` - Python processes for services

### Logging

- **Level:** INFO (most services), DEBUG (transform-service)
- **Format:** Structured logging with timestamps
- **Configuration:** `PYTHONUNBUFFERED=1` for real-time logging

---

## Environment Variables

### Service Ports

```bash
INGEST_PORT=8100
TRANSFORM_MANAGER_PORT=9101
ANALYTICS_PORT=7000
UI_FRONTEND_PORT=8801
ADMINER_PORT=8180
```

### Database Configuration

```bash
# PostgreSQL Host
INGEST_DB_HOST=10.44.1.12
TRANSFORM_DB_HOST=10.44.1.12

# Ports
INGEST_DB_PORT=5432
INGEST_DB_INTERNAL_PORT=5432
TRANSFORM_DB_PORT=5432
TRANSFORM_DB_INTERNAL_PORT=5432

# Database Names
INGEST_DB_NAME=ingest_db
TRANSFORM_DB_NAME=transform_db
MICROSHARE_DB_NAME=microshare_db

# Credentials
INGEST_DB_USER=iotuser
INGEST_DB_PASSWORD=secret
TRANSFORM_DB_USER=iotuser
TRANSFORM_DB_PASSWORD=secret
MICROSHARE_DB_USER=iotuser
MICROSHARE_DB_PASSWORD=secret
```

### API Domains

```bash
INGEST_RECEIVER_URL_ACTILITY=https://dev.sensemy.cloud/uplink?source=actility
INGEST_RECEIVER_URL_NETMORE=https://dev.sensemy.cloud/uplink?source=netmore
TRANSFORM_API_DOMAIN=https://api3.sensemy.cloud
TRANSFORM_RECEIVER_URL=https://api3.sensemy.cloud/api/transform
ANALYTICS_API_DOMAIN=https://analytics.sensemy.cloud
```

### CORS Configuration

```bash
CORS_ORIGINS=https://app2.sensemy.cloud
```

### ChirpStack Configuration

```bash
CHIRPSTACK_APP_ID=345b028b-9f0a-4c56-910c-6a05dc2dc22f
```

### General Configuration

```bash
NETWORK_NAME=sensemy_network
DOMAIN_ROOT=sensemy.cloud
TLS_EMAIL=admin@sensemy.cloud
UI_ENVIRONMENT=production
TZ=UTC
PYTHONUNBUFFERED=1
LOG_LEVEL=info
ENABLE_FORWARDING=true
ENABLE_TWINNING=true
```

---

## Additional Components

### ChirpStack Tooling

**Location:** `/opt/iot-platform/00-chirsptack-tooling/`

Contains tooling and documentation for ChirpStack integration:

- `SETUP.md` - Setup instructions
- `WEBSOCKET-SETUP.md` - WebSocket configuration
- `README.md` - General documentation

### Tools Directory

**Location:** `/opt/iot-platform/88-tools/`

Contains additional tooling:

- Adminer custom Docker configuration

### Backup Archives

**Location:** `/opt/iot-platform/backup_archives/`

Historical backups of the platform

---

## Data Flow Example

### Uplink Processing Flow

```
1. LoRaWAN Device → LNS (Actility/Netmore/TTI/ChirpStack)

2. LNS → Webhook POST → https://dev.sensemy.cloud/uplink?source=actility

3. Ingest Service:
   - Receives webhook
   - Auto-detects or uses source parameter
   - Parses with appropriate parser
   - Deduplicates (DevEUI + timestamp)
   - Stores in ingest_db
   - Publishes to MQTT (if ChirpStack)
   - Forwards to Transform Service

4. Transform Service:
   - Receives from Ingest
   - Looks up device type
   - Unpacks payload using device-specific decoder
   - Enriches with device/location metadata
   - Stores processed data in transform_db

5. Analytics Service:
   - Reads from transform_db
   - Computes aggregations
   - Provides analytics APIs

6. UI Frontend:
   - Polls Transform API for devices/locations/gateways
   - Polls Analytics API for environmental data
   - Displays in React dashboard
```

---

## File Structure Summary

```
/opt/iot-platform/
├── .env                          # Environment variables
├── docker-compose.yml            # Docker Compose orchestration
├── 00-chirsptack-tooling/        # ChirpStack integration tools
├── 01-ingest-server/             # Ingest Service
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── parsers/
│   │   └── forwarders/
│   ├── initdb/                   # Database initialization
│   └── tools/
├── 02-transform/                 # Transform Service
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/
│   │   ├── services/
│   │   ├── unpackers/
│   │   └── database/
│   └── initdb/
├── 03-analytics/                 # Analytics Service
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── entrypoint.sh
│   ├── cronjobs.txt
│   ├── app/
│   │   ├── main.py
│   │   └── routers/
│   └── schema/
├── 05-wmc-gateway-scanner/       # WMC Gateway Scanner (disabled)
├── 10-ui-frontend/               # UI Frontend
│   └── sensemy-platform/
│       ├── Dockerfile
│       ├── nginx.conf
│       ├── package.json
│       ├── vite.config.js
│       ├── src/
│       └── dist/
├── 88-tools/                     # Additional tools
│   └── adminer-custom/
├── 99-docs/                      # Documentation (empty)
└── backup_archives/              # Backups
```

---

## Version History

### Platform Version 4.0.0

- Multi-service microservices architecture
- Multi-LNS support (Actility, Netmore, TTI, ChirpStack)
- React-based UI with Tailwind CSS
- Environmental analytics
- Docker Compose deployment

### Recent Updates

- **2025-10-06:** Added MQTT publishing for ChirpStack (Ingest v0.9.0)
- **2025-08-28:** Docker Compose configuration updates
- **2025-08-26:** Analytics service enhancements
- **2025-08-11:** Analytics v2.0.0 with environmental features
- **2025-08-09:** UI enhancements and responsive design
- **2025-08-03:** Transform service CORS configuration

---

## Contact & Support

### Platform Maintainers

- **Email:** admin@sensemy.cloud
- **Organization:** SenseMy IoT Team

### External Services

- **Reverse Proxy Project:** `~/charliehub/reverse-proxy/`
- **Platform Location:** VM 113, `/opt/iot-platform`

---

## Notes

1. **Database Server:** All PostgreSQL databases are hosted externally on `10.44.1.12`, not within the container.
  
2. **Reverse Proxy:** HTTPS termination and SSL certificates are managed by a separate Traefik instance defined in `~/charliehub/reverse-proxy/`.
  
3. **Security:** Database credentials are stored in plaintext in `.env` file. Consider using secrets management in production.
  
4. **ChirpStack MQTT:** MQTT client is initialized in the Ingest Service for publishing uplinks to ChirpStack topics.
  
5. **WMC Gateway Scanner:** Service exists in codebase (`05-wmc-gateway-scanner/`) but is not currently deployed in docker-compose.yml.
  
6. **Backup Strategy:** Backup archives are stored in `/opt/iot-platform/backup_archives/`. Regular backup schedule should be documented.
  
7. **Monitoring:** Consider implementing centralized logging (e.g., ELK stack) and metrics collection (e.g., Prometheus/Grafana) for production monitoring.
  

---

**End of Documentation**
