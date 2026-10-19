import datetime
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from app.models import ActionAudit
from app.simulation import sim_manager
from app.store import init_db, save_audit_action, get_audit_logs, save_alerts, update_alert_status, get_alerts
from app.alerts import generate_preparedness_alerts
from app.silence import compute_silence_gaps
from app.metrics import compute_ground_truth_metrics

app = FastAPI(
    title="Lifeline Triage API",
    description="Decision-support tool for cyclone response control rooms (Simulated Data)",
    version="1.0.0"
)

# Enable CORS for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    init_db()

# Request schemas
class StartSimRequest(BaseModel):
    speed: int = 5 # 1, 5, or 20

class ActionRequest(BaseModel):
    type: str # approve | override | merge | split | dismiss
    reason: str
    new_priority: Optional[float] = None
    target_id: Optional[str] = None

class DraftAlertsRequest(BaseModel):
    cyclone_name: str
    expected_landfall_time: str
    category: str

# 1. Health check
@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "Lifeline Triage",
        "simulated": True,
        "offline_ready": True
    }

# 2. District & Zones
@app.get("/api/district")
def get_district():
    return sim_manager.district_data

# 3. Simulation Controls
@app.post("/api/simulation/start")
def start_simulation(req: Optional[StartSimRequest] = None):
    speed = req.speed if req else 5
    if speed not in [1, 5, 20]:
        raise HTTPException(status_code=400, detail="Speed must be 1, 5, or 20")
    sim_manager.start(speed=speed)
    return {"status": "started", "speed": speed}

@app.post("/api/simulation/reset")
def reset_simulation():
    sim_manager.reset()
    return {"status": "reset"}

@app.get("/api/simulation/state")
def get_simulation_state():
    return sim_manager.get_state()

# 4. Incidents
@app.get("/api/incidents")
def list_incidents():
    # Returns ranked incidents with factors
    with sim_manager.lock:
        return sim_manager.incidents

@app.get("/api/incidents/{incident_id}")
def get_incident(incident_id: str):
    with sim_manager.lock:
        for inc in sim_manager.incidents:
            if inc["id"] == incident_id:
                return inc
    raise HTTPException(status_code=404, detail="Incident not found")

@app.post("/api/incidents/{incident_id}/actions")
def post_incident_action(incident_id: str, action: ActionRequest):
    if not action.reason or len(action.reason.strip()) == 0:
        raise HTTPException(status_code=400, detail="Reason is required for all human-in-the-loop actions")

    valid_types = ["approve", "override", "merge", "split", "dismiss"]
    if action.type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Action type must be one of {valid_types}")

    # Check incident exists
    found = False
    with sim_manager.lock:
        for inc in sim_manager.incidents:
            if inc["id"] == incident_id:
                found = True
                break
    if not found:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Apply in simulation manager
    sim_manager.apply_action(
        incident_id=incident_id,
        action_type=action.type,
        reason=action.reason,
        new_priority=action.new_priority,
        target_id=action.target_id
    )

    # Log in audit store
    audit_entry = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "incident_id": incident_id,
        "action_type": action.type,
        "reason": action.reason,
        "new_priority": action.new_priority,
        "target_id": action.target_id,
        "user": "Control Room Lead"
    }
    save_audit_action(audit_entry)

    return {"status": "action_recorded", "incident_id": incident_id, "action": action.type}

# 5. Audit Log
@app.get("/api/audit")
def list_audit_logs():
    return get_audit_logs()

# 6. Silence Gap Analysis
@app.get("/api/silence")
def get_silence_gaps():
    with sim_manager.lock:
        gaps = compute_silence_gaps(sim_manager.zones, sim_manager.processed_reports)
        return gaps

# 7. Metrics
@app.get("/api/metrics")
def get_metrics():
    # Compute purely from ground truth, not hardcoded
    return compute_ground_truth_metrics()

# 8. Cyclone Live Track & Approach
from app.cyclone import get_cyclone_status

@app.get("/api/cyclone/track")
def get_cyclone_track():
    """
    Returns live cyclone approach coordinates, category, distance to landfall,
    wind speeds, and projected path based on current simulation progress.
    """
    with sim_manager.lock:
        curr_min = sim_manager.current_minute
    return get_cyclone_status(curr_min)

# 9. Early Warnings & Multi-Channel Alerts
@app.post("/api/alerts/draft")
def draft_alerts(req: DraftAlertsRequest):
    with sim_manager.lock:
        drafts = generate_preparedness_alerts(
            cyclone_name=req.cyclone_name,
            expected_landfall_time=req.expected_landfall_time,
            category=req.category,
            zones=sim_manager.zones
        )
    save_alerts(drafts)
    return {"status": "drafted", "alerts": drafts}

@app.get("/api/alerts")
def list_alerts():
    return get_alerts()

@app.post("/api/alerts/{alert_id}/approve")
def approve_alert(alert_id: str):
    update_alert_status(alert_id, "approved")
    return {"status": "approved", "alert_id": alert_id}

@app.post("/api/alerts/{alert_id}/broadcast")
def broadcast_alert(alert_id: str):
    """
    Simulates sending alerts directly to users in the affected zone
    via SMS Cell Broadcast, WhatsApp, and Community Siren Networks.
    """
    update_alert_status(alert_id, "broadcasted")
    return {
        "status": "broadcasted",
        "alert_id": alert_id,
        "channels_reached": ["SMS Cell Broadcast", "WhatsApp Emergency Channel", "HAM Radio / Siren Hubs"],
        "delivery_rate": "98.4%",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

