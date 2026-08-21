'use client';

import { useEffect, useState } from 'react';
import { scansAPI, findingsAPI, projectsAPI } from '@/lib/api';
import {
  Shield, Bug, CheckCircle, AlertTriangle, Activity, Target,
  TrendingUp, Clock, BarChart2, Zap
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
  informational: '#6b7280',
};

export default function DashboardPage() {
  const [stats, setStats] = useState<any>({});
  const [findings, setFindings] = useState<any[]>([]);
  const [scans, setScans] = useState<any[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [projectsRes, scansRes, findingsRes] = await Promise.all([
          projectsAPI.list(),
          scansAPI.list(),
          findingsAPI.list(),
        ]);
        setProjects(projectsRes.data);
        setScans(scansRes.data);
        const allFindings = findingsRes.data;
        setFindings(allFindings);

        // Compute stats
        const severityCounts: Record<string, number> = {};
        const statusCounts: Record<string, number> = {};
        for (const f of allFindings) {
          severityCounts[f.severity] = (severityCounts[f.severity] || 0) + 1;
          statusCounts[f.status] = (statusCounts[f.status] || 0) + 1;
        }
        setStats({ severityCounts, statusCounts, totalFindings: allFindings.length });
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const severityChartData = Object.entries(stats.severityCounts || {}).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1), value, color: SEVERITY_COLORS[name] || '#6b7280'
  }));

  const activeScans = scans.filter(s => !['completed', 'failed', 'cancelled'].includes(s.status));
  const completedScans = scans.filter(s => s.status === 'completed');

  return (
    <div style={{ padding: 32 }}>
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, margin: 0 }}>
          <span className="text-gradient-cyan">Security Dashboard</span>
        </h1>
        <p style={{ color: '#9ca3af', marginTop: 8, fontSize: 14 }}>
          Real-time overview of your security assessment posture
        </p>
      </div>

      {/* Key Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 32 }}>
        {[
          { label: 'Total Findings', value: stats.totalFindings || 0, icon: Bug, color: '#7c3aed', sub: 'All severity levels' },
          { label: 'Confirmed', value: stats.statusCounts?.confirmed || 0, icon: CheckCircle, color: '#22c55e', sub: 'Validated findings' },
          { label: 'Critical / High', value: (stats.severityCounts?.critical || 0) + (stats.severityCounts?.high || 0), icon: AlertTriangle, color: '#ef4444', sub: 'Immediate attention' },
          { label: 'Active Scans', value: activeScans.length, icon: Activity, color: '#00d4ff', sub: 'Currently running' },
          { label: 'Projects', value: projects.length, icon: Target, color: '#f97316', sub: 'Total projects' },
          { label: 'Scans Done', value: completedScans.length, icon: TrendingUp, color: '#22c55e', sub: 'Completed scans' },
        ].map(({ label, value, icon: Icon, color, sub }) => (
          <div key={label} className="card" style={{ padding: 20, transition: 'transform 0.2s' }}
            onMouseEnter={e => (e.currentTarget.style.transform = 'translateY(-2px)')}
            onMouseLeave={e => (e.currentTarget.style.transform = 'translateY(0)')}>
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
              <div>
                <div style={{ fontSize: 36, fontWeight: 700, color, lineHeight: 1 }}>{value}</div>
                <div style={{ fontSize: 13, color: '#e0e0e0', fontWeight: 600, marginTop: 6 }}>{label}</div>
                <div style={{ fontSize: 11, color: '#6b7280', marginTop: 4 }}>{sub}</div>
              </div>
              <div style={{
                width: 42, height: 42, borderRadius: 10,
                background: `${color}1a`,
                border: `1px solid ${color}33`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <Icon size={20} style={{ color }} />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 32 }}>
        {/* Severity Chart */}
        <div className="card" style={{ padding: 24 }}>
          <h2 style={{ fontSize: 16, fontWeight: 600, margin: '0 0 20px', display: 'flex', alignItems: 'center', gap: 8 }}>
            <BarChart2 size={16} style={{ color: '#00d4ff' }} /> Findings by Severity
          </h2>
          {severityChartData.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40, color: '#6b7280', fontSize: 14 }}>
              No findings yet. Start a scan to see results.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={severityChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2d2d3d" />
                <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 12 }} />
                <YAxis tick={{ fill: '#9ca3af', fontSize: 12 }} />
                <Tooltip
                  contentStyle={{ background: '#1a1d2e', border: '1px solid #2d2d3d', borderRadius: 8 }}
                  labelStyle={{ color: '#e0e0e0' }}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {severityChartData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Recent Scans */}
        <div className="card" style={{ padding: 24 }}>
          <h2 style={{ fontSize: 16, fontWeight: 600, margin: '0 0 20px', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Clock size={16} style={{ color: '#7c3aed' }} /> Recent Scans
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {scans.slice(0, 5).map((scan) => (
              <div key={scan.id} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '10px 12px',
                background: '#0f1117',
                borderRadius: 8,
              }}>
                <div>
                  <div style={{ fontSize: 12, color: '#e0e0e0', fontFamily: 'monospace' }}>
                    {scan.id.substring(0, 8)}...
                  </div>
                  <div style={{ fontSize: 11, color: '#6b7280', marginTop: 2 }}>
                    {scan.findings_count} findings
                  </div>
                </div>
                <span className={`severity-badge status-${scan.status}`}>
                  {scan.status}
                </span>
              </div>
            ))}
            {scans.length === 0 && (
              <div style={{ textAlign: 'center', padding: 30, color: '#6b7280', fontSize: 14 }}>
                No scans yet
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Critical Findings */}
      <div className="card" style={{ padding: 24 }}>
        <h2 style={{ fontSize: 16, fontWeight: 600, margin: '0 0 20px', display: 'flex', alignItems: 'center', gap: 8 }}>
          <Zap size={16} style={{ color: '#ef4444' }} /> Critical & High Findings
        </h2>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #2d2d3d' }}>
                {['Finding', 'Severity', 'Status', 'OWASP', 'Detected By', 'CVSS'].map(h => (
                  <th key={h} style={{ padding: '8px 12px', textAlign: 'left', fontSize: 11, color: '#6b7280', fontWeight: 600, whiteSpace: 'nowrap' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {findings
                .filter(f => ['critical', 'high'].includes(f.severity))
                .slice(0, 10)
                .map(f => (
                  <tr key={f.id} style={{ borderBottom: '1px solid #1a1d2e' }}>
                    <td style={{ padding: '10px 12px', maxWidth: 280 }}>
                      <div style={{ fontSize: 13, color: '#e0e0e0', fontWeight: 500 }}>{f.title}</div>
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      <span className={`severity-badge severity-${f.severity}`}>{f.severity}</span>
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      <span className={`severity-badge status-${f.status}`}>{f.status}</span>
                    </td>
                    <td style={{ padding: '10px 12px', fontSize: 11, color: '#9ca3af', maxWidth: 150 }}>
                      {f.owasp_category || f.owasp_api_category || '—'}
                    </td>
                    <td style={{ padding: '10px 12px', fontSize: 11, color: '#9ca3af' }}>{f.detected_by}</td>
                    <td style={{ padding: '10px 12px', fontSize: 12, color: '#f97316', fontWeight: 600 }}>
                      {f.cvss_score || '—'}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
          {findings.filter(f => ['critical', 'high'].includes(f.severity)).length === 0 && (
            <div style={{ textAlign: 'center', padding: 40, color: '#6b7280', fontSize: 14 }}>
              No critical/high findings yet. This is great!
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
