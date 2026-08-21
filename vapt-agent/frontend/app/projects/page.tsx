'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { projectsAPI } from '@/lib/api';
import { FolderOpen, Plus, X, Loader2, ChevronRight, Target, Calendar, Trash2 } from 'lucide-react';

interface Project {
  id: string; name: string; description?: string; client_name?: string;
  status: string; target_count: number; created_at: string;
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ name: '', description: '', client_name: '' });
  const router = useRouter();

  const load = async () => {
    setLoading(true);
    try {
      const res = await projectsAPI.list();
      setProjects(res.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async () => {
    if (!form.name.trim()) return;
    setCreating(true);
    try {
      await projectsAPI.create(form);
      setShowCreate(false);
      setForm({ name: '', description: '', client_name: '' });
      await load();
    } catch (err) { console.error(err); }
    finally { setCreating(false); }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Delete this project and all associated data?')) return;
    await projectsAPI.delete(id);
    await load();
  };

  return (
    <div style={{ padding: 32 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 32 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700, margin: 0 }}>
            <span className="text-gradient-cyan">Projects</span>
          </h1>
          <p style={{ color: '#9ca3af', marginTop: 8, fontSize: 14 }}>
            Manage your security assessment projects and authorized targets
          </p>
        </div>
        <button className="btn-primary" onClick={() => setShowCreate(true)}
          style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Plus size={16} /> New Project
        </button>
      </div>

      {/* Create Modal */}
      {showCreate && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 1000, padding: 20,
        }}>
          <div className="card" style={{ width: '100%', maxWidth: 480, padding: 32, position: 'relative' }}>
            <button onClick={() => setShowCreate(false)}
              style={{ position: 'absolute', top: 16, right: 16, background: 'none', border: 'none', cursor: 'pointer', color: '#6b7280' }}>
              <X size={20} />
            </button>
            <h2 style={{ fontSize: 20, fontWeight: 700, margin: '0 0 24px', color: '#00d4ff' }}>
              Create New Project
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {[
                { label: 'PROJECT NAME *', key: 'name', placeholder: 'ContractIQ Security Assessment' },
                { label: 'CLIENT NAME', key: 'client_name', placeholder: 'Acme Corp' },
                { label: 'DESCRIPTION', key: 'description', placeholder: 'Security assessment for the production API' },
              ].map(({ label, key, placeholder }) => (
                <div key={key}>
                  <label style={{ color: '#9ca3af', fontSize: 11, fontWeight: 600, display: 'block', marginBottom: 6 }}>{label}</label>
                  <input className="input-cyber" placeholder={placeholder}
                    value={form[key as keyof typeof form]}
                    onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
                  />
                </div>
              ))}
              <button className="btn-primary" onClick={handleCreate} disabled={creating}
                style={{ marginTop: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
                {creating ? <Loader2 size={16} style={{ animation: 'spin 0.8s linear infinite' }} /> : <Plus size={16} />}
                {creating ? 'Creating...' : 'Create Project'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Projects grid */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: 80, color: '#6b7280' }}>
          <Loader2 size={32} style={{ animation: 'spin 0.8s linear infinite', margin: '0 auto' }} />
        </div>
      ) : projects.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 80 }}>
          <FolderOpen size={48} style={{ color: '#2d2d3d', margin: '0 auto 16px' }} />
          <p style={{ color: '#6b7280', fontSize: 16 }}>No projects yet</p>
          <p style={{ color: '#4b5563', fontSize: 14, marginTop: 4 }}>Create your first security assessment project</p>
          <button className="btn-primary" onClick={() => setShowCreate(true)} style={{ marginTop: 20 }}>
            Create Project
          </button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 20 }}>
          {projects.map(p => (
            <div key={p.id} className="card" style={{ padding: 24, cursor: 'pointer', transition: 'transform 0.2s, border-color 0.2s' }}
              onClick={() => router.push(`/projects/${p.id}`)}
              onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-3px)'; e.currentTarget.style.borderColor = 'rgba(124,58,237,0.5)'; }}
              onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.borderColor = '#2d2d3d'; }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 16 }}>
                <div style={{
                  width: 40, height: 40,
                  background: 'linear-gradient(135deg, rgba(124,58,237,0.2), rgba(0,212,255,0.2))',
                  border: '1px solid rgba(124,58,237,0.3)',
                  borderRadius: 10,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <FolderOpen size={18} style={{ color: '#7c3aed' }} />
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{
                    fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 4,
                    background: p.status === 'active' ? 'rgba(34,197,94,0.15)' : 'rgba(107,114,128,0.15)',
                    color: p.status === 'active' ? '#22c55e' : '#9ca3af',
                  }}>{p.status.toUpperCase()}</span>
                  <button onClick={e => handleDelete(p.id, e)}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#4b5563', padding: 2 }}
                    onMouseEnter={e => (e.currentTarget.style.color = '#ef4444')}
                    onMouseLeave={e => (e.currentTarget.style.color = '#4b5563')}>
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
              <h3 style={{ fontSize: 16, fontWeight: 700, margin: '0 0 6px', color: '#e0e0e0' }}>{p.name}</h3>
              {p.client_name && <p style={{ fontSize: 12, color: '#7c3aed', margin: '0 0 8px' }}>{p.client_name}</p>}
              {p.description && <p style={{ fontSize: 13, color: '#6b7280', margin: '0 0 16px', lineHeight: 1.5 }}>{p.description}</p>}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: 16, borderTop: '1px solid #2d2d3d' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#6b7280', fontSize: 12 }}>
                  <Target size={12} />
                  <span>{p.target_count || 0} targets</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#6b7280', fontSize: 12 }}>
                  <Calendar size={12} />
                  <span>{new Date(p.created_at).toLocaleDateString()}</span>
                </div>
                <ChevronRight size={14} style={{ color: '#4b5563' }} />
              </div>
            </div>
          ))}
        </div>
      )}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
