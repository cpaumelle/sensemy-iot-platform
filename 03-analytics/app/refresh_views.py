#!/usr/bin/env python3
"""
Analytics Materialized View Refresh Script
Version: 1.0.0 - 2025-08-26 22:20:00 UTC
Authors: SenseMy IoT Team

Refreshes materialized views to pick up new processed uplinks from transform service.
Runs every 15 minutes to keep analytics current with latest data.
"""

import sys
from datetime import datetime
from database.connections import get_sync_db_session

def refresh_materialized_views():
    print(f"[{datetime.now().isoformat()}] Starting materialized view refresh...")
    
    try:
        db = next(get_sync_db_session())
        
        views_to_refresh = [
            'analytics.people_counting_hourly',
            'analytics.environmental_hourly', 
            'analytics.environmental_latest',
            'analytics.device_health_latest'
        ]
        
        refreshed = 0
        for view_name in views_to_refresh:
            try:
                print(f"  Refreshing {view_name}...")
                start_time = datetime.now()
                db.execute(f"REFRESH MATERIALIZED VIEW {view_name}")
                db.commit()
                elapsed = (datetime.now() - start_time).total_seconds()
                print(f"  Refreshed {view_name} in {elapsed:.2f}s")
                refreshed += 1
            except Exception as e:
                print(f"  Failed to refresh {view_name}: {str(e)}")
                continue
        
        print(f"[{datetime.now().isoformat()}] Refresh completed: {refreshed}/{len(views_to_refresh)} views updated")
        return refreshed == len(views_to_refresh)
        
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] Database connection failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    success = refresh_materialized_views()
    sys.exit(0 if success else 1)
