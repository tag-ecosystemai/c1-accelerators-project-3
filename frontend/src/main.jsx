import Landing from './Landing.jsx';
import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Activity,
  AlertTriangle,
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  Bell,
  Box,
  Check,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  CircleHelp,
  Clock3,
  CloudSun,
  Download,
  ExternalLink,
  FileText,
  Filter,
  Globe2,
  Home,
  LayoutDashboard,
  LifeBuoy,
  MapPin,
  Menu,
  MoreHorizontal,
  PackageCheck,
  Search,
  Settings2,
  ShieldCheck,
  Sparkles,
  Truck,
  Upload,
  X,
  Zap,
} from 'lucide-react';
import './styles.css';

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL !== undefined
    ? import.meta.env.VITE_API_BASE_URL.replace(/\/$/, '')
    : '';

const nav = [
  ['landing', 'Home', Home],
  ['overview', 'Overview', LayoutDashboard],
  ['shipments', 'Shipments', Truck],
  ['knowledge', 'Knowledge Base', FileText],
  ['alerts', 'Alerts', Bell],
  ['suppliers', 'Suppliers', Box],
];

const RISK_STATE_LABELS = {
  at_risk: 'At risk',
  monitoring: 'Monitoring',
  on_track: 'On track',
};

function formatRiskState(state) {
  return RISK_STATE_LABELS[state] || 'Monitoring';
}

function riskTone(state) {
  if (state === 'at_risk') {
    return 'high';
  }

  if (state === 'monitoring') {
    return 'medium';
  }

  return 'low';
}

function riskWidth(state) {
  if (state === 'at_risk') {
    return 90;
  }

  if (state === 'monitoring') {
    return 55;
  }

  return 20;
}

function getDestination(shipment) {
  if (!shipment) {
    return 'Unknown destination';
  }

  return shipment.destination || 'Unknown destination';
}

function getRouteLabel(shipment) {
  if (!shipment) {
    return 'Route unavailable';
  }

  const origin = shipment.origin || 'Origin unavailable';
  const destination = getDestination(shipment);

  return `${origin} → ${destination}`;
}

function getRiskEvidence(data) {
  const evidence = Array.isArray(data?.evidence)
    ? data.evidence
    : [];

  const usefulEvidence = evidence.find(
    (item) =>
      item?.value !== null &&
      item?.value !== undefined &&
      String(item.value).trim() !== '',
  );

  if (usefulEvidence) {
    return String(usefulEvidence.value);
  }

  if (data?.weather) {
    const weather = data.weather;
    const parts = [];

    if (typeof weather.temperature_c === 'number') {
      parts.push(`${weather.temperature_c.toFixed(1)}°C`);
    }

    if (typeof weather.precipitation_mm === 'number') {
      parts.push(
        `${weather.precipitation_mm.toFixed(1)} mm precipitation`,
      );
    }

    if (typeof weather.wind_speed_kmh === 'number') {
      parts.push(
        `${weather.wind_speed_kmh.toFixed(0)} km/h wind`,
      );
    }

    if (parts.length > 0) {
      return parts.join(' · ');
    }
  }

  return 'No additional investigation evidence was returned.';
}

function getSignalStatus(data) {
  return {
    weather: Boolean(data?.weather),
    knowledge:
      Array.isArray(data?.knowledge_results) &&
      data.knowledge_results.length > 0,
    route:
      Array.isArray(data?.route_options) &&
      data.route_options.length > 0,
    suppliers:
      Array.isArray(data?.supplier_options) &&
      data.supplier_options.length > 0,
  };
}

function normalizeShipment(shipment) {
  const riskState = shipment?.risk_state || 'monitoring';

  return {
    id: shipment?.shipment_id || 'Unknown',
    trackingNumber: shipment?.tracking_number || '—',
    carrier: shipment?.carrier || 'Unknown carrier',
    origin: shipment?.origin || 'Unknown origin',
    destination: shipment?.destination || 'Unknown destination',
    route: getRouteLabel(shipment),
    estimatedArrival: shipment?.estimated_arrival || null,
    status: shipment?.current_status || 'Unknown',
    shippingMode: shipment?.shipping_mode || 'Unknown',

    riskState,
    riskStatus: formatRiskState(riskState),
    riskTone: riskTone(riskState),
    riskWidth: riskWidth(riskState),

    signals: {
      weather: false,
      knowledge: false,
      route: false,
      suppliers: false,
    },

    routeOptions: [],
    supplierOptions: [],
    knowledgeResults: [],
    evidence: [],

    briefing: '',
    reportId: null,

    raw: shipment,
  };
}

function normalizeAnalysis(data) {
  const shipment = data?.shipment || {};
  const risk = data?.risk || {};

  const riskState = risk?.state || 'monitoring';

  const routeOptions = Array.isArray(data?.route_options)
    ? data.route_options
    : [];

  const supplierOptions = Array.isArray(data?.supplier_options)
    ? data.supplier_options
    : [];

  const knowledgeResults = Array.isArray(data?.knowledge_results)
    ? data.knowledge_results
    : [];

  const evidence = Array.isArray(data?.evidence)
    ? data.evidence
    : [];

  const signals = getSignalStatus(data);

  return {
    id: shipment?.shipment_id || 'Unknown',
    trackingNumber: shipment?.tracking_number || '—',
    carrier: shipment?.carrier || 'Unknown carrier',
    origin: shipment?.origin || 'Unknown origin',
    destination:
      shipment?.destination || 'Unknown destination',
    route: getRouteLabel(shipment),
    estimatedArrival: shipment?.estimated_arrival || null,
    status: shipment?.current_status || 'Unknown',
    shippingMode: shipment?.shipping_mode || 'Unknown',
    riskState,
    riskStatus: formatRiskState(riskState),
    riskTone: riskTone(riskState),
    riskWidth: riskWidth(riskState),
    reason: getRiskEvidence(data),
    evidenceSource:
      signals.knowledge
        ? 'Company knowledge base'
        : signals.weather
          ? 'Open-Meteo weather signal'
          : 'Shipment data',
    recommendation:
      riskState === 'at_risk'
        ? 'Human review is recommended before operational action.'
        : riskState === 'monitoring'
          ? 'Continue monitoring this shipment and review available operational evidence.'
          : 'Shipment is currently on track. Continue normal monitoring.',
    alternative:
      routeOptions.length > 0
        ? routeOptions[0]
        : supplierOptions.length > 0
          ? supplierOptions[0]
          : null,
    routeOptions,
    supplierOptions,
    knowledgeResults,
    evidence,
    briefing:
      typeof data?.briefing === 'string'
        ? data.briefing
        : 'No briefing was generated.',
    signals,
    reportId: data?.report_id || null,
    raw: data,
  };
}

function buildAlternativeText(shipment) {
  if (!shipment?.alternative) {
    return '';
  }

  const alternative = shipment.alternative;

  if (alternative.route_name) {
    return alternative.route_name;
  }

  if (alternative.supplier_name) {
    return alternative.supplier_name;
  }

  return 'Alternative operational option identified';
}

function formatDate(value) {
  if (!value) {
    return '—';
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function App() {
  const [active, setActive] = useState('landing');
  const [selected, setSelected] = useState(null);
  const [shipments, setShipments] = useState([]);
  const [shipmentId, setShipmentId] = useState('');
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('All');
  const [toast, setToast] = useState('');
  const [mobile, setMobile] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingShipments, setLoadingShipments] = useState(false);
  const [error, setError] = useState('');

  const [shipmentFile, setShipmentFile] = useState(null);
  const [knowledgeFile, setKnowledgeFile] = useState(null);
  const [uploadingShipment, setUploadingShipment] = useState(false);
  const [uploadingKnowledge, setUploadingKnowledge] = useState(false);

  const notify = (message) => {
    setToast(message);
    setTimeout(() => setToast(''), 2600);
  };

  const loadShipments = async () => {
    setLoadingShipments(true);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/shipments`,
      );

      let payload;

      try {
        payload = await response.json();
      } catch {
        payload = null;
      }

      if (!response.ok) {
        throw new Error(
          payload?.detail ||
            `Unable to load shipments. HTTP ${response.status}.`,
        );
      }

      const normalized = Array.isArray(payload)
        ? payload.map(normalizeShipment)
        : [];

      setShipments(normalized);

      if (normalized.length === 0) {
        setSelected(null);
        setShipmentId('');
        return;
      }

      if (!selected) {
        setSelected(normalized[0]);
        setShipmentId(normalized[0].id);
      }
    } catch (requestError) {
      const message =
        requestError instanceof Error
          ? requestError.message
          : 'Unable to load shipments.';

      setError(message);
    } finally {
      setLoadingShipments(false);
    }
  };

  useEffect(() => {
    loadShipments();
  }, []);

  const analyzeShipment = async (id = shipmentId) => {
    const normalizedId = String(id || '')
      .trim()
      .replace(/,+$/, '');

    if (!normalizedId) {
      setError(
        'Upload shipment data or select a shipment before running an analysis.',
      );
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/shipments/${encodeURIComponent(
          normalizedId,
        )}/analyze`,
      );

      let payload;

      try {
        payload = await response.json();
      } catch {
        payload = null;
      }

      if (!response.ok) {
        const detail =
          payload?.detail ||
          `SentinelAI API returned HTTP ${response.status}.`;

        throw new Error(detail);
      }

      const normalized = normalizeAnalysis(payload);

      setSelected(normalized);
      setShipmentId(normalized.id);
      setActive('overview');

      await loadShipments();

      notify(`Analysis completed for shipment ${normalized.id}.`);
    } catch (requestError) {
      const message =
        requestError instanceof Error
          ? requestError.message
          : 'Unable to connect to SentinelAI.';

      setError(message);
      notify('Shipment analysis failed.');
    } finally {
      setLoading(false);
    }
  };

  const uploadShipmentData = async () => {
    if (!shipmentFile) {
      notify('Choose a CSV or XLSX shipment file first.');
      return;
    }

    setUploadingShipment(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', shipmentFile);

      const response = await fetch(
        `${API_BASE_URL}/api/shipments/import`,
        {
          method: 'POST',
          body: formData,
        },
      );

      let payload;

      try {
        payload = await response.json();
      } catch {
        payload = null;
      }

      if (!response.ok) {
        throw new Error(
          payload?.detail ||
            `Shipment import failed. HTTP ${response.status}.`,
        );
      }

      setShipmentFile(null);

      await loadShipments();

      const imported =
        payload?.imported ??
        payload?.created ??
        payload?.imported_count ??
        null;

      notify(
        imported !== null
          ? `${imported} shipment${imported === 1 ? '' : 's'} imported successfully.`
          : 'Shipment data imported successfully.',
      );
    } catch (requestError) {
      const message =
        requestError instanceof Error
          ? requestError.message
          : 'Shipment import failed.';

      setError(message);
      notify('Shipment upload failed.');
    } finally {
      setUploadingShipment(false);
    }
  };

  const uploadKnowledge = async () => {
    if (!knowledgeFile) {
      notify('Choose a Markdown or TXT knowledge document first.');
      return;
    }

    setUploadingKnowledge(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', knowledgeFile);

      const response = await fetch(
        `${API_BASE_URL}/api/knowledge/upload`,
        {
          method: 'POST',
          body: formData,
        },
      );

      let payload;

      try {
        payload = await response.json();
      } catch {
        payload = null;
      }

      if (!response.ok) {
        throw new Error(
          payload?.detail ||
            `Knowledge upload failed. HTTP ${response.status}.`,
        );
      }

      setKnowledgeFile(null);

      notify(
        `${payload?.chunks_ingested || 0} knowledge chunks added to the knowledge base.`,
      );
    } catch (requestError) {
      const message =
        requestError instanceof Error
          ? requestError.message
          : 'Knowledge upload failed.';

      setError(message);
      notify('Knowledge upload failed.');
    } finally {
      setUploadingKnowledge(false);
    }
  };

  const filtered = useMemo(() => {
    const normalizedQuery = query.toLowerCase().trim();

    return shipments.filter((shipment) => {
      const matchesQuery =
        !normalizedQuery ||
        `${shipment.id} ${shipment.trackingNumber} ${shipment.carrier} ${shipment.origin} ${shipment.destination}`
          .toLowerCase()
          .includes(normalizedQuery);

      const matchesFilter =
        filter === 'All' ||
        (filter === 'At risk' &&
          shipment.riskState === 'at_risk') ||
        (filter === 'Monitoring' &&
          shipment.riskState === 'monitoring') ||
        (filter === 'On track' &&
          shipment.riskState === 'on_track');

      return matchesQuery && matchesFilter;
    });
  }, [shipments, query, filter]);

  const riskCounts = useMemo(
    () => ({
      atRisk: shipments.filter(
        (shipment) => shipment.riskState === 'at_risk',
      ).length,
      monitoring: shipments.filter(
        (shipment) => shipment.riskState === 'monitoring',
      ).length,
      onTrack: shipments.filter(
        (shipment) => shipment.riskState === 'on_track',
      ).length,
    }),
    [shipments],
  );

  const handleNav = (key) => {
    if (key === 'landing') {
      setActive('landing');
      setMobile(false);
      return;
    }

    if (key === 'alerts') {
      setActive('alerts');
      setMobile(false);

      if (riskCounts.atRisk > 0) {
        notify(
          `${riskCounts.atRisk} shipment${
            riskCounts.atRisk === 1 ? '' : 's'
          } require${riskCounts.atRisk === 1 ? 's' : ''} human review.`,
        );
      } else {
        notify('No active risk alerts.');
      }

      return;
    }

    setActive(key);
    setMobile(false);
  };

  const selectShipment = (shipment) => {
    setSelected(shipment);
    setShipmentId(shipment.id);
  };

  if (active === 'landing') {
    return (
      <Landing
        openDashboard={() => {
          setActive('overview');

          if (!selected && shipments.length > 0) {
            selectShipment(shipments[0]);
          }
        }}
      />
    );
  }

  const selectedRiskState = selected?.riskState || 'monitoring';
  const currentStatus =
    selected?.riskStatus || 'Not analyzed';

  const signalCount = selected
    ? [
        selected.signals.weather,
        selected.signals.knowledge,
        selected.signals.route,
        selected.signals.suppliers,
      ].filter(Boolean).length
    : 0;

  const alternativeText = buildAlternativeText(selected);

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobile ? 'mobile-open' : ''}`}>
        <div className="brand">
          <div className="brand-mark">
            <Activity size={20} />
          </div>

          <div>
            <strong>
              sentinel<span>ai</span>
            </strong>
            <small>SUPPLY CHAIN INTELLIGENCE</small>
          </div>

          <button
            className="icon-btn mobile-close"
            onClick={() => setMobile(false)}
          >
            <X size={18} />
          </button>
        </div>

        <div className="workspace">
          <div className="workspace-avatar">TA</div>

          <div className="workspace-copy">
            <b>TAG Accelerators</b>
            <small>Team workspace</small>
          </div>

          <ChevronDown size={15} className="muted" />
        </div>

        <div className="nav-label">WORKSPACE</div>

        <nav>
          {nav.map(([key, label, Icon]) => (
            <button
              key={key}
              onClick={() => handleNav(key)}
              className={`nav-link ${
                active === key ? 'selected' : ''
              }`}
            >
              <Icon size={18} />

              <span>{label}</span>

              {key === 'alerts' && riskCounts.atRisk > 0 && (
                <em className="nav-count">
                  {riskCounts.atRisk}
                </em>
              )}
            </button>
          ))}
        </nav>

        <div className="nav-label source-label">
          DATA INTELLIGENCE SOURCES
        </div>

        <div className="source-list">
          <div>
            <span className="live-dot" /> Shipment data
            <span className="source-live">
              {shipments.length > 0 ? 'Connected' : 'Awaiting'}
            </span>
          </div>

          <div>
            <span className="live-dot weather-dot" /> Weather
            <span className="source-live">
              {selected?.signals.weather
                ? 'Live'
                : 'Available'}
            </span>
          </div>

          <div>
            <span className="source-dot" /> Knowledge base
            <span className="source-live">
              {selected?.signals.knowledge
                ? 'Active'
                : 'Ready'}
            </span>
          </div>
        </div>

        <div className="sidebar-bottom">
          <div className="plan-card">
            <div className="plan-icon">
              <Zap size={15} />
            </div>

            <b>SentinelAI decision support</b>

            <p>
              Predictions and evidence are presented for human review.
              No automatic rerouting or supplier substitution.
            </p>

            <button
              onClick={() =>
                notify(
                  'SentinelAI provides decision support; operational actions remain human-controlled.',
                )
              }
            >
              Learn more <ArrowRight size={13} />
            </button>
          </div>

          <button
            className="nav-link"
            onClick={() =>
              notify(
                'Settings will be available in a later release.',
              )
            }
          >
            <Settings2 size={17} />
            Settings
          </button>

          <button
            className="nav-link"
            onClick={() =>
              notify(
                'Help center will be available in a later release.',
              )
            }
          >
            <LifeBuoy size={17} />
            Help center
          </button>

          <div className="profile">
            <div className="profile-avatar">TA</div>

            <div>
              <b>TAG Accelerators</b>
              <small>Operations workspace</small>
            </div>

            <MoreHorizontal
              size={17}
              className="muted"
            />
          </div>
        </div>
      </aside>

      {mobile && (
        <button
          className="scrim"
          onClick={() => setMobile(false)}
          aria-label="Close menu"
        />
      )}

      <main className="main-area">
        <header className="topbar">
          <button
            className="icon-btn menu-toggle"
            onClick={() => setMobile(true)}
          >
            <Menu size={19} />
          </button>

          <div className="breadcrumb">
            Operations
            <ChevronRight size={14} />
            <strong>
              {nav.find((n) => n[0] === active)?.[1] ||
                'Overview'}
            </strong>
          </div>

          <div className="top-actions">
            <div className="system-status">
              <span className="live-dot" />
              SentinelAI · API connected
            </div>

            <button
              className="icon-btn help-btn"
              onClick={() =>
                notify(
                  'Upload shipment data, add knowledge, then select a shipment to investigate.',
                )
              }
            >
              <CircleHelp size={18} />
            </button>

            <button
              className="icon-btn notification-btn"
              onClick={() => handleNav('alerts')}
            >
              <Bell size={18} />
              {riskCounts.atRisk > 0 && <i />}
            </button>

            <div className="top-avatar">TA</div>
          </div>
        </header>

        <div className="content">
          <section className="welcome-row">
            <div>
              <div className="eyebrow">
                <span className="eyebrow-line" />
                SENTINELAI · OPERATIONAL INTELLIGENCE

                {riskCounts.atRisk > 0 && (
                  <span className="eyebrow-live">
                    <span className="live-dot" />
                    REVIEW REQUIRED
                  </span>
                )}
              </div>

              <h1>
                Supply chain intelligence{' '}
                <span className="wave">✳</span>
              </h1>

              <p className="subtitle">
                Predict disruption risk, investigate evidence,
                and support human operational decisions.
              </p>
            </div>

            <div className="header-actions">
              <div className="shipment-input">
                <Search size={15} />

                <input
                  value={shipmentId}
                  onChange={(event) =>
                    setShipmentId(event.target.value)
                  }
                  onKeyDown={(event) => {
                    if (event.key === 'Enter') {
                      analyzeShipment();
                    }
                  }}
                  placeholder="Shipment ID"
                  aria-label="Shipment ID"
                />
              </div>

              <button
                className="btn btn-secondary"
                onClick={() => {
                  if (!selected) {
                    notify(
                      'Run an analysis before exporting a report.',
                    );
                    return;
                  }

                  notify(
                    'Report export will be connected to the briefing pipeline.',
                  );
                }}
              >
                <Download size={15} />
                Export report
              </button>

              <button
                className="btn btn-primary"
                onClick={() => analyzeShipment()}
                disabled={loading}
              >
                <Sparkles size={15} />
                {loading ? 'Analyzing…' : 'Run analysis'}
              </button>
            </div>
          </section>

          {error && (
            <div className="error-banner">
              <AlertTriangle size={17} />

              <div>
                <b>Operation unavailable</b>
                <p>{error}</p>
              </div>

              <button
                className="icon-btn"
                onClick={() => setError('')}
                aria-label="Dismiss error"
              >
                <X size={16} />
              </button>
            </div>
          )}

          <section className="upload-grid">
            <div className="panel upload-panel">
              <div className="upload-panel-icon shipment-upload">
                <Truck size={18} />
              </div>

              <div className="upload-panel-content">
                <div className="section-tag">
                  <span />
                  SHIPMENT DATA
                </div>

                <h2>Import shipments</h2>

                <p>
                  Upload your company's CSV or Excel shipment
                  data to populate the operational workspace.
                </p>

                <div className="upload-controls">
                  <label className="file-picker">
                    <Upload size={15} />

                    <span>
                      {shipmentFile
                        ? shipmentFile.name
                        : 'Choose CSV or XLSX'}
                    </span>

                    <input
                      type="file"
                      accept=".csv,.xlsx"
                      onChange={(event) =>
                        setShipmentFile(
                          event.target.files?.[0] || null,
                        )
                      }
                    />
                  </label>

                  <button
                    className="btn btn-primary"
                    onClick={uploadShipmentData}
                    disabled={
                      uploadingShipment || !shipmentFile
                    }
                  >
                    <Upload size={15} />
                    {uploadingShipment
                      ? 'Importing…'
                      : 'Import data'}
                  </button>
                </div>

                <small className="upload-note">
                  CSV and XLSX files supported
                </small>
              </div>
            </div>

            <div className="panel upload-panel">
              <div className="upload-panel-icon knowledge-upload">
                <FileText size={18} />
              </div>

              <div className="upload-panel-content">
                <div className="section-tag">
                  <span />
                  KNOWLEDGE BASE
                </div>

                <h2>Add operational knowledge</h2>

                <p>
                  Upload company procedures and SOPs so SentinelAI
                  can ground investigations in your own guidance.
                </p>

                <div className="upload-controls">
                  <label className="file-picker">
                    <FileText size={15} />

                    <span>
                      {knowledgeFile
                        ? knowledgeFile.name
                        : 'Choose MD or TXT'}
                    </span>

                    <input
                      type="file"
                      accept=".md,.txt"
                      onChange={(event) =>
                        setKnowledgeFile(
                          event.target.files?.[0] || null,
                        )
                      }
                    />
                  </label>

                  <button
                    className="btn btn-primary"
                    onClick={uploadKnowledge}
                    disabled={
                      uploadingKnowledge || !knowledgeFile
                    }
                  >
                    <Upload size={15} />
                    {uploadingKnowledge
                      ? 'Adding…'
                      : 'Add knowledge'}
                  </button>
                </div>

                <small className="upload-note">
                  Markdown and TXT files supported
                </small>
              </div>
            </div>
          </section>

          <section className="metrics-grid">
            <Metric
              label="Total shipments"
              value={shipments.length || '—'}
              delta={
                shipments.length
                  ? 'Workspace data'
                  : 'Awaiting upload'
              }
              up={shipments.length > 0}
              note="Company shipment records"
              icon={Truck}
              tone="lavender"
            />

            <Metric
              label="At risk"
              value={riskCounts.atRisk || '—'}
              delta={
                riskCounts.atRisk
                  ? 'Review required'
                  : 'No active alerts'
              }
              up={riskCounts.atRisk > 0}
              note="Deterministic operational risk state"
              icon={AlertTriangle}
              tone="peach"
              alert={riskCounts.atRisk > 0}
            />

            <Metric
              label="Monitoring"
              value={riskCounts.monitoring || '—'}
              delta="Needs observation"
              up={riskCounts.monitoring > 0}
              note="Shipment state requires monitoring"
              icon={Clock3}
              tone="mint"
            />

            <Metric
              label="On track"
              value={riskCounts.onTrack || '—'}
              delta="Normal status"
              up={riskCounts.onTrack > 0}
              note="No current operational risk flag"
              icon={PackageCheck}
              tone="sky"
            />
          </section>

          {selected ? (
            <section className="insight-banner">
              <div className="insight-icon">
                <Sparkles size={17} />
              </div>

              <div className="insight-copy">
                <div>
                  <span className="insight-kicker">
                    SENTINEL BRIEFING
                  </span>

                  <span className="insight-time">
                    · Shipment {selected.id}
                  </span>
                </div>

                <p>
                  <b>
                    {selected.riskState === 'at_risk'
                      ? 'Human review is recommended.'
                      : selected.riskState === 'monitoring'
                        ? 'Shipment requires continued monitoring.'
                        : 'Shipment is currently on track.'}
                  </b>{' '}
                  Current operational state:{' '}
                  <b>{selected.riskStatus}</b>.{' '}
                  {selected.reason}
                </p>

                <button
                  onClick={() => setActive('overview')}
                >
                  Read briefing <ArrowRight size={14} />
                </button>
              </div>

              <div className="insight-art">
                <div className="orbit orbit-one" />
                <div className="orbit orbit-two" />

                <div className="orbit-core">
                  <Activity size={20} />
                </div>

                <span className="orbit-point point-one" />
                <span className="orbit-point point-two" />
              </div>
            </section>
          ) : (
            <section className="empty-analysis">
              <div className="insight-icon">
                <Sparkles size={17} />
              </div>

              <div>
                <span className="insight-kicker">
                  SENTINEL INTELLIGENCE
                </span>

                <h3>No shipment analysis loaded</h3>

                <p>
                  Upload shipment data, select a shipment, and
                  run SentinelAI to generate an investigation.
                </p>
              </div>

              {shipments.length > 0 && (
                <button
                  className="btn btn-primary"
                  onClick={() =>
                    analyzeShipment(shipments[0].id)
                  }
                  disabled={loading}
                >
                  Analyze first shipment{' '}
                  <ArrowRight size={14} />
                </button>
              )}
            </section>
          )}

          <section className="dashboard-grid">
            <div className="panel shipments-panel">
              <div className="panel-header">
                <div>
                  <h2>My shipments</h2>

                  <p>
                    Company shipment records available for
                    SentinelAI investigation.
                  </p>
                </div>

                <button
                  className="text-button"
                  onClick={loadShipments}
                  disabled={loadingShipments}
                >
                  {loadingShipments
                    ? 'Refreshing…'
                    : 'Refresh shipments'}{' '}
                  <ArrowRight size={14} />
                </button>
              </div>

              <div className="table-tools">
                <div className="search-field">
                  <Search size={15} />

                  <input
                    value={query}
                    onChange={(event) =>
                      setQuery(event.target.value)
                    }
                    placeholder="Search shipments…"
                  />
                </div>

                <button
                  className="filter-btn"
                  onClick={() => {
                    setFilter(
                      filter === 'All'
                        ? 'At risk'
                        : filter === 'At risk'
                          ? 'Monitoring'
                          : filter === 'Monitoring'
                            ? 'On track'
                            : 'All',
                    );
                  }}
                >
                  <Filter size={14} />
                  {filter}
                  <ChevronDown size={13} />
                </button>

                <button
                  className="icon-btn table-settings"
                  onClick={() =>
                    notify(
                      'Shipment fields are sourced from your uploaded company data.',
                    )
                  }
                >
                  <MoreHorizontal size={18} />
                </button>
              </div>

              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>SHIPMENT</th>
                      <th>DESTINATION</th>
                      <th>RISK LEVEL</th>
                      <th>STATUS</th>
                      <th />
                    </tr>
                  </thead>

                  <tbody>
                    {filtered.map((shipment) => (
                      <tr
                        key={shipment.id}
                        onClick={() => selectShipment(shipment)}
                        className={
                          selected?.id === shipment.id
                            ? 'row-selected'
                            : ''
                        }
                      >
                        <td>
                          <div className="shipment-cell">
                            <div
                              className={`supplier-avatar ${
                                shipment.riskTone === 'high'
                                  ? 'violet'
                                  : shipment.riskTone === 'medium'
                                    ? 'amber'
                                    : 'green'
                              }`}
                            >
                              {shipment.id.slice(-2)}
                            </div>

                            <div>
                              <b>{shipment.id}</b>

                              <small>
                                {shipment.trackingNumber}
                                <span> · </span>
                                {shipment.carrier}
                              </small>
                            </div>
                          </div>
                        </td>

                        <td>
                          <b className="eta">
                            {shipment.destination}
                          </b>

                          <small className="eta-time">
                            ETA {formatDate(shipment.estimatedArrival)}
                          </small>
                        </td>

                        <td>
                          <div className="risk-cell">
                            <div className="risk-bar">
                              <i
                                style={{
                                  width: `${shipment.riskWidth}%`,
                                }}
                                className={shipment.riskTone}
                              />
                            </div>

                            <b>{shipment.riskStatus}</b>
                          </div>
                        </td>

                        <td>
                          <span
                            className={`status-pill ${
                              shipment.riskTone === 'high'
                                ? 'status-high'
                                : shipment.riskTone === 'medium'
                                  ? 'status-medium'
                                  : 'status-low'
                            }`}
                          >
                            <i />
                            {shipment.status}
                          </span>
                        </td>

                        <td>
                          <button
                            className="row-open"
                            aria-label="View details"
                            onClick={(event) => {
                              event.stopPropagation();
                              selectShipment(shipment);
                            }}
                          >
                            <ArrowRight size={15} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                {filtered.length === 0 && (
                  <div className="empty-state">
                    {shipments.length === 0
                      ? 'Upload a CSV or XLSX file to add shipments to your workspace.'
                      : 'No shipment matches the current search/filter.'}
                  </div>
                )}
              </div>

              <div className="table-footer">
                <span>
                  Showing <b>{filtered.length}</b> of{' '}
                  <b>{shipments.length}</b> shipments
                </span>

                <div>
                  <button className="page-btn" disabled>
                    <ChevronLeft size={15} />
                  </button>

                  <button className="page-number">1</button>

                  <button
                    className="page-btn"
                    disabled
                  >
                    <ChevronRight size={15} />
                  </button>
                </div>
              </div>
            </div>

            <div className="right-column">
              <div className="panel detail-panel">
                <div className="panel-header detail-heading">
                  <div>
                    <div className="section-tag">
                      <span />
                      {selected?.riskState === 'at_risk'
                        ? 'PRIORITY CASE'
                        : 'SHIPMENT ANALYSIS'}
                    </div>

                    <button
                      className="icon-btn"
                      onClick={() =>
                        notify(
                          'Shipment actions remain human-controlled.',
                        )
                      }
                    >
                      <MoreHorizontal size={18} />
                    </button>
                  </div>
                </div>

                {selected ? (
                  <>
                    <h2>{selected.id}</h2>

                    <p className="detail-id">
                      {selected.trackingNumber}
                      <span> · </span>
                      {selected.carrier}
                    </p>

                    <div className="detail-route">
                      <div className="route-pin">
                        <MapPin size={14} />
                      </div>

                      <span>{selected.route}</span>

                      <button
                        className="icon-btn route-map"
                        onClick={() =>
                          notify(
                            'Map visualization will be connected to route intelligence later.',
                          )
                        }
                      >
                        <ExternalLink size={14} />
                      </button>
                    </div>

                    <div className="detail-stats">
                      <div>
                        <small>ESTIMATED ARRIVAL</small>
                        <b>
                          {formatDate(
                            selected.estimatedArrival,
                          )}
                        </b>
                      </div>

                      <div>
                        <small>SHIPPING MODE</small>
                        <b>{selected.shippingMode}</b>
                      </div>

                      <div>
                        <small>RISK STATE</small>
                        <b
                          className={
                            selected.riskTone === 'high'
                              ? 'text-red'
                              : selected.riskTone === 'medium'
                                ? 'text-amber'
                                : 'text-green'
                          }
                        >
                          {selected.riskStatus}
                          <span className="risk-sub">
                            Operational state
                          </span>
                        </b>
                      </div>
                    </div>

                    <div className="divider" />

                    <div className="cause-title">
                      <div className="cause-icon">
                        <CloudSun size={15} />
                      </div>

                      <div>
                        <b>Investigation evidence</b>
                        <small>{selected.reason}</small>
                      </div>

                      <span className="confidence">
                        {selected.riskState === 'at_risk'
                          ? 'REVIEW'
                          : 'SIGNAL'}
                      </span>
                    </div>

                    <div className="evidence">
                      <div className="evidence-line" />

                      <div>
                        <b>{selected.reason}</b>

                        <small>
                          {selected.evidenceSource}
                        </small>
                      </div>
                    </div>

                    <div className="recommendation">
                      <div className="rec-header">
                        <Sparkles size={14} />
                        HUMAN REVIEW
                      </div>

                      <p>{selected.recommendation}</p>

                      {alternativeText && (
                        <div className="alt-option">
                          <ShieldCheck size={14} />

                          <span>{alternativeText}</span>
                        </div>
                      )}

                      <button
                        className="rec-action"
                        onClick={() =>
                          notify(
                            'This recommendation is for human review only; no action was executed.',
                          )
                        }
                      >
                        Review this action{' '}
                        <ArrowRight size={14} />
                      </button>
                    </div>
                  </>
                ) : (
                  <div className="empty-detail">
                    <Sparkles size={24} />

                    <h3>No analysis yet</h3>

                    <p>
                      Select a shipment and run SentinelAI to
                      inspect its risk, evidence, and operational
                      procedures.
                    </p>
                  </div>
                )}
              </div>

              <div className="panel signal-panel">
                <div className="signal-head">
                  <div>
                    <h3>Signal sources</h3>
                    <p>
                      Data availability for this investigation
                    </p>
                  </div>

                  <button
                    className="icon-btn"
                    onClick={() => analyzeShipment()}
                    disabled={loading || !selected}
                  >
                    <Activity size={16} />
                  </button>
                </div>

                <div className="signal-row">
                  <div className="signal-type">
                    <Truck size={15} />
                  </div>

                  <div>
                    <b>Shipment data</b>

                    <small>
                      {selected
                        ? 'Company shipment loaded'
                        : shipments.length
                          ? `${shipments.length} shipment records`
                          : 'Awaiting upload'}
                    </small>
                  </div>

                  {shipments.length > 0 ? (
                    <span className="signal-ok">
                      <Check size={12} /> Available
                    </span>
                  ) : (
                    <span className="signal-warn">
                      Awaiting
                    </span>
                  )}
                </div>

                <div className="signal-row">
                  <div className="signal-type weather">
                    <CloudSun size={15} />
                  </div>

                  <div>
                    <b>Weather</b>

                    <small>
                      {selected?.signals.weather
                        ? 'Observation available'
                        : 'Available when coordinates are supplied'}
                    </small>
                  </div>

                  {selected?.signals.weather ? (
                    <span className="signal-ok">
                      <Check size={12} /> Available
                    </span>
                  ) : (
                    <span className="signal-warn">
                      Optional
                    </span>
                  )}
                </div>

                <div className="signal-row">
                  <div className="signal-type news">
                    <Globe2 size={15} />
                  </div>

                  <div>
                    <b>Knowledge base</b>

                    <small>
                      {selected?.knowledgeResults?.length
                        ? `${selected.knowledgeResults.length} relevant source${
                            selected.knowledgeResults.length === 1
                              ? ''
                              : 's'
                          }`
                        : 'Company procedures available'}
                    </small>
                  </div>

                  {selected?.signals.knowledge ? (
                    <span className="signal-ok">
                      <Check size={12} /> Active
                    </span>
                  ) : (
                    <span className="signal-warn">
                      Ready
                    </span>
                  )}
                </div>

                <div className="signal-row">
                  <div className="signal-type">
                    <ShieldCheck size={15} />
                  </div>

                  <div>
                    <b>Route intelligence</b>

                    <small>
                      {selected
                        ? `${selected.routeOptions.length} alternative${
                            selected.routeOptions.length === 1
                              ? ''
                              : 's'
                          }`
                        : 'Available for future integration'}
                    </small>
                  </div>

                  {selected?.routeOptions.length > 0 ? (
                    <span className="signal-ok">
                      <Check size={12} /> Available
                    </span>
                  ) : (
                    <span className="signal-warn">
                      Optional
                    </span>
                  )}
                </div>
              </div>
            </div>
          </section>

          {selected?.briefing && (
            <section className="panel briefing-panel">
              <div className="panel-header">
                <div>
                  <h2>Operational briefing</h2>

                  <p>
                    Evidence-grounded decision support generated
                    from the current investigation.
                  </p>
                </div>

                <span className="briefing-badge">
                  <Sparkles size={13} />
                  Human review required
                </span>
              </div>

              <OperationalBriefing shipment={selected} />
            </section>
          )}

          <footer className="footer">
            <span>
              <span className="live-dot" />
              SentinelAI · Company shipment and knowledge data
            </span>

            <span>
              SentinelAI <i /> Human review required before action
            </span>
          </footer>
        </div>
      </main>

      {toast && (
        <div className="toast">
          <Check size={16} />
          {toast}

          <button onClick={() => setToast('')}>
            <X size={14} />
          </button>
        </div>
      )}
    </div>
  );
}

function OperationalBriefing({ shipment }) {
  const risk = shipment?.raw?.risk || {};
  const weather = shipment?.raw?.weather;
  const routes = shipment?.routeOptions || [];
  const suppliers = shipment?.supplierOptions || [];
  const news = shipment?.raw?.news_results || [];
  const knowledge = shipment?.knowledgeResults || [];

  const evidence = shipment?.evidence || [];

  const statusEvidence = evidence.find(
    (item) => item?.type === 'shipment_status',
  );

  const etaEvidence = evidence.find(
    (item) => item?.type === 'estimated_arrival',
  );

  const etaPassed =
    etaEvidence?.value &&
    new Date(etaEvidence.value).getTime() < Date.now();

  return (
    <div className="operational-briefing">
      <div className="briefing-summary">
        <div className="briefing-summary-icon">
          <AlertTriangle size={17} />
        </div>

        <div>
          <span className="briefing-section-label">
            EXECUTIVE SUMMARY
          </span>

          <h3>
            Shipment {shipment.id}{' '}
            {risk.state === 'at_risk'
              ? 'requires human review.'
              : risk.state === 'monitoring'
                ? 'requires continued monitoring.'
                : 'is currently on track.'}
          </h3>

          <p>
            The shipment is currently{' '}
            <strong>
              {statusEvidence?.value || shipment.status}
            </strong>
            {etaPassed
              ? ', and its estimated arrival time has passed.'
              : '.'}{' '}
            SentinelAI combines the operational state with the
            CatBoost prediction and external investigation evidence.
          </p>
        </div>
      </div>

      <div className="briefing-section">
        <div className="briefing-section-heading">
          <span className="briefing-section-label">
            RISK ASSESSMENT
          </span>
        </div>

        <div className="briefing-risk-grid">
          <div className="briefing-stat">
            <span>Operational risk</span>
            <strong className="risk-value risk-danger">
              {formatRiskState(risk.state)}
            </strong>
          </div>

          <div className="briefing-stat">
            <span>CatBoost probability</span>
            <strong>
              {typeof risk.ml_probability === 'number'
                ? `${(risk.ml_probability * 100).toFixed(1)}%`
                : 'Unavailable'}
            </strong>
          </div>

          <div className="briefing-stat">
            <span>Decision threshold</span>
            <strong>
              {typeof risk.ml_threshold === 'number'
                ? `${(risk.ml_threshold * 100).toFixed(1)}%`
                : 'Unavailable'}
            </strong>
          </div>

          <div className="briefing-stat">
            <span>ML classification</span>
            <strong
              className={
                risk.ml_is_at_risk
                  ? 'risk-danger'
                  : 'risk-safe'
              }
            >
              {risk.ml_available
                ? risk.ml_is_at_risk
                  ? 'At risk'
                  : 'Not at risk'
                : 'Unavailable'}
            </strong>
          </div>
        </div>

        {risk.ml_available &&
          risk.ml_is_at_risk !== null &&
          risk.state === 'at_risk' &&
          !risk.ml_is_at_risk && (
            <div className="briefing-note briefing-note-warning">
              <AlertTriangle size={14} />

              <span>
                Operational status and ML classification differ.
                The shipment is operationally delayed even though
                its predicted probability is below the model
                threshold.
              </span>
            </div>
          )}
      </div>

      <div className="briefing-section">
        <div className="briefing-section-heading">
          <span className="briefing-section-label">
            INVESTIGATION EVIDENCE
          </span>

          <span className="briefing-count">
            {evidence.length} signals
          </span>
        </div>

        <div className="briefing-evidence-grid">
          <div className="briefing-evidence-item">
            <div className="briefing-evidence-icon">
              <Truck size={15} />
            </div>

            <div>
              <span>Shipment status</span>
              <strong>
                {statusEvidence?.value ||
                  shipment.status ||
                  'Unavailable'}
              </strong>
            </div>
          </div>

          <div className="briefing-evidence-item">
            <div className="briefing-evidence-icon">
              <Clock3 size={15} />
            </div>

            <div>
              <span>Estimated arrival</span>
              <strong>
                {etaEvidence?.value
                  ? formatDate(etaEvidence.value)
                  : 'Unavailable'}
              </strong>
            </div>
          </div>

          <div className="briefing-evidence-item">
            <div className="briefing-evidence-icon">
              <CloudSun size={15} />
            </div>

            <div>
              <span>Weather</span>

              <strong>
                {weather
                  ? `${Number(weather.temperature_c).toFixed(1)}°C · ${Number(
                      weather.precipitation_mm,
                    ).toFixed(1)} mm rain`
                  : 'Unavailable'}
              </strong>
            </div>
          </div>

          <div className="briefing-evidence-item">
            <div className="briefing-evidence-icon">
              <MapPin size={15} />
            </div>

            <div>
              <span>Route intelligence</span>
              <strong>
                {routes.length > 0
                  ? `${routes.length} route options`
                  : 'Unavailable'}
              </strong>
            </div>
          </div>

          <div className="briefing-evidence-item">
            <div className="briefing-evidence-icon">
              <FileText size={15} />
            </div>

            <div>
              <span>Knowledge base</span>
              <strong>
                {knowledge.length > 0
                  ? `${knowledge.length} relevant sources`
                  : 'No results'}
              </strong>
            </div>
          </div>

          <div className="briefing-evidence-item">
            <div className="briefing-evidence-icon">
              <Globe2 size={15} />
            </div>

            <div>
              <span>External news</span>
              <strong>
                {news.length > 0
                  ? `${news.length} relevant records`
                  : 'No results'}
              </strong>
            </div>
          </div>
        </div>
      </div>

      {routes.length > 0 && (
        <div className="briefing-section">
          <div className="briefing-section-heading">
            <span className="briefing-section-label">
              ROUTE OPTIONS
            </span>

            <span className="briefing-count">
              Human approval required
            </span>
          </div>

          <div className="briefing-routes">
            {routes.map((route) => (
              <div
                className="briefing-route"
                key={route.route_id}
              >
                <div>
                  <span>
                    {route.recommendation ||
                      `Route ${route.route_id}`}
                  </span>

                  <strong>
                    {Number(route.distance_km).toFixed(1)} km
                  </strong>
                </div>

                <div className="briefing-route-time">
                  <Clock3 size={13} />

                  {Number(route.duration_minutes / 60).toFixed(
                    1,
                  )}{' '}
                  hrs
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="briefing-section">
        <div className="briefing-section-heading">
          <span className="briefing-section-label">
            OBSERVED RISK SIGNALS
          </span>
        </div>

        <div className="briefing-signals">
          <div>
            <Check size={14} />
            <span>Operational shipment exception confirmed.</span>
          </div>

          {etaPassed && (
            <div>
              <Check size={14} />
              <span>Estimated arrival time has passed.</span>
            </div>
          )}

          {weather && (
            <div>
              <Check size={14} />
              <span>
                Weather data is available, but does not establish
                causality.
              </span>
            </div>
          )}

          {routes.length > 0 && (
            <div>
              <Check size={14} />
              <span>
                Alternative routes are available for human review.
              </span>
            </div>
          )}

          {!news.length && (
            <div className="signal-muted">
              <CircleHelp size={14} />
              <span>
                No relevant external news evidence was returned.
              </span>
            </div>
          )}

          {!suppliers.length && (
            <div className="signal-muted">
              <CircleHelp size={14} />
              <span>
                No verified alternative suppliers were supplied.
              </span>
            </div>
          )}
        </div>
      </div>

      <div className="briefing-action">
        <div className="briefing-action-icon">
          <ShieldCheck size={17} />
        </div>

        <div>
          <span>RECOMMENDED HUMAN REVIEW</span>

          <p>
            Verify the confirmed shipment status, ETA, model
            estimate, available routes, and applicable operating
            procedures before taking action. SentinelAI does not
            automatically reroute shipments or change suppliers.
          </p>
        </div>

        <span className="briefing-human-badge">
          Human decision
        </span>
      </div>

      <div className="briefing-uncertainty">
        <CircleHelp size={14} />

        <div>
          <strong>Uncertainties</strong>

          <span>
            {weather
              ? 'Weather evidence is available but does not prove the cause of the delay.'
              : 'Weather evidence is unavailable.'}{' '}
            External news returned {news.length} result
            {news.length === 1 ? '' : 's'}. External evidence may
            be incomplete or unrelated to this shipment.
          </span>
        </div>
      </div>
    </div>
  );
}

function Metric({
  label,
  value,
  delta,
  up,
  note,
  icon: Icon,
  tone,
  alert,
}) {
  return (
    <div className="metric-card">
      <div className={`metric-icon ${tone}`}>
        <Icon size={18} />
      </div>

      <div className="metric-label">{label}</div>

      <div className="metric-bottom">
        <strong>{value}</strong>

        <span
          className={`metric-delta ${
            alert
              ? 'delta-alert'
              : up
                ? 'delta-up'
                : 'delta-down'
          }`}
        >
          {up ? (
            <ArrowUpRight size={13} />
          ) : (
            <ArrowDownRight size={13} />
          )}
          {delta}
        </span>
      </div>

      <div className="metric-note">{note}</div>

      <div className={`metric-spark ${tone}`}>
        <svg
          viewBox="0 0 90 34"
          preserveAspectRatio="none"
        >
          <path
            d={
              alert
                ? 'M0 26 C12 25 12 12 25 16 S37 29 48 16 S63 19 70 7 S82 14 90 3'
                : 'M0 26 C10 22 14 27 22 18 S33 22 41 12 S55 17 63 10 S77 14 90 4'
            }
          />
        </svg>
      </div>
    </div>
  );
}

createRoot(document.getElementById('root')).render(
  <App />,
);
