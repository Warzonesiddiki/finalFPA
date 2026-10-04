
"""
Pilot Workspace Initialization Script (GATE-13)

This script enforces a hermetic environment for Phase 1 Real-Data Pilot.
It ensures that the workspace directory is local (non-synced) and
authorizes the path for the real data ingestion engine.
"""

import os
import sys
from pathlib import Path

# Enforce local workspace directory (must not be in OneDrive/Sync paths)
def enforce_hermetic_env():
    # Attempt to detect common sync path patterns
    sync_tags = ["OneDrive", "SharePoint", "Dropbox", "Google Drive"]
    
    # Use dedicated pilot sub-dir in local AppData as recommended by ADR-004
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        print("ERROR: LOCALAPPDATA not found. Cannot enforce hermetic project location.")
        sys.exit(1)
        
    pilot_root = Path(local_app_data) / "FP&A Month-End Copilot" / "Projects" / "pilot_gate_13"
    
    if any(tag in str(pilot_root) for tag in sync_tags):
        print(f"SECURITY ALERT: Pilot root is in a sync-path: {pilot_root}")
        sys.exit(1)
        
    pilot_root.mkdir(parents=True, exist_ok=True)
    os.environ["FPA_PROJECT_DIR"] = str(pilot_root)
    
    # Establish ingestion path for real sanitized data
    data_ingest_path = pilot_root / "data_ingest"
    data_ingest_path.mkdir(exist_ok=True)
    
    print(f"Pilot workspace initialized at: {pilot_root}")
    print(f"Data ingestion path ready at: {data_ingest_path}")
    print("WARNING: Sample data is prohibited in this environment.")
    
if __name__ == "__main__":
    enforce_hermetic_env()
