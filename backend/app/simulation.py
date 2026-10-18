import time
import json
import threading
from typing import List, Dict, Any, Optional
from pathlib import Path
from app.extract import extract_report_info
from app.locate import resolve_location
from app.merge import cluster_reports_into_incidents
from app.score import score_incident
from app.silence import compute_silence_gaps

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

class SimulationManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.is_running: bool = False
        self.speed: int = 5 # 1, 5, or 20
        self.current_minute: int = 0
        self.max_minute: int = 240
        self.thread: Optional[threading.Thread] = None

        # Datasets
        self.all_reports: List[Dict[str, Any]] = []
        self.district_data: Dict[str, Any] = {}
        self.zones: List[Dict[str, Any]] = []

        # Current state
        self.processed_reports: List[Dict[str, Any]] = []
        self.incidents: List[Dict[str, Any]] = []
        self.manual_actions: Dict[str, Dict[str, Any]] = {}

        self.load_data()

    def load_data(self):
        with self.lock:
            # Load district
            dist_file = DATA_DIR / "district.json"
            if dist_file.exists():
                with open(dist_file, "r", encoding="utf-8") as f:
                    self.district_data = json.load(f)
                    self.zones = self.district_data.get("zones", [])

            # Load reports
            rep_file = DATA_DIR / "reports.jsonl"
            self.all_reports = []
            if rep_file.exists():
                with open(rep_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            self.all_reports.append(json.loads(line))
            self.all_reports.sort(key=lambda r: r["minute"])

    def start(self, speed: int = 5):
        with self.lock:
            self.speed = speed
            if not self.is_running:
                self.is_running = True
                self.thread = threading.Thread(target=self._run_loop, daemon=True)
                self.thread.start()

    def reset(self):
        with self.lock:
            self.is_running = False
            self.current_minute = 0
            self.processed_reports = []
            self.incidents = []
            self.manual_actions = {}
        # Ensure fresh data
        self.load_data()

    def get_state(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "is_running": self.is_running,
                "current_minute": self.current_minute,
                "max_minute": self.max_minute,
                "speed": self.speed,
                "total_reports": len(self.all_reports),
                "received_reports_count": len(self.processed_reports),
                "incidents_count": len(self.incidents)
            }

    def _run_loop(self):
        while True:
            with self.lock:
                if not self.is_running:
                    break
                if self.current_minute >= self.max_minute:
                    self.is_running = False
                    break
                
                # Advance simulated clock by speed step
                self.current_minute = min(self.max_minute, self.current_minute + self.speed)
                
                # Ingest newly arrived reports up to current_minute
                existing_ids = {r["id"] for r in self.processed_reports}
                new_arrivals = [r for r in self.all_reports if r["minute"] <= self.current_minute and r["id"] not in existing_ids]

                for raw_rep in new_arrivals:
                    rep_dict = dict(raw_rep)
                    
                    # 1. Extraction
                    ext = extract_report_info(rep_dict["text"])
                    rep_dict.update(ext)
                    
                    # 2. Location resolution
                    loc = resolve_location(rep_dict.get("place_text", ""), self.zones)
                    rep_dict.update(loc)
                    
                    self.processed_reports.append(rep_dict)

                # Re-cluster and score incidents each tick
                if self.processed_reports:
                    self._recompute_incidents()

            time.sleep(1.0) # tick once per real second

    def _recompute_incidents(self):
        # Filter out spam or empty
        valid_reports = self.processed_reports
        
        # Cluster
        clusters = cluster_reports_into_incidents(valid_reports)
        
        new_incidents = []
        for idx, clus in enumerate(clusters, start=1):
            scored = score_incident(clus, self.current_minute)
            rep_ids = [r["id"] for r in clus]
            
            # Deterministic incident ID based on root or first report
            inc_id = f"INC-{sorted(rep_ids)[0]}"
            
            zone_name = None
            if scored["zone_id"]:
                for z in self.zones:
                    if z["id"] == scored["zone_id"]:
                        zone_name = z["name"]
                        break

            incident_obj = {
                "id": inc_id,
                "zone_id": scored["zone_id"],
                "zone_name": zone_name or "Unassigned Zone",
                "report_ids": rep_ids,
                "reports": clus,
                "lat": scored["lat"],
                "lon": scored["lon"],
                "radius_m": scored["radius_m"],
                "need_type": scored["need_type"],
                "estimated_people": scored["estimated_people"],
                "vulnerable_groups": scored["vulnerable_groups"],
                "independent_sources": scored["independent_sources"],
                "channels": scored["channels"],
                "reliability_score": scored["reliability_score"],
                "priority_score": scored["priority_score"],
                "factors": scored["factors"],
                "reasons": scored["reasons"],
                "status": "recommended",
                "override_reason": None,
                "override_priority": None,
                "needs_human_check": scored["needs_human_check"]
            }

            # Check if coordinator performed an action previously on this incident
            if inc_id in self.manual_actions:
                action = self.manual_actions[inc_id]
                incident_obj["status"] = action["status"]
                incident_obj["override_reason"] = action.get("reason")
                if action.get("new_priority") is not None:
                    incident_obj["override_priority"] = action["new_priority"]
                    incident_obj["priority_score"] = action["new_priority"]

            new_incidents.append(incident_obj)

        # Sort by priority_score descending
        new_incidents.sort(key=lambda x: x["priority_score"], reverse=True)
        self.incidents = new_incidents

    def apply_action(self, incident_id: str, action_type: str, reason: str, new_priority: Optional[float] = None, target_id: Optional[str] = None):
        with self.lock:
            status_map = {
                "approve": "approved",
                "override": "overridden",
                "dismiss": "dismissed",
                "merge": "merged",
                "split": "split"
            }
            new_status = status_map.get(action_type, "recommended")
            self.manual_actions[incident_id] = {
                "status": new_status,
                "reason": reason,
                "new_priority": new_priority
            }
            # Recompute to reflect immediately in incident list
            self._recompute_incidents()

sim_manager = SimulationManager()
