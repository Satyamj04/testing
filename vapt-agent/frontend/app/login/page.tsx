'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { authAPI } from '@/lib/api';
import { Shield, Lock, AlertCircle, Eye, EyeOff } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [username, setUsername] = useState('');
  const [fullName, setFullName] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isRegister) {
        await authAPI.register({ email, username, password, full_name: fullName });
        // Auto-login after register
      }
      const res = await authAPI.login(email, password);
      localStorage.setItem('access_token', res.data.access_token);
      localStorage.setItem('refresh_token', res.data.refresh_token);
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Authentication failed. Check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0a0c14 0%, #0f1117 50%, #0a0c14 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Background grid */}
      <div style={{
        position: 'absolute', inset: 0,
        backgroundImage: 'linear-gradient(rgba(124,58,237,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(124,58,237,0.03) 1px, transparent 1px)',
        backgroundSize: '50px 50px',
      }} />

      {/* Glow orbs */}
      <div style={{
        position: 'absolute', top: '20%', left: '10%',
        width: 300, height: 300,
        background: 'radial-gradient(circle, rgba(124,58,237,0.08) 0%, transparent 70%)',
        borderRadius: '50%',
      }} />
      <div style={{
        position: 'absolute', bottom: '20%', right: '10%',
        width: 250, height: 250,
        background: 'radial-gradient(circle, rgba(0,212,255,0.06) 0%, transparent 70%)',
        borderRadius: '50%',
      }} />

      <div style={{ position: 'relative', width: '100%', maxWidth: 440 }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 72,
            height: 72,
            background: 'linear-gradient(135deg, rgba(124,58,237,0.2), rgba(0,212,255,0.2))',
            border: '1px solid rgba(124,58,237,0.4)',
            borderRadius: 20,
            marginBottom: 16,
          }}>
            <Shield size={36} style={{ color: '#00d4ff' }} />
          </div>
          <h1 style={{
            fontSize: 28,
            fontWeight: 700,
            background: 'linear-gradient(135deg, #00d4ff, #7c3aed)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            margin: 0,
          }}>VAPT Agent</h1>
          <p style={{ color: '#6b7280', fontSize: 14, marginTop: 8, margin: '8px 0 0' }}>
            AI-Powered Security Testing Platform
          </p>
        </div>

        {/* Card */}
        <div style={{
          background: '#1a1d2e',
          border: '1px solid #2d2d3d',
          borderRadius: 16,
          padding: 32,
          boxShadow: '0 25px 50px rgba(0,0,0,0.5)',
        }}>
          {/* Tabs */}
          <div style={{ display: 'flex', gap: 4, background: '#0f1117', borderRadius: 8, padding: 4, marginBottom: 24 }}>
            {(['Login', 'Register'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => { setIsRegister(tab === 'Register'); setError(''); }}
                style={{
                  flex: 1,
                  padding: '8px',
                  borderRadius: 6,
                  border: 'none',
                  cursor: 'pointer',
                  fontWeight: 600,
                  fontSize: 14,
                  transition: 'all 0.2s',
                  background: (isRegister ? tab === 'Register' : tab === 'Login')
                    ? 'linear-gradient(135deg, rgba(124,58,237,0.3), rgba(0,212,255,0.3))'
                    : 'transparent',
                  color: (isRegister ? tab === 'Register' : tab === 'Login') ? '#00d4ff' : '#6b7280',
                }}
              >
                {tab}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {isRegister && (
              <>
                <div>
                  <label style={{ color: '#9ca3af', fontSize: 12, fontWeight: 600, marginBottom: 6, display: 'block' }}>
                    USERNAME
                  </label>
                  <input
                    className="input-cyber"
                    type="text"
                    placeholder="security_engineer"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label style={{ color: '#9ca3af', fontSize: 12, fontWeight: 600, marginBottom: 6, display: 'block' }}>
                    FULL NAME
                  </label>
                  <input
                    className="input-cyber"
                    type="text"
                    placeholder="John Doe"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                  />
                </div>
              </>
            )}

            <div>
              <label style={{ color: '#9ca3af', fontSize: 12, fontWeight: 600, marginBottom: 6, display: 'block' }}>
                EMAIL ADDRESS
              </label>
              <input
                className="input-cyber"
                type="email"
                placeholder="engineer@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div>
              <label style={{ color: '#9ca3af', fontSize: 12, fontWeight: 600, marginBottom: 6, display: 'block' }}>
                PASSWORD
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  className="input-cyber"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  style={{ paddingRight: 44 }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{
                    position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
                    background: 'none', border: 'none', cursor: 'pointer', color: '#6b7280',
                  }}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {error && (
              <div style={{
                display: 'flex', alignItems: 'center', gap: 8,
                background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
                borderRadius: 8, padding: '10px 14px', color: '#ef4444', fontSize: 13,
              }}>
                <AlertCircle size={16} />
                {error}
              </div>
            )}

            <button
              type="submit"
              className="btn-primary"
              disabled={loading}
              style={{ marginTop: 8, opacity: loading ? 0.7 : 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}
            >
              {loading ? (
                <div style={{ width: 16, height: 16, border: '2px solid white', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
              ) : (
                <Lock size={16} />
              )}
              {loading ? 'Authenticating...' : (isRegister ? 'Create Account' : 'Sign In')}
            </button>
          </form>

          <p style={{ textAlign: 'center', color: '#4b5563', fontSize: 12, marginTop: 24 }}>
            🔒 Authorized access only. All actions are logged.
          </p>
        </div>

        <p style={{ textAlign: 'center', color: '#374151', fontSize: 11, marginTop: 16 }}>
          VAPT Agent v1.0 — For authorized security testing only
        </p>
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
