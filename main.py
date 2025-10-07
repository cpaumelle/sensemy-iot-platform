# main.py - Ingest Server with Actility + Netmore Support  
# Version: 0.5.2 - 2025-07-20 13:50 UTC  
# Changelog:  
# - Fixed crash when Netmore sends array of uplinks  
# - Ensures actility ingest remains untouched  

from fastapi import FastAPI, HTTPException, Request
import os, json, logging
from datetime import datetime
from dateutil.parser import isoparse
import psycopg2
from fastapi.middleware.cors import CORSMiddleware

from forwarders.transform_forwarder import forward_to_transform

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Env vars
DB_HOST = os.getenv("INGEST_DB_HOST", "localhost")
DB_PORT = os.getenv("INGEST_DB_INTERNAL_PORT", "5432")
DB_NAME = os.getenv("INGEST_DB_NAME", "ingest_db")
DB_USER = os.getenv("INGEST_DB_USER", "ingestuser")
DB_PASS = os.getenv("INGEST_DB_PASSWORD", "secret")

def get_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT,
        dbname=DB_NAME, user=DB_USER, password=DB_PASS
    )

@app.post("/uplink")
async def receive_uplink(req: Request):
    try:
        source = req.query_params.get("source", "").lower()
        body = await req.body()
        logger.info(f"🛰️  Incoming request on /uplink from source={source or 'unknown'}: {body}")
        parsed = json.loads(body.decode("utf-8")) if body else {}

        # Handle Netmore array payloads
        if isinstance(parsed, list):
            logger.warning("⚠️ Netmore sent array of uplinks. Using first item only.")
            parsed = parsed[0]

        created_at = datetime.utcnow()
        uplink = {}
        deveui = None
        payload_hex = None
        raw_ts = None

        # Auto-detect source if not passed
        if not source:
            if "DevEUI_uplink" in parsed:
                source = "actility"
            elif "devEui" in parsed:
                source = "netmore"

        # Identify source and extract values
        if source == "actility" or ("DevEUI_uplink" in parsed):
            uplink = parsed.get("DevEUI_uplink", {})
            deveui = uplink.get("DevEUI")
            payload_hex = uplink.get("payload_hex")
            raw_ts = uplink.get("Time")

        elif source == "netmore" or ("devEui" in parsed):
            uplink = parsed
            deveui = uplink.get("devEui")
            payload_hex = uplink.get("payload")
            raw_ts = uplink.get("timestamp")

        # Robust timestamp parsing
        try:
            received_at = isoparse(raw_ts) if raw_ts else created_at
        except Exception:
            received_at = created_at

        if not deveui:
            raise ValueError("Missing DevEUI in payload")

        # Insert into DB
        try:
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO ingest.raw_uplinks (deveui, received_at, fport, payload, uplink_metadata, source)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING uplink_id
                    """, (
                        deveui,
                        received_at,
                        uplink.get("FPort") or uplink.get("fPort"),
                        payload_hex,
                        json.dumps(parsed),
                        source
                    ))
                    ingest_id = cur.fetchone()[0]
                    conn.commit()
        except Exception as e:
            logger.error(f"❌ DB insert failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Database insert error: {e}")

        # Construct forwarding payload
        forward_payload = {
            "deveui": deveui,
            "received_at": received_at.isoformat(),
            "fport": uplink.get("FPort") or uplink.get("fPort"),
            "payload": payload_hex,
            "uplink_metadata": parsed,
            "source": source,
            "ingest_id": ingest_id
        }

        logger.info(f"📤 Forwarding to Transform: {json.dumps(forward_payload, indent=2)}")

        # Only forward to Transform
        await forward_to_transform(forward_payload)

        logger.info(f"✔️ Stored and forwarded uplink for {deveui}")
        return {"status": "stored-and-forwarded", "deveui": deveui}

    except Exception as e:
        logger.error(f"Unhandled error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok"}
