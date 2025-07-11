# merryiot_co2.py.py – v0.1.0 – 2025-07-11 07:15 UTC
"""
LoRaWAN payload unpacker for Merryiot Co2.
"""

def unpack(payload_hex: str) -> dict:
    """
    Decodes a hex payload into structured sensor data.

    Args:
        payload_hex (str): Hex-encoded payload string.

    Returns:
        dict: Decoded payload data.
    """
    return {
        "status": "unpacked (placeholder)",
        "input": payload_hex
    }

