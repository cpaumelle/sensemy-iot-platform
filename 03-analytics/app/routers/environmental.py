# routers/environmental.py - Analytics
# Version: 2.0.0 - 2025-08-11 23:30:00 UTC
# Enhanced with metric-specific filtering and sensor capabilities
# Added endpoints for environmental analytics dashboard implementation

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, distinct, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from database.connections import get_sync_db_session
from models import EnvironmentalHourly, EnvironmentalLatest, DeviceHealthLatest, DataDictionary

router = APIRouter(tags=["Environmental Analytics"])

# ═══════════════════════════════════════════════════════════════════
# EXISTING ENDPOINTS (PRESERVED)
# ═══════════════════════════════════════════════════════════════════

@router.get("/latest", response_model=List[dict])
def get_environmental_latest(
    deveui: Optional[str] = Query(None, description="Filter by specific device EUI"),
    device_type_id: Optional[int] = Query(None, description="Filter by device type"),
    site_id: Optional[str] = Query(None, description="Filter by site"),
    status: Optional[str] = Query(None, description="Filter by environmental status"),
    limit: int = Query(50, description="Maximum number of results"),
    db: Session = Depends(get_sync_db_session)
):
    """
    Get latest environmental readings from all environmental sensors

    Uses data-dictionary-driven normalization for consistent units and precision.
    Separates environmental data (temp/humidity/CO2) from device health.
    """
    query = db.query(EnvironmentalLatest)

    # Apply filters
    if deveui:
        query = query.filter(EnvironmentalLatest.deveui == deveui)
    if device_type_id:
        query = query.filter(EnvironmentalLatest.device_type_id == device_type_id)
    if site_id:
        query = query.filter(EnvironmentalLatest.site_id == site_id)
    if status:
        query = query.filter(EnvironmentalLatest.environmental_status == status)

    # Order by most recent first
    results = query.order_by(desc(EnvironmentalLatest.timestamp)).limit(limit).all()

    return [result.as_dict() for result in results]

@router.get("/hourly", response_model=List[dict])
def get_environmental_hourly(
    deveui: Optional[str] = Query(None, description="Filter by specific device EUI"),
    device_type_id: Optional[int] = Query(None, description="Filter by device type"),
    site_id: Optional[str] = Query(None, description="Filter by site"),
    hours: int = Query(24, description="Number of hours to retrieve (default 24)"),
    limit: int = Query(100, description="Maximum number of results"),
    db: Session = Depends(get_sync_db_session)
):
    """
    Get hourly aggregated environmental data

    Returns temperature, humidity, and CO2 aggregations (min/avg/max) per hour.
    Uses data-dictionary-driven field mapping and units.
    """
    # Calculate time window
    since_time = datetime.utcnow() - timedelta(hours=hours)

    query = db.query(EnvironmentalHourly).filter(
        EnvironmentalHourly.hour_bucket >= since_time
    )

    # Apply filters
    if deveui:
        query = query.filter(EnvironmentalHourly.deveui == deveui)
    if device_type_id:
        query = query.filter(EnvironmentalHourly.device_type_id == device_type_id)
    if site_id:
        query = query.filter(EnvironmentalHourly.site_id == site_id)

    # Order by time and device
    results = query.order_by(
        desc(EnvironmentalHourly.hour_bucket),
        asc(EnvironmentalHourly.deveui)
    ).limit(limit).all()

    return [result.as_dict() for result in results]

@router.get("/health", response_model=List[dict])
def get_device_health(
    deveui: Optional[str] = Query(None, description="Filter by specific device EUI"),
    device_type_id: Optional[int] = Query(None, description="Filter by device type"),
    health_status: Optional[str] = Query(None, description="Filter by overall health status"),
    battery_status: Optional[str] = Query(None, description="Filter by battery status"),
    limit: int = Query(50, description="Maximum number of results"),
    db: Session = Depends(get_sync_db_session)
):
    """
    Get device health status (battery, connectivity, overall health)

    Separated from environmental data following the established pattern.
    Uses device_type_thresholds for battery level assessment.
    """
    query = db.query(DeviceHealthLatest)

    # Apply filters
    if deveui:
        query = query.filter(DeviceHealthLatest.deveui == deveui)
    if device_type_id:
        query = query.filter(DeviceHealthLatest.device_type_id == device_type_id)
    if health_status:
        query = query.filter(DeviceHealthLatest.overall_health == health_status)
    if battery_status:
        query = query.filter(DeviceHealthLatest.battery_status == battery_status)

    # Order by health status (critical first) then by device
    results = query.order_by(
        DeviceHealthLatest.overall_health.desc(),  # critical > warning > healthy
        asc(DeviceHealthLatest.deveui)
    ).limit(limit).all()

    return [result.as_dict() for result in results]

@router.get("/devices/types", response_model=List[dict])
def get_environmental_device_types(
    db: Session = Depends(get_sync_db_session)
):
    """Get environmental device types with their data dictionary fields"""
    # Get environmental device types from latest readings
    device_types = db.query(
        EnvironmentalLatest.device_type_id,
        EnvironmentalLatest.device_type
    ).distinct().all()

    result = []
    for device_type_id, device_type in device_types:
        # Get data dictionary fields for this device type
        fields = db.query(DataDictionary).filter(
            DataDictionary.device_type_id == device_type_id,
            DataDictionary.field_name.in_(['temperature', 'humidity', 'co2_ppm'])
        ).all()

        # Count devices of this type
        device_count = db.query(EnvironmentalLatest).filter(
            EnvironmentalLatest.device_type_id == device_type_id
        ).count()

        result.append({
            "device_type_id": device_type_id,
            "device_type": device_type,
            "device_count": device_count,
            "supported_fields": [field.as_dict() for field in fields]
        })

    return result

# ═══════════════════════════════════════════════════════════════════
# NEW ENDPOINTS FOR ENVIRONMENTAL ANALYTICS DASHBOARD
# ═══════════════════════════════════════════════════════════════════

@router.get("/metrics/temperature", response_model=List[dict])
def get_temperature_data(
    device_type_ids: Optional[str] = Query(None, description="Comma-separated device type IDs (e.g., '1,2,4')"),
    devices: Optional[str] = Query(None, description="Comma-separated device EUIs for comparison"),
    hours: int = Query(24, description="Hours of historical data"),
    limit: int = Query(100, description="Maximum number of results"),
    db: Session = Depends(get_sync_db_session)
):
    """
    Get temperature-specific data for metric-first navigation
    
    Returns only devices that support temperature readings with standardized units.
    Supports multi-device comparison for the same metric.
    """
    query = db.query(EnvironmentalLatest).filter(
        EnvironmentalLatest.temperature.is_not(None)
    )
    
    # Filter by device types if provided
    if device_type_ids:
        type_ids = [int(tid.strip()) for tid in device_type_ids.split(',')]
        query = query.filter(EnvironmentalLatest.device_type_id.in_(type_ids))
    
    # Filter by specific devices if provided
    if devices:
        device_list = [dev.strip() for dev in devices.split(',')]
        query = query.filter(EnvironmentalLatest.deveui.in_(device_list))
    
    results = query.order_by(desc(EnvironmentalLatest.timestamp)).limit(limit).all()
    
    return [result.as_dict() for result in results]

@router.get("/metrics/humidity", response_model=List[dict])
def get_humidity_data(
    device_type_ids: Optional[str] = Query(None, description="Comma-separated device type IDs (e.g., '1,2,4')"),
    devices: Optional[str] = Query(None, description="Comma-separated device EUIs for comparison"),
    hours: int = Query(24, description="Hours of historical data"),
    limit: int = Query(100, description="Maximum number of results"),
    db: Session = Depends(get_sync_db_session)
):
    """
    Get humidity-specific data for metric-first navigation
    
    Returns only devices that support humidity readings with standardized units.
    """
    query = db.query(EnvironmentalLatest).filter(
        EnvironmentalLatest.humidity.is_not(None)
    )
    
    # Filter by device types if provided
    if device_type_ids:
        type_ids = [int(tid.strip()) for tid in device_type_ids.split(',')]
        query = query.filter(EnvironmentalLatest.device_type_id.in_(type_ids))
    
    # Filter by specific devices if provided
    if devices:
        device_list = [dev.strip() for dev in devices.split(',')]
        query = query.filter(EnvironmentalLatest.deveui.in_(device_list))
    
    results = query.order_by(desc(EnvironmentalLatest.timestamp)).limit(limit).all()
    
    return [result.as_dict() for result in results]

@router.get("/metrics/co2", response_model=List[dict])
def get_co2_data(
    device_type_ids: Optional[str] = Query(None, description="Comma-separated device type IDs (e.g., '2')"),
    devices: Optional[str] = Query(None, description="Comma-separated device EUIs for comparison"),
    hours: int = Query(24, description="Hours of historical data"),
    limit: int = Query(100, description="Maximum number of results"),
    db: Session = Depends(get_sync_db_session)
):
    """
    Get CO2-specific data for metric-first navigation
    
    Returns only devices that support CO2 readings (typically only Milesight AM103).
    Limited sensor coverage (1/14 devices).
    """
    query = db.query(EnvironmentalLatest).filter(
        EnvironmentalLatest.co2_ppm.is_not(None)
    )
    
    # Filter by device types if provided
    if device_type_ids:
        type_ids = [int(tid.strip()) for tid in device_type_ids.split(',')]
        query = query.filter(EnvironmentalLatest.device_type_id.in_(type_ids))
    
    # Filter by specific devices if provided
    if devices:
        device_list = [dev.strip() for dev in devices.split(',')]
        query = query.filter(EnvironmentalLatest.deveui.in_(device_list))
    
    results = query.order_by(desc(EnvironmentalLatest.timestamp)).limit(limit).all()
    
    return [result.as_dict() for result in results]

@router.get("/sensors/capabilities", response_model=Dict[str, Any])
def get_sensor_capabilities(
    db: Session = Depends(get_sync_db_session)
):
    """
    Sensor capability discovery for metric-first navigation
    
    Returns count of sensors supporting each metric type.
    Used by frontend to show metric availability (e.g., "🌡️ Temperature (14)")
    """
    # Count sensors by capability
    temp_count = db.query(EnvironmentalLatest).filter(
        EnvironmentalLatest.temperature.is_not(None)
    ).count()
    
    humidity_count = db.query(EnvironmentalLatest).filter(
        EnvironmentalLatest.humidity.is_not(None)
    ).count()
    
    co2_count = db.query(EnvironmentalLatest).filter(
        EnvironmentalLatest.co2_ppm.is_not(None)
    ).count()
    
    # Get device type breakdown
    device_types = db.query(
        EnvironmentalLatest.device_type_id,
        EnvironmentalLatest.device_type,
        func.count(EnvironmentalLatest.deveui).label('device_count')
    ).group_by(
        EnvironmentalLatest.device_type_id,
        EnvironmentalLatest.device_type
    ).all()
    
    return {
        "capabilities": {
            "temperature": {
                "sensor_count": temp_count,
                "coverage_percent": round((temp_count / 14) * 100, 1),
                "compatible_device_types": [1, 2, 4],  # All environmental sensors
                "ashrae_standard": {"min": 20, "max": 25, "unit": "°C"}
            },
            "humidity": {
                "sensor_count": humidity_count,
                "coverage_percent": round((humidity_count / 14) * 100, 1),
                "compatible_device_types": [1, 2, 4],  # All environmental sensors
                "ashrae_standard": {"min": 40, "max": 60, "unit": "%"}
            },
            "co2": {
                "sensor_count": co2_count,
                "coverage_percent": round((co2_count / 14) * 100, 1),
                "compatible_device_types": [2],  # Only Milesight AM103
                "ashrae_standard": {"max": 1000, "unit": "ppm"}
            }
        },
        "device_type_breakdown": [
            {
                "device_type_id": dt_id,
                "device_type": dt_name,
                "device_count": dt_count,
                "supports_temperature": dt_id in [1, 2, 4],
                "supports_humidity": dt_id in [1, 2, 4],
                "supports_co2": dt_id in [2]
            }
            for dt_id, dt_name, dt_count in device_types
        ],
        "total_environmental_sensors": sum([dt_count for _, _, dt_count in device_types])
    }

@router.get("/metrics/compare", response_model=Dict[str, Any])
def compare_environmental_metrics(
    metric: str = Query(..., description="Metric to compare (temperature, humidity, co2)"),
    devices: str = Query(..., description="Comma-separated device EUIs to compare"),
    hours: int = Query(24, description="Hours of historical data for comparison"),
    db: Session = Depends(get_sync_db_session)
):
    """
    Multi-location environmental comparison for same metric
    
    Compares the same environmental metric across multiple devices/locations.
    Used for side-by-side location analysis.
    """
    device_list = [dev.strip() for dev in devices.split(',')]
    since_time = datetime.utcnow() - timedelta(hours=hours)
    
    if metric not in ['temperature', 'humidity', 'co2']:
        raise HTTPException(status_code=400, detail="Invalid metric. Use: temperature, humidity, co2")
    
    # Get historical data for comparison
    query = db.query(EnvironmentalHourly).filter(
        EnvironmentalHourly.deveui.in_(device_list),
        EnvironmentalHourly.hour_bucket >= since_time
    )
    
    results = query.order_by(
        EnvironmentalHourly.hour_bucket.desc(),
        EnvironmentalHourly.deveui
    ).all()
    
    # Structure data for chart consumption
    comparison_data = {}
    for result in results:
        device_key = f"{result.deveui}_{result.device_name or 'Unknown'}"
        if device_key not in comparison_data:
            comparison_data[device_key] = []
        
        # Extract metric value based on requested metric
        metric_value = None
        if metric == 'temperature' and result.avg_temperature is not None:
            metric_value = result.avg_temperature
        elif metric == 'humidity' and result.avg_humidity is not None:
            metric_value = result.avg_humidity
        elif metric == 'co2' and result.avg_co2_ppm is not None:
            metric_value = result.avg_co2_ppm
        
        if metric_value is not None:
            comparison_data[device_key].append({
                "timestamp": result.hour_bucket.isoformat(),
                "value": metric_value,
                "hour_bucket": result.hour_bucket.isoformat()
            })
    
    return {
        "metric": metric,
        "devices_compared": len(device_list),
        "hours_analyzed": hours,
        "comparison_data": comparison_data,
        "ashrae_standard": _get_ashrae_standard(metric)
    }

def _get_ashrae_standard(metric: str) -> Dict[str, Any]:
    """Helper function to get ASHRAE standards for environmental metrics"""
    standards = {
        "temperature": {"min": 20, "max": 25, "unit": "°C", "comfort_range": "20-25°C"},
        "humidity": {"min": 40, "max": 60, "unit": "%", "comfort_range": "40-60%"},
        "co2": {"max": 1000, "unit": "ppm", "comfort_range": "<1000ppm"}
    }
    return standards.get(metric, {})

# ═══════════════════════════════════════════════════════════════════
# PRESERVED EXISTING ENDPOINTS (Individual device endpoints)
# ═══════════════════════════════════════════════════════════════════

@router.get("/latest/{deveui}", response_model=dict)
def get_device_environmental_latest(
    deveui: str,
    db: Session = Depends(get_sync_db_session)
):
    """Get latest environmental reading for specific device"""
    result = db.query(EnvironmentalLatest).filter_by(deveui=deveui).first()
    if not result:
        raise HTTPException(status_code=404, detail=f"No environmental data found for device {deveui}")
    return result.as_dict()

@router.get("/hourly/{deveui}", response_model=List[dict])
def get_device_environmental_hourly(
    deveui: str,
    hours: int = Query(24, description="Number of hours to retrieve"),
    db: Session = Depends(get_sync_db_session)
):
    """Get hourly environmental aggregations for specific device"""
    since_time = datetime.utcnow() - timedelta(hours=hours)

    results = db.query(EnvironmentalHourly).filter(
        EnvironmentalHourly.deveui == deveui,
        EnvironmentalHourly.hour_bucket >= since_time
    ).order_by(desc(EnvironmentalHourly.hour_bucket)).all()

    if not results:
        raise HTTPException(status_code=404, detail=f"No hourly environmental data found for device {deveui}")

    return [result.as_dict() for result in results]

@router.get("/health/{deveui}", response_model=dict)
def get_device_health_status(
    deveui: str,
    db: Session = Depends(get_sync_db_session)
):
    """Get health status for specific device"""
    result = db.query(DeviceHealthLatest).filter_by(deveui=deveui).first()
    if not result:
        raise HTTPException(status_code=404, detail=f"No health data found for device {deveui}")
    return result.as_dict()

@router.get("/summary", response_model=dict)
def get_environmental_summary(
    site_id: Optional[str] = Query(None, description="Filter by site"),
    db: Session = Depends(get_sync_db_session)
):
    """
    Get environmental summary statistics

    Provides overview of current environmental conditions and device health.
    """
    # Base queries
    env_query = db.query(EnvironmentalLatest)
    health_query = db.query(DeviceHealthLatest)

    if site_id:
        env_query = env_query.filter(EnvironmentalLatest.site_id == site_id)
        health_query = health_query.filter(DeviceHealthLatest.site_id == site_id)

    # Environmental summary
    env_devices = env_query.all()

    # Calculate environmental stats
    temps = [d.temperature for d in env_devices if d.temperature is not None]
    humidity_vals = [d.humidity for d in env_devices if d.humidity is not None]
    co2_vals = [d.co2_ppm for d in env_devices if d.co2_ppm is not None]

    # Health summary
    health_devices = health_query.all()
    health_counts = {}
    battery_counts = {}

    for device in health_devices:
        health_counts[device.overall_health] = health_counts.get(device.overall_health, 0) + 1
        battery_counts[device.battery_status] = battery_counts.get(device.battery_status, 0) + 1

    return {
        "environmental": {
            "total_devices": len(env_devices),
            "temperature": {
                "avg": round(sum(temps) / len(temps), 1) if temps else None,
                "min": min(temps) if temps else None,
                "max": max(temps) if temps else None,
                "unit": "°C"
            },
            "humidity": {
                "avg": round(sum(humidity_vals) / len(humidity_vals), 1) if humidity_vals else None,
                "min": min(humidity_vals) if humidity_vals else None,
                "max": max(humidity_vals) if humidity_vals else None,
                "unit": "%RH"
            },
            "co2": {
                "avg": round(sum(co2_vals) / len(co2_vals), 0) if co2_vals else None,
                "min": min(co2_vals) if co2_vals else None,
                "max": max(co2_vals) if co2_vals else None,
                "unit": "ppm"
            }
        },
        "device_health": {
            "total_devices": len(health_devices),
            "health_status": health_counts,
            "battery_status": battery_counts
        }
    }
