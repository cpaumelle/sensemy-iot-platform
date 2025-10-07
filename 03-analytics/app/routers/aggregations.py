# routers/aggregations.py - Analytics
# Version: 1.0.0 - 2025-08-09 14:15:00 UTC
# Based on: Transform service router patterns
# CRUD operations for aggregation_patterns table

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from database.connections import get_sync_db_session
from models import AggregationPattern

router = APIRouter(tags=["Aggregation Patterns"])

@router.get("", response_model=List[dict])
def get_aggregation_patterns(db: Session = Depends(get_sync_db_session)):
    """Get all aggregation patterns"""
    patterns = db.query(AggregationPattern).all()
    return [pattern.as_dict() for pattern in patterns]

@router.get("/{pattern_id}", response_model=dict)
def get_aggregation_pattern(pattern_id: int, db: Session = Depends(get_sync_db_session)):
    """Get specific aggregation pattern"""
    pattern = db.query(AggregationPattern).filter_by(pattern_id=pattern_id).first()
    if not pattern:
        raise HTTPException(status_code=404, detail="Aggregation pattern not found")
    return pattern.as_dict()

@router.get("/analytics/occupancy", response_model=List[dict])
def get_occupancy_data(db: Session = Depends(get_sync_db_session)):
    """Get people counting data from materialized view"""
    from models import PeopleCountingHourly
    
    # Get recent occupancy data (last 24 hours)
    result = db.query(PeopleCountingHourly).limit(100).all()
    
    return [{
        "deveui": row.deveui,
        "hour_bucket": row.hour_bucket.isoformat() if row.hour_bucket else None,
        "sum_in": row.sum_in,
        "sum_out": row.sum_out,
        "occupancy": row.occupancy
    } for row in result]
