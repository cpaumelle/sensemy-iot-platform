# SenseMy IoT Platform — v4 Pipeline

📦 **Repository:** `v4-iot-pipeline`  
🕒 **Last Updated:** 2025-07-11 13:20 UTC  
👤 **Maintainer:** Charles Paumelle

---

## 📁 Directory Structure

```
v4-iot-pipeline/
├── .env.v4                     # Environment variables for v4 pipeline
├── docker-compose.v4.yml      # Compose file for all services
├── Caddyfile                  # Caddy reverse proxy config
├── tools/                     # Utility scripts
│   ├── 1-validate-and-up.sh
│   ├── 2-shutdown-v4-clean.sh
│   └── 3-clean-volumes-v4.sh
├── 01-ingest-server/
│   ├── app/
│   ├── schema/
│   └── initdb/
├── 02-device-manager/
│   ├── app/
│   ├── schema/
│   └── initdb/
├── 03-analytics-alerts/
│   ├── app/
│   ├── schema/
│   └── initdb/
└── tools/adminer-custom/      # Custom Adminer UI
```

---

## 🚀 Services Deployed

| Service             | Description                              | Port (Host → Container) |
|---------------------|------------------------------------------|--------------------------|
| Ingest Server       | FastAPI app for uplink ingestion         | 8100 → 8000              |
| Device Manager      | FastAPI app for device metadata          | 9100 → 9000              |
| Analytics Alerts    | FastAPI app for processing alerts        | 7100 → 7000              |
| Ingest DB           | PostgreSQL database for raw uplinks      | 5543 → 5432              |
| Device DB           | PostgreSQL database for device data      | 5544 → 5432              |
| Analytics DB        | PostgreSQL for analytics pipeline        | 5545 → 5432              |
| Adminer UI          | DB web interface                         | 8180 → 8080              |
| Caddy Proxy         | HTTPS reverse proxy                      | 8443 → 443, 8088 → 80    |

---

## 🌐 Networks

- `sensemy_network` (v4 stack)
- `charliehub_net` (shared external services)

---

## 📌 What’s Done

- ✅ Fully validated `.env.v4` file with port conflict checking
- ✅ Working `docker-compose.v4.yml` with all services
- ✅ Adminer UI integrated with `.env.v4`
- ✅ Startup and shutdown scripts in `tools/`
- ✅ SSH key configured for GitHub push

---

## 🔧 Still to Build / Integrate

- [ ] Complete unpacker framework inside `01-ingest-server/app/`
- [ ] Uplink forwarding logic from ingest → device manager
- [ ] Analytics rule processing
- [ ] Daily/real-time device twinning sync
- [ ] Optional: Filebrowser container (on hold)

---

## 📝 How to Start

```bash
cd ~/v4-iot-pipeline/tools
./1-validate-and-up.sh
```

To shut down the stack:

```bash
./2-shutdown-v4-clean.sh
```

To remove volumes (⚠️ Destroys data):

```bash
./3-clean-volumes-v4.sh
```

---

© SenseMy / CharlieHub — 2025
