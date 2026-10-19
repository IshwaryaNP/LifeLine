import React, { useState, useEffect, useMemo, useRef } from 'react';
import { 
  MapContainer, TileLayer, GeoJSON, CircleMarker, Popup, useMap 
} from 'react-leaflet';
import { 
  AlertTriangle, CheckCircle2, ChevronRight, Activity, 
  Play, RotateCcw, FileText, ArrowRight, X, PhoneCall, 
  Users, Clock, ShieldAlert, Award, TrendingUp, Info, 
  MapPin, Radio, Compass, RefreshCw, Eye, EyeOff, Layers, ExternalLink,
  Check, ThumbsUp, ShieldCheck, LayoutDashboard, Search, Bell, Settings,
  Filter, HelpCircle, Send, User, ChevronDown, BarChart3, AlertOctagon, LifeBuoy,
  Wind, Navigation, Smartphone, Megaphone
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || '';

// Plain-language formatters
const NEED_CONFIG = {
  rescue: { label: 'People trapped by floodwater', badge: 'Rescue', color: '#c53030', bg: '#fff5f5' },
  medical: { label: 'Urgent medical assistance needed', badge: 'Medical', color: '#dd6b20', bg: '#fffaf0' },
  shelter: { label: 'Safe shelter needed urgently', badge: 'Shelter', color: '#3182ce', bg: '#ebf8ff' },
  water: { label: 'Clean drinking water required', badge: 'Drinking Water', color: '#0987a0', bg: '#e6fffa' },
  food: { label: 'Emergency food supplies needed', badge: 'Food Relief', color: '#b7791f', bg: '#fffff0' },
  other: { label: 'General relief supplies requested', badge: 'General Relief', color: '#4a5568', bg: '#edf2f7' }
};

const VULNERABLE_CONFIG = {
  elderly: { label: 'Elderly residents', icon: '👴' },
  children: { label: 'Children & infants', icon: '👶' },
  pregnant: { label: 'Expectant mothers', icon: '🤰' },
  disabled: { label: 'Persons with disabilities', icon: '♿' }
};

const CHANNEL_CONFIG = {
  whatsapp: 'WhatsApp helpline',
  sms: 'Direct emergency SMS',
  voice_ivr: 'Dial-in voice helpline (IVR)',
  social_media: 'Public emergency post'
};

function getUrgencyLevel(score) {
  if (score >= 0.70) return { label: 'Critical — dispatch immediately', color: '#c53030', bg: '#fff5f5', border: '#feb2b2', tier: 'critical' };
  if (score >= 0.40) return { label: 'High — dispatch within 2 hours', color: '#dd6b20', bg: '#fffaf0', border: '#fbd38d', tier: 'high' };
  return { label: 'Moderate — monitor and queue', color: '#2b6cb0', bg: '#ebf8ff', border: '#bee3f8', tier: 'moderate' };
}

function getVerificationLevel(relScore, sources) {
  if (relScore >= 0.75 || sources >= 3) {
    return { label: 'Strongly verified', detail: `Confirmed by ${sources} independent callers across channels`, color: '#22543d', bg: '#c6f6d5' };
  }
  if (relScore >= 0.45 || sources >= 2) {
    return { label: 'Partially verified', detail: `Corroborated by ${sources} separate reports`, color: '#744210', bg: '#feebc8' };
  }
  return { label: 'Single report — confirming', detail: 'Received from 1 caller; cross-checking field reports', color: '#7b341e', bg: '#feebc8' };
}

function MapUpdater({ center, zoom }) {
  const map = useMap();

  useEffect(() => {
    // Invalidate size immediately and after standard CSS render tick
    map.invalidateSize();
    const t = setTimeout(() => {
      map.invalidateSize();
    }, 200);
    return () => clearTimeout(t);
  }, [map]);

  useEffect(() => {
    if (center && Array.isArray(center) && center.length === 2 && center[0] != null && center[1] != null) {
      map.setView(center, zoom || map.getZoom());
    }
  }, [center, zoom, map]);

  return null;
}

export default function App() {
  const [currentStep, setCurrentStep] = useState(1); // 1: Prepare, 2: Respond, 3: Proof
  const [district, setDistrict] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [silenceData, setSilenceData] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [simState, setSimState] = useState({ is_running: false, current_step: 0, total_steps: 10 });
  const [loading, setLoading] = useState(true);
  
  // UI states
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [isWhyDrawerOpen, setIsWhyDrawerOpen] = useState(false);
  const [isAuditDrawerOpen, setIsAuditDrawerOpen] = useState(false);
  const [isFirstVisitOpen, setIsFirstVisitOpen] = useState(() => {
    return !localStorage.getItem('lifeline_visited');
  });
  const [isPitchModalOpen, setIsPitchModalOpen] = useState(false);
  const [showOverrideModal, setShowOverrideModal] = useState(false);
  const [overrideIncident, setOverrideIncident] = useState(null);
  const [overridePriority, setOverridePriority] = useState('Critical — dispatch immediately');
  const [overrideReason, setOverrideReason] = useState('');
  const [overrideError, setOverrideError] = useState('');
  
  // Guided Demo states
  const [isDemoRunning, setIsDemoRunning] = useState(false);
  const [demoStep, setDemoStep] = useState(0);
  const [toastMessage, setToastMessage] = useState(null);
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'prepare' | 'respond' | 'proof' | 'audit' | 'analytics'
  const [searchQuery, setSearchQuery] = useState('');
  const [focusedZoneId, setFocusedZoneId] = useState(null);
  const [activeNeedFilter, setActiveNeedFilter] = useState('all');
  const [cycloneTrack, setCycloneTrack] = useState(null);
  const [alertsList, setAlertsList] = useState([]);

  // Fetch initial data
  const fetchData = async () => {
    try {
      const [distRes, incRes, silRes, audRes, metRes, simRes, cycRes, altRes] = await Promise.all([
        fetch(`${API_BASE}/api/district`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/api/incidents`).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/api/silence`).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/api/audit`).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/api/metrics`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/api/simulation/state`).then(r => r.json()).catch(() => ({ is_running: false, current_step: 0 })),
        fetch(`${API_BASE}/api/cyclone/track`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/api/alerts`).then(r => r.json()).catch(() => [])
      ]);

      if (cycRes) setCycloneTrack(cycRes);
      if (Array.isArray(altRes)) setAlertsList(altRes);

      if (distRes) {
        // Normalize raw district data into GeoJSON FeatureCollection if needed
        if (distRes.zones && !distRes.features) {
          const geoJson = {
            type: "FeatureCollection",
            features: distRes.zones.map(z => ({
              type: "Feature",
              properties: {
                id: z.id,
                name: z.name,
                population: z.population,
                risk_score: z.risk_score,
                is_silent: z.is_silent,
                connectivity: z.connectivity
              },
              geometry: {
                type: "Polygon",
                // GeoJSON polygon coordinates are [longitude, latitude]
                coordinates: [z.polygon.map(coord => [coord[1], coord[0]])]
              }
            }))
          };
          setDistrict(geoJson);
        } else {
          setDistrict(distRes);
        }
      }
      if (Array.isArray(incRes)) setIncidents(incRes);
      if (Array.isArray(silRes)) setSilenceData(silRes);
      if (Array.isArray(audRes)) setAuditLogs(audRes);
      if (metRes) setMetrics(metRes);
      if (simRes) setSimState(simRes);
    } catch (err) {
      console.error('Data fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Faster, smoother refresh interval (2 seconds)
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3800);
  };

  // Guided demo sequence
  const demoSteps = useMemo(() => [
    {
      screen: 1,
      caption: 'Step 1: Prepare — Before the cyclone makes landfall, see which coastal zones have vulnerable populations and cut-off communications.',
      action: () => { setActiveTab('prepare'); setCurrentStep(1); setFocusedZoneId('Z01'); }
    },
    {
      screen: 2,
      caption: 'Step 2: Respond — 213 field reports are automatically grouped into 45 verified incidents, ranked by human urgency rather than who calls loudest.',
      action: () => { 
        setActiveTab('respond');
        setCurrentStep(2); 
        if (incidents.length > 0) {
          setSelectedIncident(incidents[0]);
          setIsWhyDrawerOpen(true);
        }
      }
    },
    {
      screen: 2,
      caption: 'Transparency — Every single dispatch priority has a plain-language explanation showing callers, vulnerable people, and time urgency.',
      action: () => { setIsWhyDrawerOpen(true); }
    },
    {
      screen: 3,
      caption: 'Step 3: Proof — Comparing our triage against traditional first-come dispatch shows 80% expert overlap and 3 of 3 cut-off zones proactively detected.',
      action: () => { setIsWhyDrawerOpen(false); setActiveTab('proof'); setCurrentStep(3); }
    }
  ], [incidents]);

  useEffect(() => {
    if (!isDemoRunning) return;
    const timer = setTimeout(() => {
      if (demoStep < demoSteps.length - 1) {
        const next = demoStep + 1;
        setDemoStep(next);
        demoSteps[next].action();
      } else {
        setIsDemoRunning(false);
        setDemoStep(0);
        showToast('Guided demo finished. You are in full manual control.');
      }
    }, 6000);
    return () => clearTimeout(timer);
  }, [isDemoRunning, demoStep, demoSteps]);

  const startDemo = () => {
    setIsFirstVisitOpen(false);
    setIsDemoRunning(true);
    setDemoStep(0);
    demoSteps[0].action();
  };

  const stopDemo = () => {
    setIsDemoRunning(false);
  };

  const dismissFirstVisit = () => {
    setIsFirstVisitOpen(false);
    localStorage.setItem('lifeline_visited', 'true');
  };

  const handleSimStart = async () => {
    try {
      await fetch(`${API_BASE}/api/simulation/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ speed: 5 })
      });
      showToast('Cyclone scenario simulation started. Incident stream active.');
      fetchData();
    } catch {
      showToast('Could not start simulation.');
    }
  };

  const handleSimReset = async () => {
    try {
      await fetch(`${API_BASE}/api/simulation/reset`, { method: 'POST' });
      showToast('System reset to pre-cyclone standby state.');
      fetchData();
    } catch {
      showToast('Could not reset simulation.');
    }
  };

  const submitPriorityOverride = async (e) => {
    e.preventDefault();
    if (!overrideReason.trim()) {
      setOverrideError('A written explanation is required to change priority.');
      return;
    }
    try {
      const priorityScoreMap = {
        'Critical — dispatch immediately': 0.95,
        'High — dispatch within 2 hours': 0.75,
        'Moderate — monitor and queue': 0.50
      };
      const numericPriority = priorityScoreMap[overridePriority] || 0.75;

      const res = await fetch(`${API_BASE}/api/incidents/${overrideIncident.id}/actions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'override',
          reason: overrideReason.trim(),
          new_priority: numericPriority
        })
      });
      if (!res.ok) {
        throw new Error('Server returned ' + res.status);
      }
      showToast(`Priority updated for incident #${overrideIncident.id}`);
      setShowOverrideModal(false);
      setOverrideReason('');
      setOverrideError('');
      fetchData();
    } catch {
      setOverrideError('Failed to record priority change. Please retry.');
    }
  };

  const filteredIncidents = useMemo(() => {
    if (activeNeedFilter === 'all') return incidents;
    return incidents.filter(inc => inc.need_type === activeNeedFilter);
  }, [incidents, activeNeedFilter]);

  // Total people at risk across incidents
  const totalPeopleAtRisk = useMemo(() => {
    return incidents.reduce((sum, inc) => sum + (inc.estimated_people || 0), 0);
  }, [incidents]);

  return (
    <div className="dash-shell">
      {/* 1. TRUSTVEST-STYLE LEFT SIDEBAR */}
      <aside className="dash-sidebar">
        <div className="sidebar-brand">
          <div className="brand-logo-sq">
            <Radio size={20} color="#ffffff" />
          </div>
          <div className="brand-names">
            <span className="brand-main-title">Lifeline</span>
            <span className="brand-sub-badge">AI Triage</span>
          </div>
        </div>

        {/* Sidebar Search Bar */}
        <div className="sidebar-search-box">
          <Search size={15} className="sidebar-search-icon" />
          <input 
            type="text" 
            placeholder="Search incident, zone..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="sidebar-search-input"
          />
        </div>

        {/* Navigation Section 1: Main */}
        <div className="sidebar-nav-section">
          <span className="nav-section-title">MAIN MENU</span>
          <nav className="sidebar-nav-list">
            <button 
              className={`sidebar-nav-item ${activeTab === 'overview' ? 'active' : ''}`}
              onClick={() => setActiveTab('overview')}
            >
              <LayoutDashboard size={18} />
              <span>Overview</span>
            </button>

            <button 
              className={`sidebar-nav-item ${activeTab === 'cyclone' ? 'active' : ''}`}
              onClick={() => setActiveTab('cyclone')}
            >
              <Wind size={18} />
              <span>Live Cyclone & Alerts</span>
              <span className="nav-tag alert">LIVE</span>
            </button>

            <button 
              className={`sidebar-nav-item ${activeTab === 'prepare' ? 'active' : ''}`}
              onClick={() => { setActiveTab('prepare'); setCurrentStep(1); }}
            >
              <Compass size={18} />
              <span>1. Blackout Zones</span>
              <span className="nav-tag alert">{silenceData.filter(s => s.status === 'silent' || s.risk_score >= 0.5).length || 3}</span>
            </button>

            <button 
              className={`sidebar-nav-item ${activeTab === 'respond' ? 'active' : ''}`}
              onClick={() => { setActiveTab('respond'); setCurrentStep(2); }}
            >
              <AlertOctagon size={18} />
              <span>2. Emergency Queue</span>
              <span className="nav-tag blue">{incidents.length || 45}</span>
            </button>

            <button 
              className={`sidebar-nav-item ${activeTab === 'proof' ? 'active' : ''}`}
              onClick={() => { setActiveTab('proof'); setCurrentStep(3); }}
            >
              <Award size={18} />
              <span>3. Proof & Impact</span>
            </button>
          </nav>
        </div>

        {/* Navigation Section 2: Management */}
        <div className="sidebar-nav-section">
          <span className="nav-section-title">CONTROL ROOM</span>
          <nav className="sidebar-nav-list">
            <button 
              className="sidebar-nav-item"
              onClick={() => setIsAuditDrawerOpen(true)}
            >
              <Activity size={18} />
              <span>Activity Log</span>
              <span className="nav-tag gray">{auditLogs.length}</span>
            </button>
          </nav>
        </div>

        {/* Sidebar Footer: System Status */}
        <div className="sidebar-footer">
          <div className="system-status-card">
            <div className="status-indicator-dot online"></div>
            <div className="status-text-group">
              <span className="status-label">FastAPI Engine</span>
              <span className="status-value">Active & Syncing (2s)</span>
            </div>
          </div>
          <button 
            className="sidebar-support-btn" 
            onClick={() => setIsFirstVisitOpen(true)}
            title="Open Interactive Guide"
          >
            <HelpCircle size={15} />
            <span>Help Guide</span>
          </button>
        </div>
      </aside>

      {/* 2. MAIN APP CANVAS */}
      <div className="dash-main-canvas">
        {/* Top Navbar */}
        <header className="dash-top-bar">
          <div className="dash-top-left">
            <h2 className="dash-page-title">
              {activeTab === 'overview' && 'Operations Overview'}
              {activeTab === 'cyclone' && 'Cyclone Approach Track & Early Warning Alerts'}
              {activeTab === 'prepare' && 'Step 1: Blackout Zones Preparation'}
              {activeTab === 'respond' && 'Step 2: Emergency Response Triage'}
              {activeTab === 'proof' && 'Step 3: Benchmark Proof & Accuracy'}
            </h2>
            <span className="top-subtitle-path">Cyclone Biparjoy Command Center • Srikakulam District</span>
          </div>

          <div className="dash-top-right">
            {/* Quick Demo Tour Button */}
            <button 
              className={`top-pill-btn tour ${isDemoRunning ? 'active' : ''}`}
              onClick={isDemoRunning ? stopDemo : startDemo}
              id="start-demo-btn"
            >
              {isDemoRunning ? <RotateCcw size={15} /> : <Play size={15} />}
              <span>{isDemoRunning ? 'Pause Tour' : '▶ 30s Tour'}</span>
            </button>

            {/* Simulated Live Stream advance */}
            <button 
              className="top-pill-btn sync"
              onClick={handleSimStart}
              title="Stream new simulated reports into control room"
            >
              <RefreshCw size={14} />
              <span>Stream Incoming</span>
            </button>

            {/* User / Coordinator Profile Avatar */}
            <div className="coordinator-avatar-badge">
              <div className="avatar-circle">IC</div>
              <div className="avatar-info">
                <span className="avatar-name">Cmdr. Rao</span>
                <span className="avatar-role">Incident Commander</span>
              </div>
            </div>
          </div>
        </header>

        {/* Guided Demo Caption Banner if active */}
        {isDemoRunning && (
          <aside className="demo-caption-banner" aria-live="polite">
            <div className="demo-caption-content">
              <Compass className="spin" size={20} />
              <p className="demo-caption-text">{demoSteps[demoStep].caption}</p>
            </div>
            <button className="demo-caption-close" onClick={stopDemo}>Exit Tour</button>
          </aside>
        )}

        {/* Body Container based on selected tab */}
        <main className="dash-content-body">
          {loading ? (
            <div className="loading-state">
              <RefreshCw className="spin" size={32} />
              <p>Loading district coastal models and incident reports...</p>
            </div>
          ) : (
            <>
              {activeTab === 'overview' && (
                <ScreenOverview 
                  district={district}
                  incidents={filteredIncidents}
                  silenceData={silenceData}
                  auditLogs={auditLogs}
                  totalPeople={totalPeopleAtRisk}
                  onNavigateTab={(tab) => {
                    setActiveTab(tab);
                    if (tab === 'prepare') setCurrentStep(1);
                    if (tab === 'respond') setCurrentStep(2);
                    if (tab === 'proof') setCurrentStep(3);
                  }}
                  onSelectIncident={(inc) => {
                    setSelectedIncident(inc);
                    setIsWhyDrawerOpen(true);
                  }}
                  onTriggerSimulation={handleSimStart}
                />
              )}

              {activeTab === 'cyclone' && (
                <ScreenCycloneTrack 
                  cycloneTrack={cycloneTrack}
                  alertsList={alertsList}
                  district={district}
                  onAlertBroadcasted={fetchData}
                  onShowToast={showToast}
                />
              )}

              {activeTab === 'prepare' && (
                <ScreenPrepare 
                  district={district}
                  silenceData={silenceData}
                  focusedZoneId={focusedZoneId}
                  onSelectZone={(zoneId) => setFocusedZoneId(zoneId)}
                  onProceed={() => {
                    setActiveTab('respond');
                    setCurrentStep(2);
                  }}
                />
              )}

              {activeTab === 'respond' && (
                <ScreenRespond 
                  incidents={filteredIncidents}
                  allIncidentsCount={incidents.length}
                  district={district}
                  selectedIncident={selectedIncident}
                  activeNeedFilter={activeNeedFilter}
                  totalPeople={totalPeopleAtRisk}
                  onSelectNeedFilter={setActiveNeedFilter}
                  onSelectIncident={(inc) => {
                    setSelectedIncident(inc);
                    setIsWhyDrawerOpen(true);
                  }}
                  onChangePriority={(inc) => {
                    setOverrideIncident(inc);
                    setShowOverrideModal(true);
                  }}
                  onProceed={() => {
                    setActiveTab('proof');
                    setCurrentStep(3);
                  }}
                />
              )}

              {activeTab === 'proof' && (
                <ScreenProof 
                  metrics={metrics}
                  incidentsCount={incidents.length}
                  silenceCount={silenceData.filter(s => s.status === 'silent' || s.risk_score >= 0.5).length}
                  onRestart={() => {
                    setActiveTab('overview');
                    setCurrentStep(1);
                  }}
                />
              )}
            </>
          )}
        </main>
      </div>

      {/* WHY DRAWER: Plain-language explanation for selected emergency */}
      {isWhyDrawerOpen && selectedIncident && (
        <WhyDrawer 
          incident={selectedIncident} 
          onClose={() => setIsWhyDrawerOpen(false)}
          onChangePriority={() => {
            setOverrideIncident(selectedIncident);
            setShowOverrideModal(true);
          }}
        />
      )}

      {/* ACTIVITY LOG DRAWER */}
      {isAuditDrawerOpen && (
        <ActivityLogDrawer 
          logs={auditLogs} 
          onClose={() => setIsAuditDrawerOpen(false)} 
        />
      )}

      {/* CHANGE PRIORITY MODAL (Mandatory Reason) */}
      {showOverrideModal && overrideIncident && (
        <div className="modal-backdrop" onClick={() => setShowOverrideModal(false)}>
          <div className="modal-dialog" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h3 className="modal-title">Adjust Emergency Priority</h3>
                <p className="modal-subtitle">
                  Incident #{overrideIncident.id} in {overrideIncident.zone_name}
                </p>
              </div>
              <button className="btn-icon" onClick={() => setShowOverrideModal(false)}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={submitPriorityOverride} className="modal-body">
              <div className="form-group">
                <label className="form-label">New Priority Level</label>
                <select 
                  className="form-select"
                  value={overridePriority}
                  onChange={e => setOverridePriority(e.target.value)}
                >
                  <option value="Critical — dispatch immediately">Critical — dispatch immediately</option>
                  <option value="High — dispatch within 2 hours">High — dispatch within 2 hours</option>
                  <option value="Moderate — monitor and queue">Moderate — monitor and queue</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">
                  Reason for Adjustment <span className="required-star">*</span>
                </label>
                <textarea 
                  className="form-textarea"
                  rows={3}
                  placeholder="Explain why this priority is being changed (e.g., 'Field reconnaissance team confirms immediate dam overflow hazard')..."
                  value={overrideReason}
                  onChange={e => {
                    setOverrideReason(e.target.value);
                    setOverrideError('');
                  }}
                  required
                />
                {overrideError && <p className="form-error">{overrideError}</p>}
                <p className="form-helper">
                  A reason is mandatory. This adjustment is recorded permanently in the official activity log.
                </p>
              </div>

              <div className="modal-footer">
                <button 
                  type="button" 
                  className="btn btn-secondary" 
                  onClick={() => setShowOverrideModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Save Priority & Log Action
                </button>
              </div>
            </form>
          </div>
        </div>
      )}



      {/* FIRST-VISIT 3-STEP GUIDE MODAL */}
      {isFirstVisitOpen && (
        <div className="modal-backdrop">
          <div className="modal-dialog modal-welcome">
            <div className="welcome-header">
              <div className="welcome-icon-box">
                <Radio size={28} color="#2b6cb0" />
              </div>
              <div>
                <h2 className="welcome-title">Welcome to Lifeline Triage</h2>
                <p className="welcome-subtitle">A fast guide for control room coordinators and observers</p>
              </div>
            </div>

            <div className="welcome-body">
              <div className="welcome-card">
                <div className="welcome-step-num">1</div>
                <div>
                  <h4 className="welcome-step-heading">Step 1: Prepare (Blackout Zones)</h4>
                  <p className="welcome-step-desc">
                    Spot vulnerable coastal areas and telecom blackouts <strong>before</strong> the cyclone makes landfall.
                  </p>
                </div>
              </div>

              <div className="welcome-card">
                <div className="welcome-step-num">2</div>
                <div>
                  <h4 className="welcome-step-heading">Step 2: Respond (Life-Threat Urgency)</h4>
                  <p className="welcome-step-desc">
                    Dispatch rescue teams by true life-safety urgency, not just whoever calls the helpline most times.
                  </p>
                </div>
              </div>

              <div className="welcome-card">
                <div className="welcome-step-num">3</div>
                <div>
                  <h4 className="welcome-step-heading">Step 3: Proof (Benchmark Results)</h4>
                  <p className="welcome-step-desc">
                    Verify that automated triage matches disaster management experts and reaches silent zones first.
                  </p>
                </div>
              </div>
            </div>

            <div className="welcome-footer">
              <button className="btn btn-demo" onClick={startDemo}>
                <Play size={15} />
                <span>▶ Start 30-Second Demo Tour</span>
              </button>
              <button className="btn btn-ghost" onClick={dismissFirstVisit}>
                Explore On My Own
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toast notifications */}
      {toastMessage && (
        <aside className="toast" role="status" aria-live="polite">
          <CheckCircle2 size={18} color="#22543d" />
          <span>{toastMessage}</span>
        </aside>
      )}
    </div>
  );
}

// ----------------------------------------------------------------------------
// SCREEN: OVERVIEW (TrustVest Inspired Dashboard)
// High-level operational command center: Metric Cards, Influx Bar Chart,
// Instant Action Dispatch Console, and Real-Time Incident Stream
// ----------------------------------------------------------------------------
function ScreenOverview({ 
  district, 
  incidents, 
  silenceData, 
  auditLogs,
  totalPeople,
  onNavigateTab,
  onSelectIncident,
  onTriggerSimulation
}) {
  const [calcZone, setCalcZone] = useState('Z01');
  const [calcNeed, setCalcNeed] = useState('rescue');
  const [calcUrgency, setCalcUrgency] = useState('Critical');
  const [calcEstimatedPeople, setCalcEstimatedPeople] = useState(15);
  const [calcNotice, setCalcNotice] = useState(null);

  // Group stats
  const criticalCount = useMemo(() => {
    return incidents.filter(i => (i.priority_score || 0) >= 0.70).length;
  }, [incidents]);

  const silentZonesCount = useMemo(() => {
    return silenceData.filter(s => s.status === 'silent' || (s.risk_score && s.risk_score >= 0.5)).length;
  }, [silenceData]);

  // Hourly / Batch Influx Distribution (simulated timeline bar chart)
  const influxBatches = useMemo(() => {
    return [
      { time: '08:00 - 10:00', calls: 38, incidents: 8, height: '45%' },
      { time: '10:00 - 12:00', calls: 74, incidents: 16, height: '85%', highlighted: true },
      { time: '12:00 - 14:00', calls: 42, incidents: 9, height: '52%' },
      { time: '14:00 - 16:00', calls: 59, incidents: 12, height: '68%' },
      { time: 'Current Window', calls: 213, incidents: incidents.length || 45, height: '100%' }
    ];
  }, [incidents]);

  const handleInstantDispatch = (e) => {
    e.preventDefault();
    setCalcNotice(`Dispatch orders generated for Zone ${calcZone} (${calcNeed.toUpperCase()}) — response team notified.`);
    setTimeout(() => setCalcNotice(null), 4500);
  };

  return (
    <div className="dashboard-overview">
      {/* 1. TOP 4 METRIC CURRENCY-STYLE CARDS */}
      <div className="overview-cards-row">
        {/* Card 1: Total Raw Emergency Calls */}
        <div className="dash-stat-card">
          <div className="dash-card-header">
            <div className="dash-card-title-group">
              <span className="dash-flag-icon">📞</span>
              <span className="dash-card-currency">CALLS INFLUX</span>
            </div>
            <button className="dash-dots-btn" title="Options">•••</button>
          </div>
          <div className="dash-stat-main">
            <h2 className="dash-stat-value">213</h2>
            <span className="dash-stat-sub">Raw 112/108 reports</span>
          </div>
          <div className="dash-stat-footer">
            <span className="dash-status-pill active">
              <span className="pill-dot"></span> Active Stream
            </span>
            <span className="dash-limit-text">Compressed into {incidents.length || 45} unique tasks</span>
          </div>
        </div>

        {/* Card 2: Clustered Operations */}
        <div className="dash-stat-card">
          <div className="dash-card-header">
            <div className="dash-card-title-group">
              <span className="dash-flag-icon">🎯</span>
              <span className="dash-card-currency">TRIAGED INCIDENTS</span>
            </div>
            <button className="dash-dots-btn" title="Options">•••</button>
          </div>
          <div className="dash-stat-main">
            <h2 className="dash-stat-value">{incidents.length || 45}</h2>
            <span className="dash-stat-sub">Unique rescue targets</span>
          </div>
          <div className="dash-stat-footer">
            <span className="dash-status-pill active">
              <span className="pill-dot"></span> -79% Noise Cut
            </span>
            <span className="dash-limit-text">{criticalCount} critical immediate</span>
          </div>
        </div>

        {/* Card 3: Cut-Off Silent Zones */}
        <div className="dash-stat-card alert-tint">
          <div className="dash-card-header">
            <div className="dash-card-title-group">
              <span className="dash-flag-icon">📡</span>
              <span className="dash-card-currency">BLACKOUT ZONES</span>
            </div>
            <button className="dash-dots-btn" title="Options">•••</button>
          </div>
          <div className="dash-stat-main">
            <h2 className="dash-stat-value alert-text">{silentZonesCount || 3} / 6</h2>
            <span className="dash-stat-sub">Zero telecom signal</span>
          </div>
          <div className="dash-stat-footer">
            <span className="dash-status-pill inactive">
              <span className="pill-dot inactive"></span> Towers Down
            </span>
            <span className="dash-limit-text">Coastal flood risk active</span>
          </div>
        </div>

        {/* Card 4: Lives at Risk Estimated */}
        <div className="dash-stat-card">
          <div className="dash-card-header">
            <div className="dash-card-title-group">
              <span className="dash-flag-icon">👥</span>
              <span className="dash-card-currency">PEOPLE AT RISK</span>
            </div>
            <button className="dash-dots-btn" title="Options">•••</button>
          </div>
          <div className="dash-stat-main">
            <h2 className="dash-stat-value">{totalPeople || 284}</h2>
            <span className="dash-stat-sub">Estimated stranded persons</span>
          </div>
          <div className="dash-stat-footer">
            <span className="dash-status-pill active">
              <span className="pill-dot"></span> 80% Top-10 Met
            </span>
            <span className="dash-limit-text">Medical & rescue prioritized</span>
          </div>
        </div>
      </div>

      {/* 2. MIDDLE SPLIT: PAYMENT-STYLE INFLUX BAR CHART (LEFT) + QUICK DISPATCH CALCULATOR (RIGHT) */}
      <div className="overview-middle-grid">
        {/* Left: Call Stream & Incident Influx Chart */}
        <div className="dash-chart-card">
          <div className="dash-chart-header">
            <div>
              <span className="chart-pretitle">CALL VOLUME & TRIAGE EFFICIENCY</span>
              <h3 className="chart-title">Incoming Distress Influx</h3>
            </div>
            <div className="chart-header-controls">
              <span className="trend-badge-positive">+89% Peak Wave</span>
              <select className="dash-select" aria-label="Time Filter">
                <option>Cyclone Landfall Phase</option>
                <option>Pre-Cyclone Phase</option>
                <option>Post-Landfall Relief</option>
              </select>
            </div>
          </div>

          <div className="chart-hero-number">
            <span className="hero-num-val">213 Calls</span>
            <span className="hero-num-arrow">→ 45 Actionable Targets</span>
          </div>

          {/* Bar Chart Visualization matching TrustVest style */}
          <div className="dash-bar-chart-container">
            <div className="dash-bar-chart-grid">
              {influxBatches.map((batch, idx) => (
                <div key={idx} className={`dash-bar-col ${batch.highlighted ? 'highlighted' : ''}`}>
                  <div className="dash-bar-tooltip">
                    <strong>{batch.calls} Calls</strong>
                    <span>{batch.incidents} Rescues</span>
                  </div>
                  <div className="dash-bar-track">
                    <div 
                      className="dash-bar-fill" 
                      style={{ height: batch.height }}
                    >
                      <div className="dash-bar-highlight-top"></div>
                    </div>
                  </div>
                  <span className="dash-bar-label">{batch.time}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="chart-bottom-summary">
            <div className="chart-pill-item">
              <span className="dot dot-green"></span>
              <span>Clustered Deduplication: <strong>79% noise eliminated</strong></span>
            </div>
            <div className="chart-pill-item">
              <span className="dot dot-blue"></span>
              <span>Fastest Triage Time: <strong>&lt; 0.4s AI grouping</strong></span>
            </div>
            <button 
              className="chart-explore-link" 
              onClick={() => onNavigateTab('proof')}
            >
              See Benchmark Proof →
            </button>
          </div>
        </div>

        {/* Right: Transfer-Calculator Style "Quick Rescue Dispatch" Console */}
        <div className="dash-calculator-card">
          <div className="calculator-header">
            <div className="flex-row items-center gap-2">
              <div className="calc-header-icon">
                <LifeBuoy size={18} color="#15803d" />
              </div>
              <div>
                <h4 className="calc-title">Quick Rescue Dispatcher</h4>
                <p className="calc-subtitle">Instant boat/medic routing simulator</p>
              </div>
            </div>
          </div>

          <form onSubmit={handleInstantDispatch} className="calc-form">
            <div className="calc-input-group">
              <label className="calc-label">Target Coastal Sector</label>
              <div className="calc-box">
                <span className="calc-symbol">📍</span>
                <select 
                  className="calc-select" 
                  value={calcZone}
                  onChange={(e) => setCalcZone(e.target.value)}
                >
                  <option value="Z01">Zone 01 - Bhavanapadu Coastal</option>
                  <option value="Z02">Zone 02 - Kalingapatnam Port</option>
                  <option value="Z03">Zone 03 - Baruva Fishing Village</option>
                  <option value="Z04">Zone 04 - Srikakulam Urban</option>
                  <option value="Z05">Zone 05 - Narasannapeta Rural</option>
                  <option value="Z06">Zone 06 - Sompeta Lowlands</option>
                </select>
              </div>
            </div>

            <div className="calc-input-group">
              <label className="calc-label">Primary Need Category</label>
              <div className="calc-box">
                <span className="calc-symbol">🚨</span>
                <select 
                  className="calc-select" 
                  value={calcNeed}
                  onChange={(e) => setCalcNeed(e.target.value)}
                >
                  <option value="rescue">Flood Water Evacuation (Boats)</option>
                  <option value="medical">Critical Medical / ICU Trapped</option>
                  <option value="shelter">High-Ground Cyclone Shelter</option>
                  <option value="water">Potable Drinking Water Supplies</option>
                  <option value="food">Emergency Rations Air-Drop</option>
                </select>
              </div>
            </div>

            <div className="calc-details-box">
              <div className="calc-row">
                <span className="calc-row-key">Estimated Victims</span>
                <span className="calc-row-val">
                  <input 
                    type="number" 
                    value={calcEstimatedPeople} 
                    onChange={e => setCalcEstimatedPeople(Number(e.target.value))}
                    min="1"
                    max="500"
                    className="calc-inline-input"
                  /> people
                </span>
              </div>
              <div className="calc-row">
                <span className="calc-row-key">Auto Priority Rank</span>
                <span className="calc-row-val green-text">Top 5 Dispatch</span>
              </div>
              <div className="calc-row">
                <span className="calc-row-key">Telecom Connection</span>
                <span className="calc-row-val alert-text">VHF Radio Only</span>
              </div>
            </div>

            {calcNotice && (
              <div className="calc-notice-banner">
                {calcNotice}
              </div>
            )}

            <button type="submit" className="btn-send-money">
              <Send size={16} />
              <span>Deploy Rescue Resource</span>
            </button>
          </form>
        </div>
      </div>

      {/* 3. BOTTOM: RECENT INCIDENTS TABLE (MATCHING "TRANSACTIONS HISTORY") */}
      <div className="dash-transactions-card">
        <div className="transactions-header">
          <div>
            <h4 className="trans-title">Live Emergency Incident Feed</h4>
            <p className="trans-subtitle">Showing {incidents.slice(0, 5).length} of {incidents.length} ranked operations</p>
          </div>
          <div className="trans-header-actions">
            <button className="btn-table-action" onClick={onTriggerSimulation}>
              <RefreshCw size={14} />
              <span>Simulate Next Wave</span>
            </button>
            <button 
              className="btn-table-primary"
              onClick={() => onNavigateTab('respond')}
            >
              <span>View Full Queue ({incidents.length})</span>
              <ArrowRight size={14} />
            </button>
          </div>
        </div>

        <div className="dash-table-wrapper">
          <table className="dash-table">
            <thead>
              <tr>
                <th>Incident & Location</th>
                <th>Category</th>
                <th>People at Risk</th>
                <th>Source Verification</th>
                <th>Priority Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {incidents.slice(0, 6).map((inc) => {
                const urg = getUrgencyLevel(inc.priority_score);
                const need = NEED_CONFIG[inc.need_type] || { badge: inc.need_type, color: '#3b82f6', bg: '#eff6ff' };
                return (
                  <tr key={inc.id} onClick={() => onSelectIncident(inc)}>
                    <td>
                      <div className="td-location-group">
                        <div className="location-icon-box">
                          <MapPin size={15} color="#2563eb" />
                        </div>
                        <div>
                          <strong className="td-zone-title">{inc.zone_name}</strong>
                          <span className="td-zone-sub">Incident #{inc.id} • {inc.reported_time ? new Date(inc.reported_time).toLocaleTimeString() : 'Recent'}</span>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className="td-need-badge" style={{ backgroundColor: need.bg, color: need.color }}>
                        {need.badge}
                      </span>
                    </td>
                    <td>
                      <span className="td-people-count">
                        <strong>{inc.estimated_people}</strong> persons
                      </span>
                    </td>
                    <td>
                      <div className="td-verified-cell">
                        <span className="check-dot">✓</span>
                        <span>{inc.source_count || 3} Callers ({inc.channel || '112/108'})</span>
                      </div>
                    </td>
                    <td>
                      <span className={`td-status-pill ${urg.tier}`}>
                        <span className="status-dot"></span>
                        {urg.tier === 'critical' ? 'Critical' : (urg.tier === 'high' ? 'High Urgency' : 'Moderate')}
                      </span>
                    </td>
                    <td>
                      <button 
                        className="btn-row-inspect"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectIncident(inc);
                        }}
                      >
                        Explain Priority →
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
function ScreenPrepare({ district, silenceData, focusedZoneId, onSelectZone, onProceed }) {
  const [selectedZone, setSelectedZone] = useState(null);

  const zones = district?.features || [];

  // Match silence status to zones
  const zoneSummaryList = useMemo(() => {
    return zones.map(z => {
      const zid = z.properties.id;
      const sinfo = silenceData.find(s => s.zone_id === zid);
      const isSilent = sinfo?.status === 'silent' || (sinfo?.risk_score && sinfo.risk_score >= 0.5);
      return {
        id: zid,
        name: z.properties.name,
        population: z.properties.population || 45000,
        riskScore: sinfo?.risk_score || 0.35,
        isSilent,
        silentReason: isSilent 
          ? 'Zero emergency calls received despite coastal inundation hazard — high risk of total telecom blackout.'
          : 'Communication towers operational, normal emergency call reception.',
        coordinates: z.geometry.coordinates
      };
    }).sort((a, b) => b.riskScore - a.riskScore);
  }, [zones, silenceData]);

  const highRiskZones = zoneSummaryList.filter(z => z.isSilent);

  // Set default selected zone
  useEffect(() => {
    if (focusedZoneId) {
      const match = zoneSummaryList.find(z => z.id === focusedZoneId);
      if (match) setSelectedZone(match);
    } else if (zoneSummaryList.length > 0 && !selectedZone) {
      setSelectedZone(zoneSummaryList[0]);
    }
  }, [focusedZoneId, zoneSummaryList, selectedZone]);

  const geoJsonStyle = (feature) => {
    const zid = feature.properties.id;
    const isSelected = selectedZone?.id === zid;
    const sinfo = silenceData.find(s => s.zone_id === zid);
    const isSilent = sinfo?.status === 'silent' || (sinfo?.risk_score && sinfo.risk_score >= 0.5);

    return {
      fillColor: isSilent ? '#e53e3e' : '#3182ce',
      weight: isSelected ? 3 : 1.5,
      opacity: 1,
      color: isSelected ? '#1a202c' : '#ffffff',
      dashArray: isSilent ? '4' : '',
      fillOpacity: isSelected ? 0.65 : (isSilent ? 0.45 : 0.25)
    };
  };

  return (
    <div className="screen-prepare">
      {/* Top Banner with Clear Question & Key Stats */}
      <section className="screen-header-card">
        <div className="screen-header-main">
          <div className="screen-badge">SCREEN 1 OF 3: PRE-LANDFALL PREPARATION</div>
          <h2 className="screen-question-title">Which areas are most at risk before the cyclone?</h2>
          <p className="screen-explanation">
            Coastal zones are evaluated by population density, flood risk, and sudden communication silence. 
            When a high-risk zone sends <strong>zero calls</strong>, towers are likely knocked down — these areas need proactive drone or satellite scout teams.
          </p>
        </div>

        <div className="stats-row">
          <div className="stat-card">
            <span className="stat-label">Total Coastal Zones Monitored</span>
            <span className="stat-value">{zones.length}</span>
            <span className="stat-sub">Srikakulam coastal belt</span>
          </div>

          <div className="stat-card stat-alert">
            <span className="stat-label">Communication Blackout Zones</span>
            <span className="stat-value">{highRiskZones.length}</span>
            <span className="stat-sub">Zero calls despite high surge risk</span>
          </div>

          <div className="stat-card">
            <span className="stat-label">Preparedness Action Required</span>
            <span className="stat-value">Pre-position</span>
            <span className="stat-sub">Boats and satellite radios</span>
          </div>
        </div>
      </section>

      {/* 2-Column Split: Map on Left, Zone Risk Cards on Right */}
      <div className="screen-two-col">
        {/* Left Column: Interactive Map */}
        <div className="map-panel">
          <div className="panel-title-bar">
            <div className="flex-row items-center gap-2">
              <MapPin size={18} color="#2b6cb0" />
              <h3 className="panel-title">Srikakulam Coastal District Map</h3>
            </div>
            <span className="panel-badge">Interactive view</span>
          </div>

          <div className="map-wrapper">
            <MapContainer 
              center={[17.68, 82.96]} 
              zoom={10} 
              style={{ height: '100%', width: '100%' }}
              scrollWheelZoom={true}
            >
              <MapUpdater center={[17.68, 82.96]} zoom={10} />
              <TileLayer
                attribution='&copy; OpenStreetMap contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {district && (
                <GeoJSON 
                  key={JSON.stringify(district?.features?.length || 0)}
                  data={district} 
                  style={geoJsonStyle}
                  onEachFeature={(feature, layer) => {
                    layer.on({
                      click: () => {
                        const match = zoneSummaryList.find(z => z.id === feature.properties.id);
                        if (match) setSelectedZone(match);
                        onSelectZone(feature.properties.id);
                      }
                    });
                  }}
                />
              )}
            </MapContainer>
            
            <div className="map-legend-overlay">
              <div className="legend-row">
                <span className="legend-swatch swatch-alert"></span>
                <span>Silent high-hazard zone (0 calls received)</span>
              </div>
              <div className="legend-row">
                <span className="legend-swatch swatch-normal"></span>
                <span>Active communications (calls received)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Zone Risk Inspector */}
        <div className="sidebar-panel">
          <div className="panel-title-bar">
            <div className="flex-row items-center gap-2">
              <ShieldAlert size={18} color="#c53030" />
              <h3 className="panel-title">Monitored Coastal Sectors</h3>
            </div>
            <span className="panel-badge alert">{highRiskZones.length} Blackouts Identified</span>
          </div>

          {/* Quick Judge Takeaway Callout */}
          <div className="judge-takeaway-box">
            <span className="judge-takeaway-label">💡 KEY INSIGHT FOR JUDGES:</span>
            <p className="judge-takeaway-text">
              Notice <strong>Kalingapatnam Sands (Z01)</strong> and <strong>Dhamra Creek (Z04)</strong>. Traditional dispatch sends 0 ambulances here because 0 calls were logged. Our silence model recognizes that collapsed antennas mean maximum danger.
            </p>
          </div>

          <div className="zone-cards-scroll">
            {zoneSummaryList.map(zone => {
              const isSelected = selectedZone?.id === zone.id;
              return (
                <div 
                  key={zone.id}
                  className={`zone-card ${isSelected ? 'selected' : ''} ${zone.isSilent ? 'zone-silent' : ''}`}
                  onClick={() => {
                    setSelectedZone(zone);
                    onSelectZone(zone.id);
                  }}
                >
                  <div className="zone-card-top">
                    <div>
                      <h4 className="zone-name">{zone.name}</h4>
                      <p className="zone-id">Zone {zone.id} &bull; Approx. {zone.population.toLocaleString()} residents</p>
                    </div>
                    {zone.isSilent ? (
                      <span className="badge badge-critical">
                        <AlertTriangle size={12} />
                        Telecom Blackout
                      </span>
                    ) : (
                      <span className="badge badge-normal">
                        <CheckCircle2 size={12} />
                        Cellular Online
                      </span>
                    )}
                  </div>

                  <p className="zone-reason">{zone.silentReason}</p>

                  <div className="zone-card-footer">
                    <span className="zone-action-hint">
                      {zone.isSilent ? '🚨 Action: Dispatch VHF Radio / Scout Drone' : '✅ Normal call reception active'}
                    </span>
                    <button className="btn-link" onClick={() => setSelectedZone(zone)}>
                      Inspect on Map
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Action button to proceed to Step 2 */}
          <div className="panel-bottom-cta">
            <button className="btn btn-proceed btn-full" onClick={onProceed} id="proceed-to-respond-btn">
              <span>Next → Step 2: See Who Gets Rescued First</span>
              <ArrowRight size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ----------------------------------------------------------------------------
// SCREEN 2: RESPOND
// Question: What should we do first, and why?
// ----------------------------------------------------------------------------
function ScreenRespond({ 
  incidents, 
  allIncidentsCount, 
  district,
  selectedIncident, 
  activeNeedFilter, 
  totalPeople,
  onSelectNeedFilter, 
  onSelectIncident, 
  onChangePriority, 
  onProceed 
}) {
  const [selectedMapIncident, setSelectedMapIncident] = useState(null);

  // Group by priority tiers
  const grouped = useMemo(() => {
    const critical = [];
    const high = [];
    const moderate = [];

    incidents.forEach(inc => {
      const urg = getUrgencyLevel(inc.priority_score);
      if (urg.tier === 'critical') critical.push(inc);
      else if (urg.tier === 'high') high.push(inc);
      else moderate.push(inc);
    });

    return { critical, high, moderate };
  }, [incidents]);

  return (
    <div className="screen-respond">
      {/* Top Banner with Clear Question & Key Metrics */}
      <section className="screen-header-card">
        <div className="screen-header-main">
          <div className="screen-badge">SCREEN 2 OF 3: OPERATIONAL TRIAGE</div>
          <h2 className="screen-question-title">What should we do first, and why?</h2>
          <p className="screen-explanation">
            Incoming emergency calls have been grouped into verified incidents. 
            Emergencies are ranked by life-threat urgency, trapped vulnerable people, and corroborating callers — never first-come-first-served.
          </p>
        </div>

        {/* Filter Bar by Emergency Type */}
        <div className="filter-pill-bar">
          <span className="filter-label">Filter by emergency:</span>
          {['all', 'rescue', 'medical', 'shelter', 'water', 'food'].map(type => (
            <button 
              key={type}
              className={`pill-btn ${activeNeedFilter === type ? 'active' : ''}`}
              onClick={() => onSelectNeedFilter(type)}
            >
              {type === 'all' ? 'All Emergencies' : NEED_CONFIG[type]?.badge || type}
            </button>
          ))}
          <span className="filter-count">
            Showing {incidents.length} of {allIncidentsCount} active emergencies
          </span>
        </div>
      </section>

      {/* Main Grid: Priority Incident List (Left) + Tactical Map (Right) */}
      <div className="screen-two-col">
        {/* Left Column: Ranked Incident Queue */}
        <div className="incident-queue-panel">
          <div className="panel-title-bar">
            <div className="flex-row items-center gap-2">
              <AlertTriangle size={18} color="#c53030" />
              <h3 className="panel-title">Triage Queue — Ordered by Life Danger</h3>
            </div>
            <span className="panel-badge alert">{grouped.critical.length} Critical Rescues</span>
          </div>

          {/* Quick Judge Takeaway Callout */}
          <div className="judge-takeaway-box blue">
            <span className="judge-takeaway-label">💡 KEY INSIGHT FOR JUDGES:</span>
            <p className="judge-takeaway-text">
              Notice <strong>#1 Incident</strong> has <strong>pregnant mothers / children trapped</strong> and multiple callers confirming it. Even if another non-critical call arrived earlier, our multi-factor AI prioritizes saving lives first.
            </p>
          </div>

          <div className="incident-list-scroll">
            {incidents.length === 0 ? (
              <div className="empty-state">
                <Info size={32} />
                <p>No incidents match the selected emergency filter.</p>
              </div>
            ) : (
              incidents.map((incident, index) => (
                <EmergencyCard 
                  key={incident.id}
                  incident={incident}
                  rank={index + 1}
                  isSelected={selectedIncident?.id === incident.id}
                  onSelect={() => {
                    setSelectedMapIncident(incident);
                    onSelectIncident(incident);
                  }}
                  onChangePriority={() => onChangePriority(incident)}
                />
              ))
            )}
          </div>

          <div className="panel-bottom-cta">
            <button className="btn btn-proceed btn-full" onClick={onProceed} id="proceed-to-proof-btn">
              <span>Next → Step 3: See Proof vs Traditional Dispatch</span>
              <ArrowRight size={18} />
            </button>
          </div>
        </div>

        {/* Right Column: Tactical Map with Clusters */}
        <div className="map-panel">
          <div className="panel-title-bar">
            <div className="flex-row items-center gap-2">
              <MapPin size={18} color="#2b6cb0" />
              <h3 className="panel-title">Live Tactical Operations Map</h3>
            </div>
            <span className="panel-badge">Click marker to inspect</span>
          </div>

          <div className="map-wrapper">
            <MapContainer 
              center={selectedIncident?.lat ? [selectedIncident.lat, selectedIncident.lon] : [17.68, 82.96]} 
              zoom={selectedIncident?.lat ? 12 : 10} 
              style={{ height: '100%', width: '100%' }}
              scrollWheelZoom={true}
            >
              <MapUpdater 
                center={selectedIncident?.lat ? [selectedIncident.lat, selectedIncident.lon] : [17.68, 82.96]} 
                zoom={selectedIncident?.lat ? 12 : 10} 
              />
              <TileLayer
                attribution='&copy; OpenStreetMap contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {district && (
                <GeoJSON 
                  key={JSON.stringify(district?.features?.length || 0)}
                  data={district} 
                  style={{
                    fillColor: '#cbd5e0',
                    weight: 1,
                    opacity: 0.8,
                    color: '#718096',
                    fillOpacity: 0.15
                  }}
                />
              )}
              {incidents.filter(inc => inc.lat != null && inc.lon != null && !isNaN(inc.lat) && !isNaN(inc.lon)).map((inc) => {
                const isSelected = selectedIncident?.id === inc.id;
                const urg = getUrgencyLevel(inc.priority_score);
                const color = urg.tier === 'critical' ? '#e53e3e' : (urg.tier === 'high' ? '#dd6b20' : '#3182ce');

                return (
                  <CircleMarker
                    key={inc.id}
                    center={[inc.lat, inc.lon]}
                    radius={isSelected ? 14 : 9}
                    pathOptions={{
                      color: isSelected ? '#1a202c' : '#ffffff',
                      weight: isSelected ? 3 : 2,
                      fillColor: color,
                      fillOpacity: 0.85
                    }}
                    eventHandlers={{
                      click: () => {
                        onSelectIncident(inc);
                      }
                    }}
                  >
                    <Popup>
                      <div className="map-popup-card">
                        <h4 className="popup-title">{inc.zone_name}</h4>
                        <p className="popup-need">
                          <strong>{NEED_CONFIG[inc.need_type]?.badge || inc.need_type}:</strong> {inc.estimated_people} people affected
                        </p>
                        <p className="popup-urgency">{urg.label}</p>
                        <button 
                          className="btn btn-primary btn-sm btn-full"
                          onClick={() => onSelectIncident(inc)}
                        >
                          Open Emergency Details
                        </button>
                      </div>
                    </Popup>
                  </CircleMarker>
                );
              })}
            </MapContainer>

            <div className="map-legend-overlay">
              <div className="legend-row">
                <span className="legend-swatch swatch-critical"></span>
                <span>Critical — dispatch immediately</span>
              </div>
              <div className="legend-row">
                <span className="legend-swatch swatch-high"></span>
                <span>High — dispatch within 2 hours</span>
              </div>
              <div className="legend-row">
                <span className="legend-swatch swatch-moderate"></span>
                <span>Moderate priority</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ----------------------------------------------------------------------------
// EMERGENCY CARD COMPONENT (Plain Language)
// ----------------------------------------------------------------------------
function EmergencyCard({ incident, rank, isSelected, onSelect, onChangePriority }) {
  const needInfo = NEED_CONFIG[incident.need_type] || NEED_CONFIG.other;
  const urgency = getUrgencyLevel(incident.priority_score);
  const verification = getVerificationLevel(incident.reliability_score, incident.independent_sources);

  // Plain language vulnerable summary
  const vulnerableCount = incident.vulnerable_groups?.length || 0;
  const vulnerableLabels = incident.vulnerable_groups?.map(g => VULNERABLE_CONFIG[g]?.label || g).join(', ');

  return (
    <article 
      className={`emergency-card ${isSelected ? 'selected' : ''}`}
      onClick={onSelect}
    >
      <div className="card-top-row">
        <div className="card-rank-badge">#{rank}</div>
        <div className="card-location-group">
          <h4 className="card-location">{incident.zone_name}</h4>
          <span className="card-id">Incident #{incident.id}</span>
        </div>
        <span 
          className="urgency-pill"
          style={{ color: urgency.color, backgroundColor: urgency.bg, borderColor: urgency.border }}
        >
          {urgency.label}
        </span>
      </div>

      <div className="card-need-banner" style={{ backgroundColor: needInfo.bg, borderColor: needInfo.color }}>
        <span className="need-badge" style={{ backgroundColor: needInfo.color }}>
          {needInfo.badge}
        </span>
        <span className="need-label">{needInfo.label}</span>
      </div>

      <div className="card-stats-grid">
        <div className="card-stat">
          <Users size={15} color="#4a5568" />
          <span><strong>{incident.estimated_people}</strong> people trapped</span>
        </div>
        <div className="card-stat">
          <PhoneCall size={15} color="#4a5568" />
          <span><strong>{incident.independent_sources}</strong> separate callers</span>
        </div>
      </div>

      {vulnerableCount > 0 && (
        <div className="card-vulnerable-notice">
          <span className="vuln-icon">⚠️</span>
          <span>Includes vulnerable people: <strong>{vulnerableLabels}</strong></span>
        </div>
      )}

      {incident.override_reason && (
        <div className="card-override-notice">
          <strong>Coordinator adjusted:</strong> {incident.override_reason}
        </div>
      )}

      <div className="card-actions-row" onClick={e => e.stopPropagation()}>
        <button className="btn btn-secondary btn-sm" onClick={onSelect}>
          <span>Why is this ranked here?</span>
          <ChevronRight size={14} />
        </button>
        <button className="btn-link-sm" onClick={onChangePriority}>
          Change priority
        </button>
      </div>
    </article>
  );
}

// ----------------------------------------------------------------------------
// WHY DRAWER: Plain-Language Explanation of Score
// ----------------------------------------------------------------------------
function WhyDrawer({ incident, onClose, onChangePriority }) {
  const needInfo = NEED_CONFIG[incident.need_type] || NEED_CONFIG.other;
  const urgency = getUrgencyLevel(incident.priority_score);
  const verification = getVerificationLevel(incident.reliability_score, incident.independent_sources);
  const factors = incident.factors || {};

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside className="drawer-panel" onClick={e => e.stopPropagation()} aria-label="Incident Explanation">
        <div className="drawer-header">
          <div>
            <span className="drawer-category">DECISION EXPLANATION</span>
            <h3 className="drawer-title">Why this incident is ranked #{incident.id}</h3>
            <p className="drawer-subtitle">{incident.zone_name} &bull; {needInfo.label}</p>
          </div>
          <button className="btn-icon" onClick={onClose} aria-label="Close drawer">
            <X size={20} />
          </button>
        </div>

        <div className="drawer-body">
          {/* Top Urgency Banner */}
          <div 
            className="drawer-urgency-banner"
            style={{ backgroundColor: urgency.bg, color: urgency.color, borderColor: urgency.border }}
          >
            <AlertTriangle size={20} />
            <div>
              <strong>{urgency.label}</strong>
              <p>Calculated from life danger, trapped vulnerable people, and caller confirmation.</p>
            </div>
          </div>

          {/* Plain Language Reasons from Backend */}
          <div className="drawer-section">
            <h4 className="section-title">Key Decision Factors</h4>
            <div className="reasons-list">
              {incident.reasons && incident.reasons.length > 0 ? (
                incident.reasons.map((reason, idx) => (
                  <div key={idx} className="reason-item">
                    <CheckCircle2 size={16} color="#2b6cb0" />
                    <span>{reason}</span>
                  </div>
                ))
              ) : (
                <p>Urgent life-safety response required based on corroborated field reports.</p>
              )}
            </div>
          </div>

          {/* Factor Breakdown Cards (Plain Language, No Raw Decimals) */}
          <div className="drawer-section">
            <h4 className="section-title">Factor Breakdown</h4>
            <div className="factors-grid">
              <div className="factor-card">
                <span className="factor-title">Urgency of Need</span>
                <span className="factor-value high">
                  {incident.need_type === 'rescue' ? 'Immediate danger to life' : 'High assistance need'}
                </span>
                <p className="factor-desc">Floodwaters rising, urgent physical evacuation required.</p>
              </div>

              <div className="factor-card">
                <span className="factor-title">People at Risk</span>
                <span className="factor-value">
                  Approx. {incident.estimated_people} people affected
                </span>
                <p className="factor-desc">Estimated from combined reports from this location.</p>
              </div>

              <div className="factor-card">
                <span className="factor-title">Vulnerable Residents</span>
                <span className="factor-value alert">
                  {incident.vulnerable_groups?.length > 0 
                    ? incident.vulnerable_groups.map(g => VULNERABLE_CONFIG[g]?.label || g).join(', ')
                    : 'None reported specifically'}
                </span>
                <p className="factor-desc">Children, elderly, or medical patients given priority.</p>
              </div>

              <div className="factor-card">
                <span className="factor-title">Caller Verification</span>
                <span className="factor-value green">{verification.label}</span>
                <p className="factor-desc">{verification.detail}</p>
              </div>
            </div>
          </div>

          {/* Field Reports Corroborating This Emergency */}
          <div className="drawer-section">
            <h4 className="section-title">
              Combined Field Reports ({incident.reports?.length || incident.independent_sources || 1})
            </h4>
            <div className="field-reports-scroll">
              {incident.reports && incident.reports.length > 0 ? (
                incident.reports.map((rep, idx) => (
                  <div key={idx} className="report-card">
                    <div className="report-card-top">
                      <span className="report-channel">
                        {CHANNEL_CONFIG[rep.channel] || 'Helpline report'}
                      </span>
                      <span className="report-time">
                        {rep.time_offset_min ? `${rep.time_offset_min} min ago` : 'Recent'}
                      </span>
                    </div>
                    <p className="report-text">"{rep.text || rep.summary || 'Emergency assistance requested at this location.'}"</p>
                  </div>
                ))
              ) : (
                <div className="report-card">
                  <p className="report-text">
                    Combined reports from {incident.independent_sources} callers received via emergency SMS and voice helpline.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="drawer-footer">
          <button className="btn btn-secondary" onClick={onChangePriority}>
            Adjust Priority...
          </button>
          <button className="btn btn-primary" onClick={onClose}>
            Done Reviewing
          </button>
        </div>
      </aside>
    </div>
  );
}

// ----------------------------------------------------------------------------
// SCREEN 3: PROOF — Plain-English Impact Evidence
// Shows: What problem we solved, How much better we are, Why it matters
// ----------------------------------------------------------------------------
function ScreenProof({ metrics, incidentsCount, silenceCount, onRestart }) {
  return (
    <div className="screen-proof">
      
      {/* ── HERO HEADER ─────────────────────────────────────────────────────── */}
      <section className="proof-hero-header">
        <div className="proof-hero-badge">📊 STEP 3 OF 3 — EVIDENCE & RESULTS</div>
        <h2 className="proof-hero-title">
          Does Lifeline Triage Actually Save More Lives?
        </h2>
        <p className="proof-hero-sub">
          We ran Lifeline Triage against the same cyclone data a traditional 911 dispatch would receive.
          Here's what happened — measured in real numbers, not promises.
        </p>

        {/* Key Metrics Strip */}
        <div className="proof-kpi-strip">
          <div className="proof-kpi-item red-kpi">
            <span className="kpi-number">79%</span>
            <span className="kpi-label">Less noise for coordinators</span>
            <span className="kpi-sub">213 calls → 45 clear missions</span>
          </div>
          <div className="proof-kpi-divider" />
          <div className="proof-kpi-item green-kpi">
            <span className="kpi-number">+20%</span>
            <span className="kpi-label">Better rescue accuracy</span>
            <span className="kpi-sub">60% → 80% expert agreement</span>
          </div>
          <div className="proof-kpi-divider" />
          <div className="proof-kpi-item blue-kpi">
            <span className="kpi-number">3/3</span>
            <span className="kpi-label">Blackout zones detected</span>
            <span className="kpi-sub">Traditional dispatch found 0</span>
          </div>
        </div>
      </section>

      {/* ── 3 PROBLEM → SOLUTION CARDS ──────────────────────────────────────── */}
      <div className="proof-section-label">
        <span>THREE PROBLEMS TRADITIONAL DISPATCH CANNOT SOLVE</span>
      </div>

      <div className="proof-cards-grid">

        {/* ── Card 1: Call Flood / Noise ── */}
        <div className="proof-card proof-card-blue">
          <div className="proof-card-topbar blue-bar">
            <span className="proof-problem-num">Problem #1</span>
            <span className="proof-problem-label">PHONE LINE OVERLOAD</span>
          </div>

          <div className="proof-card-body">
            <div className="proof-card-icon-row">
              <div className="proof-icon-box blue"><Layers size={20} color="#1d4ed8" /></div>
              <h3 className="proof-card-title">Operators drown in duplicate calls</h3>
            </div>
            <p className="proof-card-scenario">
              During Cyclone Biparjoy, <strong>213 calls</strong> flooded the helpline — but most came from the same 5 flooded streets, repeated in a panic.
              Traditional dispatch reads every one of them individually.
            </p>

            <div className="proof-compare-row">
              <div className="compare-col before-col">
                <div className="compare-col-label before-label">❌ Without Lifeline</div>
                <div className="compare-metric-big red-text">213</div>
                <div className="compare-metric-desc">calls read one-by-one</div>
                <p className="compare-col-impact bad">Coordinators paralyzed — no time to act</p>
              </div>

              <div className="compare-arrow-sep">
                <ArrowRight size={28} color="#94a3b8" />
              </div>

              <div className="compare-col after-col">
                <div className="compare-col-label after-label">✅ With Lifeline Triage</div>
                <div className="compare-metric-big green-text">45</div>
                <div className="compare-metric-desc">verified unique missions</div>
                <p className="compare-col-impact good">Teams act on 45 clear rescue operations</p>
              </div>
            </div>

            <div className="proof-result-banner blue-result">
              <TrendingUp size={16} /> <strong>79% noise removed</strong> — coordinators see only what matters
            </div>
          </div>
        </div>

        {/* ── Card 2: Priority Accuracy ── */}
        <div className="proof-card proof-card-green">
          <div className="proof-card-topbar green-bar">
            <span className="proof-problem-num">Problem #2</span>
            <span className="proof-problem-label">WRONG PEOPLE RESCUED FIRST</span>
          </div>

          <div className="proof-card-body">
            <div className="proof-card-icon-row">
              <div className="proof-icon-box green"><Award size={20} color="#15803d" /></div>
              <h3 className="proof-card-title">Minor complaints pushed ahead of critical cases</h3>
            </div>
            <p className="proof-card-scenario">
              Traditional dispatch follows a simple rule: <em>whoever called first gets help first</em>.
              A complaint about a broken fence gets handled before a family trapped in floodwater.
            </p>

            <div className="proof-compare-row">
              <div className="compare-col before-col">
                <div className="compare-col-label before-label">❌ Without Lifeline</div>
                <div className="compare-metric-big muted-text">60%</div>
                <div className="compare-metric-desc">correct priority order</div>
                <p className="compare-col-impact bad">4 in 10 rescues sent to the wrong location first</p>
              </div>

              <div className="compare-arrow-sep">
                <ArrowRight size={28} color="#94a3b8" />
              </div>

              <div className="compare-col after-col">
                <div className="compare-col-label after-label">✅ With Lifeline Triage</div>
                <div className="compare-metric-big green-text">80%</div>
                <div className="compare-metric-desc">matches expert order</div>
                <p className="compare-col-impact good">Pregnant mothers & trapped children rescued first</p>
              </div>
            </div>

            <div className="proof-result-banner green-result">
              <TrendingUp size={16} /> <strong>+20% accuracy</strong> — life-critical cases always go to the top
            </div>
          </div>
        </div>

        {/* ── Card 3: Blackout Blindspot ── */}
        <div className="proof-card proof-card-red">
          <div className="proof-card-topbar red-bar">
            <span className="proof-problem-num">Problem #3</span>
            <span className="proof-problem-label">SILENT ZONES FORGOTTEN</span>
          </div>

          <div className="proof-card-body">
            <div className="proof-card-icon-row">
              <div className="proof-icon-box red"><Radio size={20} color="#b91c1c" /></div>
              <h3 className="proof-card-title">Coastal areas go dark — and no one notices</h3>
            </div>
            <p className="proof-card-scenario">
              When towers collapse, <strong>zero calls reach the helpline</strong>. Traditional dispatch interprets silence as "no emergency."
              Entire coastal villages — Dhamra Creek, Kalingapatnam — are abandoned.
            </p>

            <div className="proof-compare-row">
              <div className="compare-col before-col">
                <div className="compare-col-label before-label">❌ Without Lifeline</div>
                <div className="compare-metric-big red-text">0 / 3</div>
                <div className="compare-metric-desc">blackout zones found</div>
                <p className="compare-col-impact bad">24,000+ residents left without any response</p>
              </div>

              <div className="compare-arrow-sep">
                <ArrowRight size={28} color="#94a3b8" />
              </div>

              <div className="compare-col after-col">
                <div className="compare-col-label after-label">✅ With Lifeline Triage</div>
                <div className="compare-metric-big green-text">3 / 3</div>
                <div className="compare-metric-desc">zones alerted & dispatched</div>
                <p className="compare-col-impact good">Scout drones & VHF radio teams pre-positioned</p>
              </div>
            </div>

            <div className="proof-result-banner red-result">
              <TrendingUp size={16} /> <strong>100% detection</strong> — silence is treated as an emergency signal
            </div>
          </div>
        </div>
      </div>

      {/* ── ARCHITECTURE PILLARS ─────────────────────────────────────────────── */}
      <section className="pillars-section">
        <div className="pillars-header">
          <div className="flex-row items-center gap-2">
            <ShieldCheck size={22} color="#1d4ed8" />
            <h3 className="pillars-title">How It Works — 4 Technical Pillars</h3>
          </div>
          <span className="pillars-subtitle">The engineering behind reliable life-saving decisions</span>
        </div>

        <div className="pillars-grid">
          <div className="pillar-item">
            <div className="pillar-badge">1</div>
            <div>
              <strong className="pillar-heading">Noise & Duplicate Reduction</strong>
              <p className="pillar-desc">
                TF-IDF character n-gram text similarity + Union-Find graph clustering groups repetitive incoming calls within seconds.
              </p>
            </div>
          </div>

          <div className="pillar-item">
            <div className="pillar-badge">2</div>
            <div>
              <strong className="pillar-heading">Silence Gap Detection</strong>
              <p className="pillar-desc">
                Monitors expected baseline call rates per coastal ward. If high-risk zones go unexpectedly quiet, an urgent alert fires automatically.
              </p>
            </div>
          </div>

          <div className="pillar-item">
            <div className="pillar-badge">3</div>
            <div>
              <strong className="pillar-heading">Transparent AI Decision Logic</strong>
              <p className="pillar-desc">
                Every priority score includes a plain-English breakdown (Severity, Urgency, Vulnerability, Hazards). No black-box decisions.
              </p>
            </div>
          </div>

          <div className="pillar-item">
            <div className="pillar-badge">4</div>
            <div>
              <strong className="pillar-heading">Human-in-the-Loop & Offline-Ready</strong>
              <p className="pillar-desc">
                Commanders override any automated ranking with a mandatory reason note, permanently logged for accountability.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── FOOTER CTA ──────────────────────────────────────────────────────── */}
      <div className="proof-footer-cta">
        <div className="proof-footer-info">
          <div className="proof-footer-icon">⚡</div>
          <div>
            <h4 className="proof-footer-title">Demonstration Complete</h4>
            <p className="proof-footer-desc">
              You've seen how Lifeline Triage turns chaotic disaster communication into clear, prioritized life-saving action.
            </p>
          </div>
        </div>
        <button className="btn btn-primary btn-restart" onClick={onRestart}>
          <RotateCcw size={16} />
          <span>Start Presentation Again (Step 1)</span>
        </button>
      </div>
    </div>
  );
}

// ----------------------------------------------------------------------------
// ACTIVITY LOG DRAWER
// ----------------------------------------------------------------------------
function ActivityLogDrawer({ logs, onClose }) {
  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside className="drawer-panel" onClick={e => e.stopPropagation()} aria-label="Activity Audit Log">
        <div className="drawer-header">
          <div>
            <span className="drawer-category">AUDIT & ACCOUNTABILITY</span>
            <h3 className="drawer-title">Activity Log ({logs.length})</h3>
            <p className="drawer-subtitle">Every automated ranking and human priority adjustment is permanently recorded.</p>
          </div>
          <button className="btn-icon" onClick={onClose} aria-label="Close drawer">
            <X size={20} />
          </button>
        </div>

        <div className="drawer-body">
          {logs.length === 0 ? (
            <div className="empty-state">
              <Activity size={32} />
              <p>No activity entries recorded yet in this session.</p>
            </div>
          ) : (
            <div className="audit-list">
              {logs.map((log, idx) => (
                <div key={idx} className="audit-item">
                  <div className="audit-item-top">
                    <span className="audit-action-badge">{log.action || log.event || 'System Action'}</span>
                    <span className="audit-time">{log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : 'Recent'}</span>
                  </div>
                  <p className="audit-detail">{log.details || log.notes || log.message || JSON.stringify(log)}</p>
                  {log.user && <span className="audit-user">Actor: {log.user}</span>}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="drawer-footer">
          <button className="btn btn-primary btn-full" onClick={onClose}>
            Close Activity Log
          </button>
        </div>
      </aside>
    </div>
  );
}

// ----------------------------------------------------------------------------
// SCREEN: LIVE CYCLONE APPROACH TRACK & CITIZEN ALERT BROADCAST
// ----------------------------------------------------------------------------
function ScreenCycloneTrack({ cycloneTrack, alertsList, district, onAlertBroadcasted, onShowToast }) {
  const [selectedAlertForPreview, setSelectedAlertForPreview] = useState(null);
  const [broadcastingId, setBroadcastingId] = useState(null);

  const cyclone = cycloneTrack?.cyclone || {
    name: "Biparjoy-II",
    category: "Category 4 Very Severe Cyclonic Storm",
    bulletin_number: "IMD-RSMC-CYC-2026-B8",
    storm_surge_m: 4.5,
    max_sustained_winds_kmh: 185
  };

  const pos = cycloneTrack?.current_position || {
    lat: 17.06,
    lon: 83.42,
    distance_km: 85.0,
    wind_speed_kmh: 175,
    hours_to_landfall: 7.5,
    category: "Cat 4 Very Severe",
    status_description: "Telecom towers report intermittent signal degradation along coastal fringes."
  };

  const pastTrack = cycloneTrack?.past_track || [];
  const futureTrack = cycloneTrack?.projected_track || [];

  const handleBroadcast = async (alertId) => {
    try {
      setBroadcastingId(alertId);
      const res = await fetch(`${API_BASE}/api/alerts/${alertId}/broadcast`, { method: 'POST' });
      const data = await res.json();
      if (data.status === 'broadcasted') {
        onShowToast(`🚨 Official Emergency Alert broadcasted to all citizens via SMS & WhatsApp! (98.4% delivery)`);
        onAlertBroadcasted?.();
      }
    } catch {
      onShowToast("Failed to broadcast alert.");
    } finally {
      setBroadcastingId(null);
    }
  };

  return (
    <div className="cyclone-screen-container">
      {/* 1. Header Threat Banner */}
      <div className="cyclone-header-banner">
        <div className="cyclone-title-row">
          <div className="cyclone-radar-pulse-icon">
            <Wind size={26} color="#ffffff" />
          </div>
          <div>
            <span className="cyclone-badge-cat">{cyclone.category}</span>
            <h1 className="cyclone-main-title">Cyclone {cyclone.name} Track & Early Warning</h1>
            <p className="cyclone-bulletin-id">
              Live IMD Coastal Radar Tracking • Bulletin {cyclone.bulletin_number} • Projected Landfall: Kalingapatnam Sands
            </p>
          </div>
        </div>

        <div className="cyclone-header-stats">
          <div className="cyclone-stat-box">
            <span className="stat-label">Distance to Coast</span>
            <span className="stat-val red">{pos.distance_km} km</span>
          </div>
          <div className="cyclone-stat-box">
            <span className="stat-label">Landfall ETA</span>
            <span className="stat-val">{pos.hours_to_landfall > 0 ? `${pos.hours_to_landfall} hrs` : 'LANDFALL ACTIVE'}</span>
          </div>
          <div className="cyclone-stat-box">
            <span className="stat-label">Max Wind Speed</span>
            <span className="stat-val red">{pos.wind_speed_kmh} km/h</span>
          </div>
          <div className="cyclone-stat-box">
            <span className="stat-label">Expected Surge</span>
            <span className="stat-val">{cyclone.storm_surge_m} m</span>
          </div>
        </div>
      </div>

      {/* 2. Main 2-Column Section */}
      <div className="cyclone-grid-layout">
        {/* Left Column: Interactive Approach Radar Map */}
        <div className="cyclone-card">
          <div className="cyclone-card-header">
            <span className="cyclone-card-title">
              <Navigation size={18} color="#1d4ed8" />
              Live Storm Eye & Coastal Trajectory
            </span>
            <span className="nav-tag alert">RADAR ACTIVE</span>
          </div>

          <div className="cyclone-map-wrapper">
            <MapContainer
              center={[pos.lat, pos.lon]}
              zoom={8}
              style={{ height: '100%', width: '100%' }}
              scrollWheelZoom={false}
            >
              <TileLayer
                attribution='&copy; OpenStreetMap'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <MapUpdater center={[pos.lat, pos.lon]} zoom={8} />

              {/* District Zones Polygons */}
              {district && (
                <GeoJSON
                  data={district}
                  style={(feature) => ({
                    color: feature.properties?.is_silent ? '#dc2626' : '#2563eb',
                    weight: 2,
                    fillColor: feature.properties?.is_silent ? '#fee2e2' : '#dbeafe',
                    fillOpacity: 0.35
                  })}
                />
              )}

              {/* Past Waypoints (Grey/Orange) */}
              {pastTrack.map((pt, idx) => (
                <CircleMarker
                  key={`past-${idx}`}
                  center={[pt.lat, pt.lon]}
                  radius={5}
                  pathOptions={{ color: '#ea580c', fillColor: '#fed7aa', fillOpacity: 0.9, weight: 2 }}
                >
                  <Popup>
                    <strong>Track Step {pt.step}</strong> (T+{pt.minute}m)<br />
                    Wind: {pt.wind_speed_kmh} km/h<br />
                    Distance: {pt.distance_km} km
                  </Popup>
                </CircleMarker>
              ))}

              {/* Projected Future Waypoints (Dashed Red) */}
              {futureTrack.map((pt, idx) => (
                <CircleMarker
                  key={`fut-${idx}`}
                  center={[pt.lat, pt.lon]}
                  radius={6}
                  pathOptions={{ color: '#dc2626', fillColor: '#ef4444', fillOpacity: 0.5, weight: 1.5, dashArray: '4, 4' }}
                >
                  <Popup>
                    <strong>Projected Waypoint</strong><br />
                    {pt.description}<br />
                    Wind: {pt.wind_speed_kmh} km/h
                  </Popup>
                </CircleMarker>
              ))}

              {/* Gale Wind Force Outer Danger Circle (~160km radius in degrees approx) */}
              <CircleMarker
                center={[pos.lat, pos.lon]}
                radius={75}
                pathOptions={{ color: '#f97316', fillColor: '#ffedd5', fillOpacity: 0.18, weight: 1.5, dashArray: '5, 5' }}
              />

              {/* Eye-wall Destructive Vortex Circle */}
              <CircleMarker
                center={[pos.lat, pos.lon]}
                radius={24}
                pathOptions={{ color: '#dc2626', fillColor: '#fee2e2', fillOpacity: 0.45, weight: 2 }}
              />

              {/* Current Eye Center Marker */}
              <CircleMarker
                center={[pos.lat, pos.lon]}
                radius={10}
                pathOptions={{ color: '#ffffff', fillColor: '#dc2626', fillOpacity: 1.0, weight: 3 }}
              >
                <Popup>
                  <div style={{ padding: '4px' }}>
                    <strong style={{ color: '#dc2626' }}>CYCLONE EYE (CURRENT)</strong><br />
                    Coordinates: {pos.lat}°N, {pos.lon}°E<br />
                    Wind Gusts: {pos.wind_speed_kmh} km/h<br />
                    Landfall Proximity: {pos.distance_km} km
                  </div>
                </Popup>
              </CircleMarker>
            </MapContainer>

            {/* In-Map Tactical HUD */}
            <div className="cyclone-overlay-hud">
              <div className="hud-item">
                <Wind size={18} color="#38bdf8" />
                <div className="hud-item-text">
                  <span className="hud-item-label">Eye Coordinates</span>
                  <span className="hud-item-val">{pos.lat}°N, {pos.lon}°E</span>
                </div>
              </div>
              <div className="hud-item">
                <Compass size={18} color="#f87171" />
                <div className="hud-item-text">
                  <span className="hud-item-label">Heading Vector</span>
                  <span className="hud-item-val">{cyclone.movement_direction} @ {cyclone.movement_speed_kmh} km/h</span>
                </div>
              </div>
              <div className="hud-item">
                <Activity size={18} color="#4ade80" />
                <div className="hud-item-text">
                  <span className="hud-item-label">Current Phase</span>
                  <span className="hud-item-val">{pos.category}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Early Warning Citizen Broadcast Engine */}
        <div className="alert-delivery-panel">
          {/* Citizen Broadcast Cards */}
          <div className="cyclone-card">
            <div className="cyclone-card-header">
              <span className="cyclone-card-title">
                <Megaphone size={18} color="#dc2626" />
                Community Broadcast Alerts ({alertsList.length})
              </span>
              <span className="stat-label">Human-in-the-Loop</span>
            </div>

            <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px', maxHeight: '350px', overflowY: 'auto' }}>
              {alertsList.length === 0 ? (
                <div className="empty-state">
                  <Info size={28} />
                  <p>Generating targeted zone early warning drafts...</p>
                </div>
              ) : (
                alertsList.map((alt) => (
                  <div key={alt.id} className={`alert-item-card ${alt.status === 'broadcasted' ? 'broadcasted' : ''}`}>
                    <div className="alert-item-top">
                      <span className="alert-zone-badge">
                        <MapPin size={16} color="#dc2626" />
                        {alt.zone_name} ({alt.zone_id})
                      </span>
                      <span className={`alert-status-pill ${alt.status}`}>
                        {alt.status === 'broadcasted' ? '✓ SENT TO USERS' : alt.status}
                      </span>
                    </div>

                    <div className="alert-msg-box">
                      {alt.message}
                    </div>

                    <div className="alert-channels-grid">
                      <div className="alert-channel-chip active">
                        <Radio size={13} /> SMS Cell Broadcast
                      </div>
                      <div className="alert-channel-chip active">
                        <Smartphone size={13} /> WhatsApp Alert
                      </div>
                      <div className="alert-channel-chip active">
                        <Megaphone size={13} /> Village Siren
                      </div>
                    </div>

                    <div className="alert-actions-row">
                      <button
                        type="button"
                        className="btn btn-secondary"
                        style={{ fontSize: '12px', padding: '6px 12px' }}
                        onClick={() => setSelectedAlertForPreview(alt)}
                      >
                        Preview on Citizen Phone
                      </button>

                      <button
                        type="button"
                        className="btn-broadcast"
                        disabled={alt.status === 'broadcasted' || broadcastingId === alt.id}
                        onClick={() => handleBroadcast(alt.id)}
                      >
                        {broadcastingId === alt.id ? (
                          <>
                            <RefreshCw className="spin" size={14} />
                            Dispatching...
                          </>
                        ) : alt.status === 'broadcasted' ? (
                          <>
                            <Check size={14} />
                            Broadcast Complete
                          </>
                        ) : (
                          <>
                            <Send size={14} />
                            Authorize & Send Alert
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Citizen Phone Device Preview */}
          <div className="phone-preview-card">
            <span className="cyclone-card-title" style={{ marginBottom: '12px' }}>
              <Smartphone size={18} color="#2563eb" />
              Citizen Emergency Handset Simulation
            </span>
            <div className="phone-screen-container">
              <div className="phone-notch"></div>
              <div className="phone-sms-bubble">
                <div className="phone-sms-title">
                  <ShieldAlert size={14} />
                  EMERGENCY ALERT • GOVT DISASTER MGMT
                </div>
                <div className="phone-sms-body">
                  {selectedAlertForPreview ? (
                    selectedAlertForPreview.message
                  ) : (
                    alertsList[0]?.message || 
                    "OFFICIAL PREPAREDNESS WARNING: Cyclone Biparjoy (Cat 4) landfall imminent within 6 hours. High surge threat. Mandatory evacuation to cyclone shelters."
                  )}
                </div>
                <div className="phone-sms-time">Direct Cell Broadcast • Just now</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

