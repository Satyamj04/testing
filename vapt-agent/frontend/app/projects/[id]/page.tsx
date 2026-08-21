'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { projectsAPI, targetsAPI, scopesAPI, scansAPI } from '@/lib/api';
import {
  ArrowLeft, Plus, Shield, CheckCircle, AlertCircle, X, Loader2,
  Play, Target, Globe, ChevronRight, Activity, Lock
} from 'lucide-react';

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [project, setProject] = useState<any>(null);
  const [targets, setTargets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddTarget, setShowAddTarget] = useState(false);
  const [targetForm, setTargetForm] = useState({ name: '', url: '', description: '', is_authorized: false, authorization_notes: '' });
  const [adding, setAdding] = useState(false);

  const load = async () => {
    const [pRes, tRes] = await Promise.all([
      projectsAPI.get(id),
      targetsAPI.list(id),
    ]);
    setProject(pRes.data);
    setTargets(tRes.data);
    setLoading(false);
  };

  useEffect(() => { if (id) load(); }, [id]);

  const handleAddTarget = async () => {
    if (!targetForm.name || !targetForm.url) return;
    setAdding(true);
    try {
      await targetsAPI.create(id, targetForm);
      setShowAddTarget(false);
      setTargetForm({ name: '', url: '', description: '', is_authorized: false, authorization_notes: '' });
      await load();
    } finally { setAdding(false); }
  };

  const handleStartScan = async (targetId: string) => {
    const target = targets.find(t => t.id === targetId);
    if (!target?.is_authorized) {
      alert('Target must be marked as authorized before starting a scan.');
      return;
    }
    try {
      await scansAPI.create({ target_id: targetId, scan_type: 'full' });
      router.push('/scans');
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Failed to start scan');
    }
  };

  if (loading) return (
    <div style={{ padding: 32, textAlign: 'center', paddingTop: 100 }}>
      <Loader2 size={32} style={{ color: '#7c3aed', animation: 'spin 0.8s linear infinite', margin: '0 auto' }} />
    </div>
  );

  return (
    <div style={{ padding: 32 }}>
      <button onClick={() => router.back()} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#6b7280', display: 'flex', alignItems: 'center', gap: 6, marginBottom: 24, fontSize: 13 }}>
        <ArrowLeft size={16} /> Back to Projects
      </button>

      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 32 }}>
        <div>
          <h1 style={{ fontSize: 26, fontWeight: 700, margin: 0 }}>
            <span className="text-gradient-cyan">{project?.name}</span>
          </h1>
          {project?.client_name && <p style={{ color: '#7c3aed', fontSize: 14, margin: '6px 0 0' }}>{project.client_name}</p>}
          {project?.description && <p style={{ color: '#9ca3af', fontSize: 14, margin: '6px 0 0' }}>{project.description}</p>}
        </div>
        <button className="btn-primary" onClick={() => setShowAddTarget(true)}
          style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Plus size={16} /> Add Target
        </button>
      </div>

      {/* Add Target Modal */}
      {showAddTarget && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: 20 }}>
          <div className="card" style={{ width: '100%', maxWidth: 520, padding: 32, position: 'relative' }}>
            <button onClick={() => setShowAddTarget(false)} style={{ position: 'absolute', top: 16, right: 16, background: 'none', border: 'none', cursor: 'pointer', color: '#6b7280' }}>
              <X size={20} />
            </button>
            <h2 style={{ fontSize: 20, fontWeight: 700, margin: '0 0 8px', color: '#00d4ff' }}>Add Authorized Target</h2>
            <p style={{ color: '#6b7280', fontSize: 13, margin: '0 0 24px' }}>
              ⚠️ Only add targets you own or have explicit written authorization to test.
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {[
                { label: 'TARGET NAME *', key: 'name', placeholder: 'Production API' },
                { label: 'TARGET URL *', key: 'url', placeholder: 'https://authorized-test.example.com' },
                { label: 'DESCRIPTION', key: 'description', placeholder: 'Main production REST API endpoint' },
                { label: 'AUTHORIZATION NOTES', key: 'authorization_notes', placeholder: 'Authorized by security team - Ticket: SEC-001' },
              ].map(({ label, key, placeholder }) => (
                <div key={key}>
                  <label style={{ color: '#9ca3af', fontSize: 11, fontWeight: 600, display: 'block', marginBottom: 6 }}>{label}</label>
                  <input className="input-cyber" placeholder={placeholder}
                    value={targetForm[key as keyof typeof targetForm] as string}
                    onChange={e => setTargetForm(f => ({ ...f, [key]: e.target.value }))}
                  />
                </div>
              ))}
              <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', padding: '12px 14px', background: '#0f1117', borderRadius: 8, border: '1px solid #2d2d3d' }}>
                <input type="checkbox" checked={targetForm.is_authorized}
                  onChange={e => setTargetForm(f => ({ ...f, is_authorized: e.target.checked }))}
                  style={{ width: 16, height: 16, accentColor: '#22c55e' }} />
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: targetForm.is_authorized ? '#22c55e' : '#e0e0e0' }}>
                    ✓ I confirm I am authorized to test this target
                  </div>
                  <div style={{ fontSize: 11, color: '#6b7280', marginTop: 2 }}>
                    Scanning unauthorized targets is illegal and unethical
                  </div>
                </div>
              </label>
              <button className="btn-primary" onClick={handleAddTarget} disabled={adding || !targetForm.is_authorized}
                style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, opacity: !targetForm.is_authorized ? 0.5 : 1 }}>
                {adding ? <Loader2 size={16} style={{ animation: 'spin 0.8s linear infinite' }} /> : <Target size={16} />}
                Add Authorized Target
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Targets */}
      <h2 style={{ fontSize: 18, fontWeight: 600, margin: '0 0 16px', color: '#e0e0e0' }}>Targets ({targets.length})</h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {targets.map(t => (
          <div key={t.id} className="card" style={{ padding: 24 }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                  <div style={{
                    width: 36, height: 36, borderRadius: 8,
                    background: t.is_authorized ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)',
                    border: `1px solid ${t.is_authorized ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)'}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    {t.is_authorized ? <CheckCircle size={18} style={{ color: '#22c55e' }} /> : <AlertCircle size={18} style={{ color: '#ef4444' }} />}
                  </div>
                  <div>
                    <h3 style={{ fontSize: 15, fontWeight: 700, margin: 0, color: '#e0e0e0' }}>{t.name}</h3>
                    <a href={t.url} target="_blank" rel="noopener noreferrer" style={{ fontSize: 12, color: '#00d4ff', textDecoration: 'none' }}>
                      <Globe size={10} style={{ display: 'inline', marginRight: 4 }} />{t.url}
                    </a>
                  </div>
                </div>
                {t.authorization_notes && (
                  <p style={{ fontSize: 12, color: '#6b7280', margin: '0 0 8px', paddingLeft: 46 }}>
                    <Lock size={10} style={{ display: 'inline', marginRight: 4 }} />{t.authorization_notes}
                  </p>
                )}
              </div>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <span className={`severity-badge ${t.is_authorized ? 'status-confirmed' : 'severity-high'}`}>
                  {t.is_authorized ? 'Authorized' : 'Unauthorized'}
                </span>
                <button onClick={() => router.push(`/targets/${t.id}`)} className="btn-secondary" style={{ padding: '6px 14px', fontSize: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
                  Configure <ChevronRight size={12} />
                </button>
                <button onClick={() => handleStartScan(t.id)} className="btn-primary" disabled={!t.is_authorized} style={{ padding: '6px 14px', fontSize: 12, display: 'flex', alignItems: 'center', gap: 6, opacity: !t.is_authorized ? 0.5 : 1 }}>
                  <Play size={12} /> Scan
                </button>
              </div>
            </div>
          </div>
        ))}
        {targets.length === 0 && (
          <div style={{ textAlign: 'center', padding: 60, color: '#6b7280' }}>
            <Target size={40} style={{ margin: '0 auto 12px', opacity: 0.3 }} />
            <p>No targets added yet. Add your first authorized target.</p>
          </div>
        )}
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
