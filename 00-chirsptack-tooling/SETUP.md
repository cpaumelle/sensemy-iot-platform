# Quick Setup Guide

## First Time Setup

1. **Create your .env file:**
   ```bash
   cd /opt/iot-platform/00-gateway-onboarding
   cp .env.example .env
   ```

2. **Get your ChirpStack API key:**
   - Visit: https://chirpstack.sensemy.cloud
   - Login: admin/admin
   - Go to: API Keys → Add API Key
   - Create key with "Admin" permissions
   - Copy the generated key

3. **Edit .env and add your API key:**
   ```bash
   nano .env
   ```

   Change this line:
   ```
   CHIRPSTACK_API_KEY=
   ```

   To:
   ```
   CHIRPSTACK_API_KEY=your-actual-api-key-here
   ```

   Save and exit (Ctrl+X, Y, Enter)

4. **Secure the .env file:**
   ```bash
   chmod 600 .env
   ```

## Running the Script

```bash
./configure-kerlink-gateway.sh
```

You'll be prompted for:
- Gateway IP address
- Gateway root password
- Gateway name (optional - defaults to Kerlink-XXXXXXXX)
- Gateway description (optional)

The script handles everything else automatically!

## Configuration Variables Reference

### .env.example contents:

```bash
# ChirpStack Configuration
CHIRPSTACK_API_KEY=                                         # REQUIRED: Get from ChirpStack UI
CHIRPSTACK_GRPC_SERVER=10.44.1.110:8080                    # VM 110 gRPC endpoint
CHIRPSTACK_WEB_URL=https://chirpstack.sensemy.cloud        # Web UI URL
LNS_WEBSOCKET_URL=wss://chirpstack.sensemy.cloud/api/basicstation  # Gateway connection URL

# Default Gateway Settings
DEFAULT_GATEWAY_NAME_PREFIX=Kerlink                         # Prefix for auto-generated names
GATEWAY_STATS_INTERVAL=30                                   # Stats reporting interval (seconds)

# Script Paths
SCRIPT_DIR=/opt/iot-platform/00-gateway-onboarding
REGISTER_SCRIPT=${SCRIPT_DIR}/chirpstack_register_gateway.py

# Gateway SSH Configuration (optional - will prompt if not set)
# GATEWAY_IP=                                                # Pre-set gateway IP to skip prompt
# GATEWAY_PASSWORD=                                          # Pre-set password (not recommended)
# GATEWAY_DEFAULT_USER=root                                  # SSH username
```

## That's it!

Once configured, you can run the script anytime to onboard new gateways. The API key is stored securely in `.env` and won't need to be entered again.
