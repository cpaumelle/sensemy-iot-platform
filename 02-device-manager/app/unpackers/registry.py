# registry.py – v0.2.0 – 2025-07-10
"""
Device unpacker registry for dynamically resolving unpacker functions
based on device_model string (e.g. "browan_tbwl", "winext_an102c").

Unpacker modules must expose a function: def unpack(payload_hex: str) -> dict
"""

import importlib

# Registry map: device model → unpacker module path
UNPACKER_REGISTRY = {
    # Environment
    "browan_tbhh": "device_manager.app.unpackers.environment.browan_tbhh",
    "browan_tbhv110": "device_manager.app.unpackers.environment.browan_tbhv110",
    "milesight_am103": "device_manager.app.unpackers.environment.milesight_am103",
    "merryiot_co2": "device_manager.app.unpackers.environment.merryiot_co2",

    # Monitoring
    "winext_an102c": "device_manager.app.unpackers.monitoring.winext_an102c",
    "browan_tbdw": "device_manager.app.unpackers.monitoring.browan_tbdw",
    "browan_tbwl": "device_manager.app.unpackers.monitoring.browan_tbwl",

    # Buttons
    "smilio_a": "device_manager.app.unpackers.buttons.smilio_a",
    "smilio_s": "device_manager.app.unpackers.buttons.smilio_s",

    # Network
    "atim_acw_lw8": "device_manager.app.unpackers.network.atim_acw_lw8",
    "netvox_r716": "device_manager.app.unpackers.network.netvox_r716",
}


def get_unpacker(device_model: str):
    """
    Resolves and returns the unpack(payload_hex) function for a given device model.
    Raises ValueError if model not found or unpacker cannot be imported.
    """
    module_path = UNPACKER_REGISTRY.get(device_model.lower())
    if not module_path:
        raise ValueError(f"Unpacker not found for device model '{device_model}'")

    try:
        module = importlib.import_module(module_path)
        return getattr(module, "unpack")
    except (ImportError, AttributeError) as e:
        raise ImportError(f"Error importing unpacker for {device_model}: {e}")
