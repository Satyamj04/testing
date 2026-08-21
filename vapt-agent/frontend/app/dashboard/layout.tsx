'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  Shield, LayoutDashboard, FolderOpen, Target, Wifi, History,
  RotateCcw, Map, Search, Bug, FileText, MessageSquare, LogOut,
  ChevronRight, Activity, Bell
} from 'lucide-react';

const NAV_ITEMS = [
  { href: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { href: '/projects', icon: FolderOpen, label: 'Projects' },
  { href: '/scans', icon: Activity, label: 'Scans' },
  { href: '/http-history', icon: History, label: 'HTTP History' },
  { href: '/repeater', icon: RotateCcw, label: 'Repeater' },
  { href: '/app-map', icon: Map, label: 'App Map' },
  { href: '/findings', icon: Bug, label: 'Findings' },
  { href: '/reports', icon: FileText, label: 'Reports' },
  { href: '/ai-chat', icon: MessageSquare, label: 'AI Assistant' },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [wsStatus, setWsStatus] = useState<'connected' | 'disconnected'>('disconnected');

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) { router.replace('/login'); return; }

    // Fetch user info
    import('@/lib/api').then(({ authAPI }) => {
      authAPI.me().then(res => setUser(res.data)).catch(() => {
        localStorage.removeItem('access_token');
        router.replace('/login');
      });
    });

    // WebSocket connection
    const wsUrl = (process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000').replace('http', 'ws');
    const ws = new WebSocket(`${wsUrl}/ws`);
    ws.onopen = () => setWsStatus('connected');
    ws.onclose = () => setWsStatus('disconnected');
    return () => ws.close();
  }, [router]);

  const handleLogout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    router.replace('/login');
  }, [router]);

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#0a0c14' }}>
      {/* Sidebar */}
      <aside style={{
        width: 240,
        background: '#0f1117',
        borderRight: '1px solid #2d2d3d',
        display: 'flex',
        flexDirection: 'column',
        position: 'fixed',
        top: 0,
        left: 0,
        height: '100vh',
        zIndex: 100,
        flexShrink: 0,
      }}>
        {/* Logo */}
        <div style={{
          padding: '20px 20px 16px',
          borderBottom: '1px solid #2d2d3d',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 36, height: 36,
              background: 'linear-gradient(135deg, rgba(124,58,237,0.3), rgba(0,212,255,0.3))',
              border: '1px solid rgba(124,58,237,0.5)',
              borderRadius: 10,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Shield size={18} style={{ color: '#00d4ff' }} />
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: 15, color: '#e0e0e0' }}>VAPT Agent</div>
              <div style={{ fontSize: 10, color: '#6b7280', marginTop: 1 }}>Security Platform</div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav style={{ flex: 1, padding: '12px 12px', overflowY: 'auto' }}>
          {NAV_ITEMS.map(({ href, icon: Icon, label }) => {
            const active = pathname === href || pathname.startsWith(href + '/');
            return (
              <Link
                key={href}
                href={href}
                className={`sidebar-item ${active ? 'active' : ''}`}
                style={{ marginBottom: 2, textDecoration: 'none' }}
              >
                <Icon size={16} />
                <span style={{ fontSize: 13 }}>{label}</span>
                {active && <ChevronRight size={12} style={{ marginLeft: 'auto', color: '#00d4ff' }} />}
              </Link>
            );
          })}
        </nav>

        {/* Status & User */}
        <div style={{ padding: 12, borderTop: '1px solid #2d2d3d' }}>
          {/* WebSocket status */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 12, padding: '6px 8px' }}>
            <div style={{
              width: 6, height: 6, borderRadius: '50%',
              background: wsStatus === 'connected' ? '#22c55e' : '#ef4444',
              boxShadow: wsStatus === 'connected' ? '0 0 6px #22c55e' : 'none',
            }} />
            <span style={{ fontSize: 11, color: '#6b7280' }}>
              {wsStatus === 'connected' ? 'Live feed active' : 'Reconnecting...'}
            </span>
          </div>

          {/* User info */}
          {user && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: 8,
              padding: '8px 8px',
              background: '#1a1d2e',
              borderRadius: 8,
            }}>
              <div style={{
                width: 30, height: 30, borderRadius: '50%',
                background: 'linear-gradient(135deg, #7c3aed, #00d4ff)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 12, fontWeight: 700, color: 'white',
                flexShrink: 0,
              }}>
                {user.username?.[0]?.toUpperCase() || 'U'}
              </div>
              <div style={{ flex: 1, overflow: 'hidden' }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: '#e0e0e0', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {user.username}
                </div>
                <div style={{ fontSize: 10, color: '#6b7280' }}>{user.role}</div>
              </div>
              <button
                onClick={handleLogout}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#6b7280', padding: 2 }}
                title="Logout"
              >
                <LogOut size={14} />
              </button>
            </div>
          )}
        </div>
      </aside>

      {/* Main content */}
      <main style={{ marginLeft: 240, flex: 1, overflow: 'auto' }}>
        {children}
      </main>
    </div>
  );
}
