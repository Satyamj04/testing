import { dashboardStats, mockIncidents } from '../data/mockIncidents'

const wait = (value) => Promise.resolve(value)

export const getIncidents = () => wait(mockIncidents)
export const getIncidentById = (id) => wait(mockIncidents.find((incident) => incident.eventId === id))
export const getDashboardStats = () => wait(dashboardStats)
