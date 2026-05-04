import apiClient from './client'

export const logsApi = {
  getStats: () => apiClient.get('/logs/stats'),
  
  getOperations: (params?: any) => apiClient.get('/logs/operations', { params }),
  getLogins: (params?: any) => apiClient.get('/logs/logins', { params }),
  getAccess: (params?: any) => apiClient.get('/logs/access', { params }),
  
  clearOperations: (days: number = 30) => apiClient.delete(`/logs/operations/clear?days=${days}`),
  clearLogins: (days: number = 30) => apiClient.delete(`/logs/logins/clear?days=${days}`),
  clearAccess: (days: number = 30) => apiClient.delete(`/logs/access/clear?days=${days}`),
}
