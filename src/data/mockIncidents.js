export const mockIncidents = [
  {
    eventId: 'EVT-67F0D517',
    eventType: 'LOGIN',
    user: 'john.smith',
    ipAddress: '185.100.50.25',
    timestamp: '2026-08-27T18:06:38.046725+00:00',
    securityAnalysis: {
      riskScore: 100,
      severity: 'CRITICAL',
      detected: true,
      reasons: ['Multiple failed login attempts', 'Login from a new IP address', 'Login from a new location', 'Login from a new device', 'Impossible travel detected', 'Suspicious IP address'],
    },
    salesforce: { incidentCreated: true, incidentId: 'a01g800000g5Wu4AAE' },
  },
  { eventId: 'EVT-82A1F201', user: 'alice.wilson', ipAddress: '103.21.44.18', eventType: 'LOGIN', timestamp: '2026-08-27T16:44:12+00:00', securityAnalysis: { riskScore: 82, severity: 'CRITICAL', detected: true, reasons: ['Multiple failed login attempts', 'Login from a new location', 'Suspicious IP address'] }, salesforce: { incidentCreated: true, incidentId: 'a01g800000g5Wu4AAE' } },
  { eventId: 'EVT-91B2C310', user: 'robert.johnson', ipAddress: '172.16.10.25', eventType: 'LOGIN', timestamp: '2026-08-27T14:22:05+00:00', securityAnalysis: { riskScore: 68, severity: 'HIGH', detected: true, reasons: ['Login from a new device', 'Impossible travel detected'] }, salesforce: { incidentCreated: true, incidentId: 'a01g800000g5Wu4AAE' } },
  { eventId: 'EVT-12C4D901', user: 'michael.brown', ipAddress: '192.168.1.20', eventType: 'LOGIN', timestamp: '2026-08-27T11:08:49+00:00', securityAnalysis: { riskScore: 45, severity: 'MEDIUM', detected: false, reasons: ['Login from a new IP address'] }, salesforce: { incidentCreated: false, incidentId: null } },
  { eventId: 'EVT-45D7A221', user: 'sarah.davis', ipAddress: '10.10.20.15', eventType: 'LOGIN', timestamp: '2026-08-27T09:31:27+00:00', securityAnalysis: { riskScore: 20, severity: 'LOW', detected: false, reasons: ['Login from a new device'] }, salesforce: { incidentCreated: false, incidentId: null } },
]

export const dashboardStats = [
  { label: 'Total incidents', value: '128', change: '+12.5%', detail: 'vs last 30 days', icon: 'shield' },
  { label: 'Critical incidents', value: '12', change: '+4.2%', detail: 'requires attention', icon: 'alert' },
  { label: 'High risk', value: '27', change: '-8.1%', detail: 'vs last 30 days', icon: 'activity' },
  { label: 'Incidents today', value: '8', change: '+2', detail: 'since midnight', icon: 'clock' },
]
