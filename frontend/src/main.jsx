import Landing from './Landing.jsx';
import React, { useMemo, useState } from 'react';
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
  X,
  Zap,
} from 'lucide-react';
import './styles.css';

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL !== undefined
    ? import.meta.env.VITE_API_BASE_URL.replace(/\/$/, '')
    : '';
    
const DEFAULT_SHIPMENT_ID = '77202';

const nav = [
  ['landing', 'Home', Home],
  ['overview', 'Overview', LayoutDashboard],
  ['shipments', 'Shipments', Truck],
  ['alerts', 'Alerts', Bell],
  ['suppliers', 'Suppliers', Box],
];

function formatPercentage(value) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return '—';
  }

  return `${Math.round(value * 100)}%`;
}

function formatRiskStatus(probability, isAtRisk) {
  if (isAtRisk) {
    return probability >= 0.7 ? 'High risk' : 'At risk';
  }

  return probability >= 0.25 ? 'Monitor' : 'On track';
}

function riskTone(probability, isAtRisk) {
  if (isAtRisk || probability >= 0.5) {
    return 'high';
  }

  if (probability >= 0.3) {
    return 'medium';
  }

  return 'low';
}

function getDestination(shipment) {
  if (!shipment) {
    return 'Unknown destination';
  }

  return [shipment.destination_city, shipment.destination_country]
    .filter(Boolean)
    .join(', ');
}

function getRouteLabel(shipment) {
  if (!shipment) {
    return 'Route unavailable';
  }

  const destination = getDestination(shipment);

  if (destination === 'Unknown destination') {
    return 'Destination unavailable';
  }

  return `→ ${destination}`;
}

function getRiskEvidence(data) {
  const findings = Array.isArray(data?.investigation_findings)
    ? data.investigation_findings
    : [];

  if (findings.length > 0) {
    return findings[0];
  }

  if (data?.weather) {
    const weather = data.weather;

    const parts = [];

    if (typeof weather.temperature_c === 'number') {
      parts.push(`${weather.temperature_c.toFixed(1)}°C`);
    }

    if (typeof weather.precipitation_mm === 'number') {
      parts.push(`${weather.precipitation_mm.toFixed(1)} mm precipitation`);
    }

    if (typeof weather.wind_speed_kmh === 'number') {
      parts.push(`${weather.wind_speed_kmh.toFixed(0)} km/h wind`);
    }

    if (parts.length > 0) {
      return parts.join(' · ');
    }
  }

  if (data?.route_options?.length > 0) {
    return `${data.route_options.length} alternative route option${
      data.route_options.length === 1 ? '' : 's'
    } identified`;
  }

  return 'No additional investigation findings available';
}

function getSignalStatus(data) {
  return {
    weather: Boolean(data?.weather),
    news: Array.isArray(data?.news) && data.news.length > 0,
    route:
      Boolean(data?.route_context) ||
      (Array.isArray(data?.route_options) && data.route_options.length > 0),
    suppliers:
      Array.isArray(data?.supplier_options) &&
      data.supplier_options.length > 0,
  };
}

function normalizeAnalysis(data) {
  const shipment = data?.shipment || {};
  const risk = data?.risk_assessment || {};

  const probability =
    typeof risk.probability === 'number' ? risk.probability : 0;

  const isAtRisk = Boolean(risk.is_at_risk);

  const destination = getDestination(shipment);
  const routeLabel = getRouteLabel(shipment);

  const routeOptions = Array.isArray(data?.route_options)
    ? data.route_options
    : [];

  const supplierOptions = Array.isArray(data?.supplier_options)
    ? data.supplier_options
    : [];

  const news = Array.isArray(data?.news) ? data.news : [];

  const knowledgeResults = Array.isArray(data?.knowledge_results)
    ? data.knowledge_results
    : [];

  const signals = getSignalStatus(data);

  return {
    id: data?.shipment_id || shipment.shipment_id || DEFAULT_SHIPMENT_ID,
    name:
      shipment.product_categories ||
      `Shipment ${data?.shipment_id || DEFAULT_SHIPMENT_ID}`,
    route: routeLabel,
    destination,
    supplier: 'Supplier identity unavailable',
    status: shipment.status || 'Unknown',
    shippingMode: shipment.shipping_mode || 'Unknown',
    orderRegion: shipment.order_region || 'Unknown',
    orderDate: shipment.order_date || 'Unknown',
    scheduledDays: shipment.scheduled_shipping_days ?? '—',
    risk: Math.round(probability * 100),
    probability,
    threshold:
      typeof risk.threshold === 'number' ? risk.threshold : null,
    isAtRisk,
    riskStatus: formatRiskStatus(probability, isAtRisk),
    riskTone: riskTone(probability, isAtRisk),
    reason: getRiskEvidence(data),
    evidenceSource:
      signals.weather
        ? 'Open-Meteo weather signal'
        : signals.route
          ? 'Route intelligence'
          : signals.news
            ? 'Regional news'
            : 'SentinelAI investigation',
    recommendation:
      data?.recommended_actions?.length > 0
        ? data.recommended_actions[0]
        : isAtRisk
          ? 'Human review is recommended before operational action.'
          : 'Continue monitoring this shipment.',
    alternative:
      routeOptions.length > 0
        ? routeOptions[0]
        : supplierOptions.length > 0
          ? supplierOptions[0]
          : null,
    routeOptions,
    supplierOptions,
    news,
    knowledgeResults,
    findings: Array.isArray(data?.investigation_findings)
      ? data.investigation_findings
      : [],
    briefing:
      typeof data?.briefing === 'string'
        ? data.briefing
        : 'No briefing was generated.',
    signals,
    raw: data,
  };
}

function buildAlternativeText(shipment) {
  if (!shipment?.alternative) {
    return '';
  }

  const alternative = shipment.alternative;

  if (alternative.route_name) {
    const score =
      typeof alternative.demo_reliability_score === 'number'
        ? ` · demo reliability ${Math.round(
            alternative.demo_reliability_score * 100,
          )}%`
        : '';

    return `${alternative.route_name}${score}`;
  }

  if (alternative.supplier_name) {
    const score =
      typeof alternative.reliability_score === 'number'
        ? ` · reliability ${Math.round(
            alternative.reliability_score * 100,
          )}%`
        : '';

    return `${alternative.supplier_name}${score}`;
  }

  return 'Alternative operational option identified';
}

function App() {
  const [active, setActive] = useState('landing');
  const [selected, setSelected] = useState(null);
  const [shipmentId, setShipmentId] = useState(DEFAULT_SHIPMENT_ID);
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('All');
  const [toast, setToast] = useState('');
  const [mobile, setMobile] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const notify = (message) => {
    setToast(message);
    setTimeout(() => setToast(''), 2600);
  };

  const analyzeShipment = async (id = shipmentId) => {
    const normalizedId = String(id || '').trim();

    if (!normalizedId) {
      setError('Enter a shipment ID before running an analysis.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/api/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          shipment_id: normalizedId,
        }),
      });

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

  const filtered = useMemo(() => {
    if (!selected) {
      return [];
    }

    const matchesQuery = `${selected.id} ${selected.name} ${selected.route} ${selected.supplier}`
      .toLowerCase()
      .includes(query.toLowerCase());

    const matchesFilter =
      filter === 'All' ||
      (filter === 'At risk' && selected.isAtRisk) ||
      (filter === 'On track' && !selected.isAtRisk);

    return matchesQuery && matchesFilter ? [selected] : [];
  }, [selected, query, filter]);

  const handleNav = (key) => {
    if (key === 'landing') {
      setActive('landing');
      setMobile(false);
      return;
    }

    if (key === 'shipments') {
      setActive('shipments');
      setMobile(false);
      return;
    }

    if (key === 'alerts') {
      setActive('alerts');
      setMobile(false);

      if (selected?.isAtRisk) {
        notify('The selected shipment requires human review.');
      } else {
        notify('No active risk alert is loaded.');
      }

      return;
    }

    setActive(key);
    setMobile(false);
  };

  if (active === 'landing') {
    return (
      <Landing
        openDashboard={() => {
          setActive('overview');

          if (!selected) {
            analyzeShipment(DEFAULT_SHIPMENT_ID);
          }
        }}
      />
    );
  }

  const currentRisk = selected?.risk ?? 0;
  const currentStatus = selected?.riskStatus || 'Not analyzed';

  const signalCount = selected
    ? [
        selected.signals.weather,
        selected.signals.route,
        selected.signals.news,
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

              {key === 'alerts' && selected?.isAtRisk && (
                <em className="nav-count">1</em>
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
            <span className="source-live">DataCo</span>
          </div>

          <div>
            <span className="live-dot weather-dot" /> Weather
            <span className="source-live">
              {selected?.signals.weather ? 'Live' : 'Unavailable'}
            </span>
          </div>

          <div>
            <span className="source-dot" /> Regional news
            <span className="source-live paused">
              {selected?.signals.news ? 'Available' : 'Optional'}
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
            onClick={() => notify('Settings will be available in a later release.')}
          >
            <Settings2 size={17} />
            Settings
          </button>

          <button
            className="nav-link"
            onClick={() => notify('Help center will be available in a later release.')}
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

            <MoreHorizontal size={17} className="muted" />
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
              {nav.find((n) => n[0] === active)?.[1] || 'Overview'}
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
                notify('Enter a shipment ID and run SentinelAI analysis.')
              }
            >
              <CircleHelp size={18} />
            </button>

            <button
              className="icon-btn notification-btn"
              onClick={() => handleNav('alerts')}
            >
              <Bell size={18} />
              {selected?.isAtRisk && <i />}
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
                {selected?.isAtRisk && (
                  <span className="eyebrow-live">
                    <span className="live-dot" />
                    REVIEW REQUIRED
                  </span>
                )}
              </div>

              <h1>
                Supply chain intelligence <span className="wave">✳</span>
              </h1>

              <p className="subtitle">
                Predict disruption risk, investigate evidence, and support
                human operational decisions.
              </p>
            </div>

            <div className="header-actions">
              <div className="shipment-input">
                <Search size={15} />

                <input
                  value={shipmentId}
                  onChange={(event) => setShipmentId(event.target.value)}
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
                    notify('Run an analysis before exporting a report.');
                    return;
                  }

                  notify('Report export will be connected to the briefing pipeline.');
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
                <b>Analysis unavailable</b>
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

          <section className="metrics-grid">
            <Metric
              label="Current shipment"
              value={selected?.id || '—'}
              delta={selected ? selected.status.replaceAll('_', ' ') : 'Not analyzed'}
              up={false}
              note="DataCo shipment record"
              icon={Truck}
              tone="lavender"
            />

            <Metric
              label="Delay risk"
              value={selected ? `${currentRisk}%` : '—'}
              delta={selected ? currentStatus : 'Awaiting analysis'}
              up={selected?.isAtRisk}
              note={
                selected?.threshold !== null && selected?.threshold !== undefined
                  ? `Model threshold ${Math.round(selected.threshold * 100)}%`
                  : 'Risk assessment'
              }
              icon={AlertTriangle}
              tone="peach"
              alert={selected?.isAtRisk}
            />

            <Metric
              label="Evidence signals"
              value={selected ? signalCount : '—'}
              delta={
                selected
                  ? `${selected.routeOptions.length} route option${
                      selected.routeOptions.length === 1 ? '' : 's'
                    }`
                  : 'Not analyzed'
              }
              up={signalCount > 0}
              note="Available investigation evidence"
              icon={PackageCheck}
              tone="mint"
            />

            <Metric
              label="Knowledge sources"
              value={selected ? selected.knowledgeResults.length : '—'}
              delta="RAG results"
              up={selected?.knowledgeResults.length > 0}
              note="Operational procedures retrieved"
              icon={Clock3}
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
                    {selected.isAtRisk
                      ? 'Human review is recommended.'
                      : 'No elevated risk was detected.'}
                  </b>{' '}
                  SentinelAI assessed this shipment at{' '}
                  <b>{selected.risk}% delay risk</b>.{' '}
                  {selected.reason}
                </p>

                <button onClick={() => setActive('overview')}>
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
                  Enter a DataCo shipment ID above and run SentinelAI to
                  generate a risk assessment and investigation.
                </p>
              </div>

              <button
                className="btn btn-primary"
                onClick={() => analyzeShipment(DEFAULT_SHIPMENT_ID)}
                disabled={loading}
              >
                Analyze 77202 <ArrowRight size={14} />
              </button>
            </section>
          )}

          <section className="dashboard-grid">
            <div className="panel shipments-panel">
              <div className="panel-header">
                <div>
                  <h2>Shipment under investigation</h2>
                  <p>
                    Historical shipment data used by the SentinelAI
                    intelligence pipeline.
                  </p>
                </div>

                <button
                  className="text-button"
                  onClick={() => analyzeShipment()}
                  disabled={loading}
                >
                  Refresh analysis <ArrowRight size={14} />
                </button>
              </div>

              <div className="table-tools">
                <div className="search-field">
                  <Search size={15} />

                  <input
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    placeholder="Search analyzed shipment…"
                  />
                </div>

                <button
                  className="filter-btn"
                  onClick={() => {
                    setFilter(
                      filter === 'All'
                        ? 'At risk'
                        : filter === 'At risk'
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
                      'Shipment fields shown are sourced from the current analysis.',
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
                        onClick={() => setSelected(shipment)}
                        className="row-selected"
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
                              <b>{shipment.name}</b>

                              <small>
                                {shipment.id}
                                <span> · </span>
                                {shipment.shippingMode}
                              </small>
                            </div>
                          </div>
                        </td>

                        <td>
                          <b className="eta">
                            {shipment.destination}
                          </b>

                          <small className="eta-time">
                            {shipment.orderRegion}
                          </small>
                        </td>

                        <td>
                          <div className="risk-cell">
                            <div className="risk-bar">
                              <i
                                style={{
                                  width: `${shipment.risk}%`,
                                }}
                                className={
                                  shipment.risk >= 70
                                    ? 'high'
                                    : shipment.risk >= 40
                                      ? 'medium'
                                      : 'low'
                                }
                              />
                            </div>

                            <b>{shipment.risk}%</b>
                          </div>
                        </td>

                        <td>
                          <span
                            className={`status-pill ${
                              shipment.risk >= 70
                                ? 'status-high'
                                : shipment.risk >= 40
                                  ? 'status-medium'
                                  : 'status-low'
                            }`}
                          >
                            <i />
                            {shipment.riskStatus}
                          </span>
                        </td>

                        <td>
                          <button
                            className="row-open"
                            aria-label="View details"
                            onClick={(event) => {
                              event.stopPropagation();
                              setSelected(shipment);
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
                    {selected
                      ? 'No shipment matches the current search/filter.'
                      : 'Run an analysis to load shipment intelligence.'}
                  </div>
                )}
              </div>

              <div className="table-footer">
                <span>
                  Showing <b>{filtered.length}</b> analyzed shipment
                </span>

                <div>
                  <button className="page-btn" disabled>
                    <ChevronLeft size={15} />
                  </button>

                  <button className="page-number">1</button>

                  <button
                    className="page-btn"
                    disabled
                    title="Pagination will be connected when shipment listing is added."
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
                      {selected?.isAtRisk
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
                    <h2>{selected.name}</h2>

                    <p className="detail-id">
                      {selected.id}
                      <span> · </span>
                      {selected.supplier}
                    </p>

                    <div className="detail-route">
                      <div className="route-pin">
                        <MapPin size={14} />
                      </div>

                      <span>
                        {selected.destination}
                        {' · '}
                        {selected.orderRegion}
                      </span>

                      <button
                        className="icon-btn route-map"
                        onClick={() =>
                          notify(
                            'Map visualization will use route intelligence in the next UI integration.',
                          )
                        }
                      >
                        <ExternalLink size={14} />
                      </button>
                    </div>

                    <div className="detail-stats">
                      <div>
                        <small>ORDER DATE</small>
                        <b>{selected.orderDate}</b>
                      </div>

                      <div>
                        <small>SCHEDULED SHIPPING</small>
                        <b>{selected.scheduledDays} days</b>
                      </div>

                      <div>
                        <small>DELAY RISK</small>
                        <b
                          className={
                            selected.risk >= 70
                              ? 'text-red'
                              : selected.risk >= 40
                                ? 'text-amber'
                                : 'text-green'
                          }
                        >
                          {selected.risk}%
                          <span className="risk-sub">
                            {selected.riskStatus}
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
                        {selected.isAtRisk ? 'REVIEW' : 'SIGNAL'}
                      </span>
                    </div>

                    <div className="evidence">
                      <div className="evidence-line" />

                      <div>
                        <b>{selected.reason}</b>

                        <small>{selected.evidenceSource}</small>
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
                        Review this action <ArrowRight size={14} />
                      </button>
                    </div>
                  </>
                ) : (
                  <div className="empty-detail">
                    <Sparkles size={24} />
                    <h3>No analysis yet</h3>
                    <p>
                      Run SentinelAI on a shipment to inspect its risk,
                      evidence, alternatives, and operational procedures.
                    </p>
                  </div>
                )}
              </div>

              <div className="panel signal-panel">
                <div className="signal-head">
                  <div>
                    <h3>Signal sources</h3>
                    <p>Data availability for this investigation</p>
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
                        ? 'DataCo record loaded'
                        : 'Awaiting analysis'}
                    </small>
                  </div>

                  <span className="signal-ok">
                    <Check size={12} /> Available
                  </span>
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
                        : 'No observation returned'}
                    </small>
                  </div>

                  {selected?.signals.weather ? (
                    <span className="signal-ok">
                      <Check size={12} /> Available
                    </span>
                  ) : (
                    <span className="signal-warn">Unavailable</span>
                  )}
                </div>

                <div className="signal-row">
                  <div className="signal-type news">
                    <Globe2 size={15} />
                  </div>

                  <div>
                    <b>Regional news</b>
                    <small>
                      {selected?.signals.news
                        ? `${selected.news.length} article${
                            selected.news.length === 1 ? '' : 's'
                          }`
                        : 'No records returned'}
                    </small>
                  </div>

                  {selected?.signals.news ? (
                    <span className="signal-ok">
                      <Check size={12} /> Available
                    </span>
                  ) : (
                    <span className="signal-warn">Optional</span>
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
                        : 'Awaiting analysis'}
                    </small>
                  </div>

                  {selected?.routeOptions.length > 0 ? (
                    <span className="signal-ok">
                      <Check size={12} /> Available
                    </span>
                  ) : (
                    <span className="signal-warn">None</span>
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
                    Evidence-grounded decision support generated from the
                    current investigation.
                  </p>
                </div>

                <span className="briefing-badge">
                  <Sparkles size={13} />
                  Human review required
                </span>
              </div>

              <pre className="briefing-content">{selected.briefing}</pre>
            </section>
          )}

          <footer className="footer">
            <span>
              <span className="live-dot" />
              SentinelAI · Data and signals shown reflect the current
              analysis
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

createRoot(document.getElementById('root')).render(<App />);