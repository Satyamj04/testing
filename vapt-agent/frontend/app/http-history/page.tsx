'use client';

import { useEffect, useState, useCallback } from 'react';
import { httpHistoryAPI, repeaterAPI } from '@/lib/api';
import { History, Filter, RotateCcw, Search, Copy, ChevronDown, ChevronRight } from 'lucide-react';

const STATUS_COLOR = (s: number) => {
  if (s < 300) return '#22c55e';
  if (s < 400) return '#00d4ff';
  if (s < 500) return '#eab308';
  return '#ef4444';
};

export default function HTTPHistoryPage() {
  const [requests, setRequests] = useState<any[]>([]);
  const [selected, setSelected] = useState<any>(null);
  const [selectedBody, setSelectedBody] = useState<{ request?: string; response?: string }>({});
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ method: '', status: '', host: '', path: '' });
  const [activeTab, setActiveTab] = useState<'request' | 'response'>('request');
  const [sending, setSending] = useState(false);

  const load = useCallback(async () => {
    const params: any = {};
    if (filter.method) params.method = filter.method;
    if (filter.status) params.status_code = parseInt(filter.status);
    if (filter.host) params.host = filter.host;
    if (filter.path) params.path_contains = filter.path;
    const res = await httpHistoryAPI.list(params);
    setRequests(res.data);
    setLoading(false);
  }, [filter]);

  useEffect(() => { load(); }, [load]);

  const selectRequest = async (req: any) => {
    setSelected(req);
    setSelectedBody({});
    setActiveTab('request');
    // Load body from storage
    try {
      const reqBody = await httpHistoryAPI.getBody(req.id, 'request');
      const respBody = await httpHistoryAPI.getBody(req.id, 'response');
      setSelectedBody({ request: reqBody.data.body, response: respBody.data.body });
    } catch { }
  };

  const sendToRepeater = async () => {
    if (!selected) return;
    setSending(true);
    try {
      await repeaterAPI.execute({ original_request_id: selected.id });
      alert('Sent to Repeater successfully');
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Failed to send to repeater');
    } finally { setSending(false); }
  };

  return (
    <div style={{ padding: 32 }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, margin: 0 }}>
          <span className="text-gradient-cyan">HTTP History</span>
        </h1>
        <p style={{ color: '#9ca3af', marginTop: 8, fontSize: 14 }}>Burp Suite-style HTTP request/response viewer</p>
      </div>

      {/* Filters */}
      <div className="card" style={{ padding: 16, marginBottom: 20, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <select className="input-cyber" style={{ width: 120 }} value={filter.method} onChange={e => setFilter(f => ({ ...f, method: e.target.value }))}>
          <option value="">All Methods</option>
          {['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS', 'HEAD'].map(m => <option key={m}>{m}</option>)}
        </select>
        <input className="input-cyber" style={{ width: 120 }} placeholder="Status" value={filter.status}
          onChange={e => setFilter(f => ({ ...f, status: e.target.value }))} />
        <input className="input-cyber" style={{ width: 180 }} placeholder="Host filter" value={filter.host}
          onChange={e => setFilter(f => ({ ...f, host: e.target.value }))} />
        <input className="input-cyber" style={{ flex: 1 }} placeholder="Path contains..." value={filter.path}
          onChange={e => setFilter(f => ({ ...f, path: e.target.value }))} />
        <button className="btn-primary" onClick={load} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <Search size={14} /> Filter
        </button>
      </div>

      {/* Split pane */}
      <div style={{ display: 'grid', gridTemplateColumns: selected ? '1fr 1.5fr' : '1fr', gap: 16 }}>
        {/* Request list */}
        <div className="card" style={{ overflow: 'hidden' }}>
          <div style={{ padding: '12px 16px', borderBottom: '1px solid #2d2d3d', fontSize: 12, color: '#6b7280', fontWeight: 600 }}>
            {requests.length} REQUESTS
          </div>
          <div style={{ overflow: 'auto', maxHeight: '70vh' }}>
            {requests.map((req, i) => (
              <div key={req.id} onClick={() => selectRequest(req)}
                style={{
                  padding: '10px 16px',
                  borderBottom: '1px solid #1a1d2e',
                  cursor: 'pointer',
                  background: selected?.id === req.id ? 'rgba(124,58,237,0.1)' : 'transparent',
                  transition: 'background 0.15s',
                  display: 'grid',
                  gridTemplateColumns: '50px 70px 1fr 50px',
                  gap: 8,
                  alignItems: 'center',
                }}
                onMouseEnter={e => { if (selected?.id !== req.id) e.currentTarget.style.background = '#1a1d2e'; }}
                onMouseLeave={e => { if (selected?.id !== req.id) e.currentTarget.style.background = 'transparent'; }}>
                <span style={{ fontSize: 11, fontWeight: 700, fontFamily: 'monospace' }} className={`method-${req.method}`}>{req.method}</span>
                <span style={{ fontSize: 12, color: STATUS_COLOR(req.response_status || 0), fontFamily: 'monospace' }}>{req.response_status || '—'}</span>
                <span style={{ fontSize: 11, color: '#9ca3af', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {req.host}{req.path}
                </span>
                <span style={{ fontSize: 10, color: '#4b5563', textAlign: 'right' }}>
                  {req.duration_ms ? `${Math.round(req.duration_ms)}ms` : ''}
                </span>
              </div>
            ))}
            {requests.length === 0 && !loading && (
              <div style={{ textAlign: 'center', padding: 60, color: '#6b7280', fontSize: 14 }}>
                <History size={32} style={{ margin: '0 auto 12px', opacity: 0.3 }} />
                <p>No requests captured yet.</p>
                <p style={{ fontSize: 12, marginTop: 4 }}>Configure your browser to use the proxy at port 8080</p>
              </div>
            )}
          </div>
        </div>

        {/* Request/Response viewer */}
        {selected && (
          <div className="card" style={{ overflow: 'hidden' }}>
            <div style={{ padding: '12px 16px', borderBottom: '1px solid #2d2d3d', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', gap: 4 }}>
                {(['request', 'response'] as const).map(tab => (
                  <button key={tab} onClick={() => setActiveTab(tab)}
                    style={{
                      padding: '4px 12px', borderRadius: 6, border: 'none', cursor: 'pointer', fontSize: 12, fontWeight: 600,
                      background: activeTab === tab ? 'rgba(124,58,237,0.2)' : 'transparent',
                      color: activeTab === tab ? '#00d4ff' : '#6b7280',
                    }}>
                    {tab.charAt(0).toUpperCase() + tab.slice(1)}
                  </button>
                ))}
              </div>
              <button className="btn-secondary" onClick={sendToRepeater} disabled={sending}
                style={{ padding: '4px 12px', fontSize: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
                <RotateCcw size={12} /> Send to Repeater
              </button>
            </div>

            <div style={{ padding: 16, maxHeight: '65vh', overflow: 'auto' }}>
              {/* URL bar */}
              <div style={{ marginBottom: 12, padding: '8px 12px', background: '#0f1117', borderRadius: 6, display: 'flex', gap: 8, alignItems: 'center' }}>
                <span className={`method-${selected.method}`} style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: 12 }}>{selected.method}</span>
                <span style={{ fontSize: 12, color: '#9ca3af', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis' }}>{selected.url}</span>
                <span style={{ fontSize: 12, fontWeight: 700, color: STATUS_COLOR(selected.response_status) }}>{selected.response_status}</span>
              </div>

              {/* Headers */}
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 11, color: '#6b7280', fontWeight: 600, marginBottom: 8 }}>
                  {activeTab === 'request' ? 'REQUEST HEADERS' : 'RESPONSE HEADERS'}
                </div>
                <div className="code-block" style={{ maxHeight: 200 }}>
                  {Object.entries(activeTab === 'request' ? (selected.request_headers || {}) : (selected.response_headers || {})).map(([k, v]) => (
                    <div key={k}><span style={{ color: '#7c3aed' }}>{k}</span>: <span style={{ color: '#a0a8c0' }}>{String(v)}</span></div>
                  ))}
                </div>
              </div>

              {/* Body */}
              <div>
                <div style={{ fontSize: 11, color: '#6b7280', fontWeight: 600, marginBottom: 8 }}>
                  {activeTab === 'request' ? 'REQUEST BODY' : 'RESPONSE BODY'}
                </div>
                <div className="code-block" style={{ maxHeight: 300 }}>
                  {selectedBody[activeTab] || '(empty)'}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
