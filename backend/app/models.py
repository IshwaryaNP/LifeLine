from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Landmark(BaseModel):
    name: str
    lat: float
    lon: float
    aliases: List[str] = Field(default_factory=list)

class Zone(BaseModel):
    id: str
    name: str
    population: int
    area_km2: float
    elevation_m: float
    dist_to_shelter_km: float
    dist_to_hospital_km: float
    connectivity: float
    landmarks: List[Landmark] = Field(default_factory=list)
    polygon: List[List[float]] # [[lat, lon], ...]
    risk_score: float = 0.0
    risk_factors: Dict[str, float] = Field(default_factory=dict)
    is_silent: bool = False

class Report(BaseModel):
    id: str
    minute: int
    channel: str # sms, call, social, volunteer
    sender_hash: str
    text: str
    # Extraction outputs
    need_type: Optional[str] = None
    people_count: Optional[int] = None
    vulnerable_groups: List[str] = Field(default_factory=list)
    urgency_cues: List[str] = Field(default_factory=list)
    place_text: Optional[str] = None
    extraction_confidences: Dict[str, float] = Field(default_factory=dict)
    # Geo location
    lat: Optional[float] = None
    lon: Optional[float] = None
    radius_m: float = 1000.0
    zone_id: Optional[str] = None
    location_confidence: float = 0.0
    needs_human_check: bool = False
    is_fake_detected: bool = False

class FactorBreakdown(BaseModel):
    need_severity: float
    people: float
    vulnerable: float
    time_criticality: float
    corroboration: float
    reliability: float
    priority_score: float

class Incident(BaseModel):
    id: str
    zone_id: Optional[str] = None
    zone_name: Optional[str] = None
    report_ids: List[str] = Field(default_factory=list)
    reports: List[Report] = Field(default_factory=list)
    lat: Optional[float] = None
    lon: Optional[float] = None
    radius_m: float = 500.0
    need_type: str = "other"
    estimated_people: int = 0
    vulnerable_groups: List[str] = Field(default_factory=list)
    independent_sources: int = 1
    channels: List[str] = Field(default_factory=list)
    reliability_score: float = 0.5
    priority_score: float = 0.0
    factors: Dict[str, float] = Field(default_factory=dict)
    reasons: List[str] = Field(default_factory=list)
    status: str = "recommended" # recommended, approved, overridden, dismissed, merged
    override_reason: Optional[str] = None
    override_priority: Optional[float] = None
    needs_human_check: bool = False

class ActionAudit(BaseModel):
    id: Optional[int] = None
    timestamp: str
    incident_id: str
    action_type: str # approve, override, merge, split, dismiss
    reason: str
    new_priority: Optional[float] = None
    target_id: Optional[str] = None
    user: str = "Coordinator"

class SilentZoneAlert(BaseModel):
    zone_id: str
    zone_name: str
    risk_score: float
    connectivity: float
    report_count: int
    expected_reports: float
    silence_index: float
    message: str = "No or few reports, but high risk. Possible unreported need. Verify by call or scout."

class WarningAlertDraft(BaseModel):
    id: str
    cyclone_name: str
    expected_landfall_time: str
    category: str
    zone_id: str
    zone_name: str
    message: str
    reasons: List[str]
    status: str = "draft" # draft, approved
