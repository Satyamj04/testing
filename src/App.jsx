import { useEffect, useState } from 'react'
import { Activity, Bell, ChevronDown, LayoutDashboard, LogIn, Menu, Search, Settings, Shield, UserRound, X } from 'lucide-react'
import { ActionCard, DetailView, FilterBar, IncidentTable, RiskOverview, StatCard, StatusPanel } from './components/DashboardComponents'
import { getDashboardStats, getIncidents } from './services/api'
import './App.css'

function App() {
  const [page, setPage] = useState('dashboard')
  const [incidents, setIncidents] = useState([])
  const [stats, setStats] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [menuOpen, setMenuOpen] = useState(false)
  const [filters, setFilters] = useState({ search: '', severity: 'All', detected: 'All' })

  useEffect(() => {
    getIncidents().then(setIncidents)
    getDashboardStats().then(setStats)
  }, [])

  const selectedIncident = incidents.find((incident) => incident.eventId === selectedId)
  const filteredIncidents = incidents.filter((incident) => {
    const text = `${incident.eventId} ${incident.user} ${incident.ipAddress}`.toLowerCase()
    const matchesSearch = text.includes(filters.search.toLowerCase())
    const matchesSeverity = filters.severity === 'All' || incident.securityAnalysis.severity === filters.severity.toUpperCase()
    const matchesDetected = filters.detected === 'All' || (filters.detected === 'Detected') === incident.securityAnalysis.detected
    return matchesSearch && matchesSeverity && matchesDetected
  })

  const openIncident = (id) => {
    if (id === 'all') { setPage('incidents'); return }
    setSelectedId(id)
    setPage('detail')
  }

  const navigate = (nextPage) => { setPage(nextPage); setSelectedId(null); setMenuOpen(false) }

  return (
    <div className="app-shell">
      <aside className={`sidebar ${menuOpen ? 'open' : ''}`}>
        <div className="brand"><span className="brand-mark"><Shield size={18} /></span><span>CyberShield <b>360</b></span><button className="close-menu" onClick={() => setMenuOpen(false)}><X size={19} /></button></div>
        <p className="nav-label">Workspace</p>
        <nav><NavItem icon={LayoutDashboard} label="Dashboard" active={page === 'dashboard'} onClick={() => navigate('dashboard')} /><NavItem icon={Activity} label="Security incidents" active={page === 'incidents' || page === 'detail'} onClick={() => navigate('incidents')} /><NavItem icon={LogIn} label="Login events" onClick={() => navigate('incidents')} /><NavItem icon={Shield} label="Risk analysis" onClick={() => navigate('dashboard')} /><NavItem icon={Settings} label="Settings" onClick={() => navigate('dashboard')} /></nav>
        <div className="sidebar-footer"><div className="profile"><span className="avatar">SA</span><div><strong>Security Admin</strong><small>Administrator</small></div><ChevronDown size={15} /></div><div className="connection"><i /> AWS Connected</div></div>
      </aside>
      <main className="main-content">
        <header className="topbar"><button className="menu-button" onClick={() => setMenuOpen(true)}><Menu size={21} /></button><div className="mobile-title">CyberShield 360</div><label className="global-search"><Search size={17} /><input placeholder="Search anything..." /></label><div className="top-actions"><span className="environment"><i /> AWS Connected</span><button className="icon-button" aria-label="Notifications"><Bell size={19} /><b /></button><span className="top-avatar">SA</span><span className="admin-name">Security Admin</span><ChevronDown size={15} /></div></header>
        {selectedIncident && page === 'detail' ? <DetailView incident={selectedIncident} onBack={() => setPage('dashboard')} /> : <>
          <div className="page-header"><div><span className="eyebrow">Security operations center</span><h1>{page === 'incidents' ? 'Security incidents' : 'Security dashboard'}</h1><p>{page === 'incidents' ? 'Search and review all security events from your connected sources.' : 'A clear view of your organization’s security posture.'}</p></div><span className="date-chip">August 27, 2026 <ChevronDown size={14} /></span></div>
          {page === 'incidents' ? <><FilterBar filters={filters} setFilters={setFilters} onClear={() => setFilters({ search: '', severity: 'All', detected: 'All' })} /><IncidentTable incidents={filteredIncidents} onSelect={openIncident} /></> : <><div className="stats-grid">{stats.map((stat) => <StatCard stat={stat} key={stat.label} />)}</div><div className="overview-grid"><RiskOverview /><StatusPanel /></div><IncidentTable incidents={incidents.slice(0, 5)} onSelect={openIncident} /><div className="bottom-grid"><ActionCard /><section className="panel notice-panel"><div className="notice-icon"><UserRound size={18} /></div><div><span className="eyebrow">Analyst workspace</span><h2>Stay ahead of risk</h2><p>Review critical incidents first to keep your environment resilient.</p></div></section></div></>}
        </>}
      </main>
    </div>
  )
}

function NavItem({ icon: Icon, label, active, onClick }) { return <button className={`nav-item ${active ? 'active' : ''}`} onClick={onClick}><Icon size={18} /><span>{label}</span>{active && <i />}</button> }

export default App
