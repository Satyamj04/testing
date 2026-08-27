import { Activity, AlertTriangle, Check, CheckCircle2, Clock3, Cloud, Database, ExternalLink, LockKeyhole, Server, ShieldCheck, Sparkles, X } from 'lucide-react'

const iconMap = { shield: ShieldCheck, alert: AlertTriangle, activity: Activity, clock: Clock3 }

export function SeverityBadge({ severity }) {
  return <span className={`severity severity-${severity.toLowerCase()}`}><span />{severity}</span>
}

export function StatCard({ stat }) {
  const Icon = iconMap[stat.icon]
  return <article className="stat-card"><div className={`stat-icon stat-${stat.icon}`}><Icon size={19} /></div><div><p>{stat.label}</p><strong>{stat.value}</strong><small className={stat.change.startsWith('-') ? 'trend down' : 'trend'}>{stat.change} <em>{stat.detail}</em></small></div></article>
}

export function RiskOverview() {
  const risks = [['low', 'Low', 42], ['medium', 'Medium', 38], ['high', 'High', 27], ['critical', 'Critical', 12]]
  return <section className="panel risk-panel"><div className="section-heading"><div><span className="eyebrow">Risk distribution</span><h2>Risk overview</h2></div><span className="period">Last 30 days <span>⌄</span></span></div><div className="risk-list">{risks.map(([key, label, value]) => <div className="risk-row" key={key}><div className="risk-label"><span className={`risk-dot dot-${key}`} />{label}<strong>{value}</strong></div><div className="risk-bar"><i className={`bar-${key}`} style={{ width: `${(value / 42) * 100}%` }} /></div></div>)}</div><div className="risk-foot"><span><i className="legend-dot dot-critical" /> Needs attention</span><b>119 total scored events</b></div></section>
}

export function StatusPanel() {
  const services = [['AWS Lambda', 'Connected', Cloud, 'connected'], ['DynamoDB', 'Connected', Database, 'connected'], ['Salesforce', 'Connected', Server, 'connected'], ['Amazon Bedrock', 'Pending verification', Sparkles, 'pending']]
  return <section className="panel system-panel"><div className="section-heading"><div><span className="eyebrow">Infrastructure</span><h2>System status</h2></div><span className="live"><i /> Live</span></div><div className="service-list">{services.map(([name, status, Icon, state]) => <div className="service" key={name}><Icon size={17} /><span>{name}</span><small className={state}><i />{status}</small></div>)}</div></section>
}

export function IncidentTable({ incidents, onSelect }) {
  return <section className="panel incidents-panel"><div className="section-heading"><div><span className="eyebrow">Live event stream</span><h2>Recent security incidents</h2></div><button className="text-button" onClick={() => onSelect('all')}>View all incidents <span>↗</span></button></div><div className="table-wrap"><table><thead><tr><th>Event ID</th><th>User</th><th>IP address</th><th>Risk score</th><th>Severity</th><th>Detected</th><th>Timestamp</th><th /></tr></thead><tbody>{incidents.map((incident) => <tr key={incident.eventId} onClick={() => onSelect(incident.eventId)}><td><span className="event-id">{incident.eventId}</span></td><td><span className="user-cell"><span className="mini-avatar">{incident.user[0].toUpperCase()}</span>{incident.user}</span></td><td className="mono">{incident.ipAddress}</td><td><span className={`score score-${incident.securityAnalysis.severity.toLowerCase()}`}>{incident.securityAnalysis.riskScore}</span></td><td><SeverityBadge severity={incident.securityAnalysis.severity} /></td><td><span className={incident.securityAnalysis.detected ? 'detected' : 'not-detected'}><i />{incident.securityAnalysis.detected ? 'Detected' : 'Not detected'}</span></td><td className="timestamp">{new Date(incident.timestamp).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</td><td><button className="row-action" aria-label={`Open ${incident.eventId}`}><ExternalLink size={15} /></button></td></tr>)}</tbody></table></div></section>
}

export function FilterBar({ filters, setFilters, onClear }) {
  const update = (key, value) => setFilters((current) => ({ ...current, [key]: value }))
  return <div className="filter-bar"><label className="filter-search"><Activity size={16} /><input placeholder="Search incidents..." value={filters.search} onChange={(event) => update('search', event.target.value)} /></label><select value={filters.severity} onChange={(event) => update('severity', event.target.value)}><option value="All">All severities</option><option>Low</option><option>Medium</option><option>High</option><option>Critical</option></select><select value={filters.detected} onChange={(event) => update('detected', event.target.value)}><option value="All">All detection status</option><option>Detected</option><option>Not Detected</option></select><button className="clear-button" onClick={onClear}><X size={15} /> Clear filters</button></div>
}

export function DetailView({ incident, onBack }) {
  const analysis = incident.securityAnalysis
  return <div className="detail-page"><button className="back-button" onClick={onBack}>← Back to dashboard</button><div className="detail-heading"><div><span className="eyebrow">Incident record</span><h1>Security incident details</h1><p>Review the event context and response readiness for <b>{incident.eventId}</b>.</p></div><SeverityBadge severity={analysis.severity} /></div><div className="detail-grid"><section className="panel detail-card"><div className="section-heading"><div><span className="eyebrow">Event telemetry</span><h2>Incident summary</h2></div><span className="detected"><i />{analysis.detected ? 'Detected' : 'Not detected'}</span></div><div className="detail-fields"><Field label="Event ID" value={incident.eventId} mono /><Field label="User" value={incident.user} /><Field label="IP address" value={incident.ipAddress} mono /><Field label="Event type" value={incident.eventType} /><Field label="Timestamp" value="Aug 27, 2026 · 18:06:38 UTC" /><Field label="Salesforce" value={incident.salesforce.incidentCreated ? 'Record created' : 'Not created'} /></div></section><section className="panel score-panel"><span className="eyebrow">Threat assessment</span><div className="score-ring" style={{ '--score': `${analysis.riskScore * 3.6}deg` }}><div><strong>{analysis.riskScore}</strong><span>/ 100</span></div></div><SeverityBadge severity={analysis.severity} /><p>Risk score</p></section></div><div className="detail-lower"><section className="panel analysis-card"><div className="section-heading"><div><span className="eyebrow">Signal review</span><h2>Security analysis</h2></div><LockKeyhole size={18} /></div><ul className="reason-list">{analysis.reasons.map((reason) => <li key={reason}><Check size={15} />{reason}</li>)}</ul></section><AIAnalysisCard /><SalesforceCard incident={incident} /></div></div>
}

function Field({ label, value, mono }) { return <div><span>{label}</span><strong className={mono ? 'mono' : ''}>{value}</strong></div> }

function AIAnalysisCard() { return <section className="panel ai-card"><div className="ai-top"><div className="ai-icon"><Sparkles size={18} /></div><span className="eyebrow">Future capability</span></div><h2>AI security analysis</h2><p>AI analysis will be available soon. Connect your Bedrock workflow when verification is complete.</p><div className="ai-actions"><button disabled>Analyze with AI</button><button disabled>Generate recommendation</button><button disabled>Explain incident</button></div></section> }

function SalesforceCard({ incident }) { return <section className="panel salesforce-card"><div className="section-heading"><div><span className="eyebrow">Case management</span><h2>Salesforce integration</h2></div><CheckCircle2 className="success-icon" size={19} /></div><div className="salesforce-status"><span>Status</span><strong><i /> Connected</strong><span>Incident created</span><strong>{incident.salesforce.incidentCreated ? 'Yes' : 'No'}</strong><span>Salesforce incident ID</span><strong className="mono">{incident.salesforce.incidentId || 'Not available'}</strong></div><button className="outline-button" disabled><ExternalLink size={15} /> View Salesforce record</button></section> }

export function ActionCard() { return <section className="panel action-card"><div className="section-heading"><div><span className="eyebrow">Response playbook</span><h2>Recommended security actions</h2></div><span className="future-tag">Static preview</span></div><ul>{['Investigate recent login activity', "Verify user's identity", 'Review IP reputation', 'Check device history', 'Consider temporarily blocking the suspicious IP', 'Review authentication logs'].map((action) => <li key={action}><Check size={15} />{action}</li>)}</ul><p className="muted-note">AI-generated recommendations will appear here.</p></section> }
