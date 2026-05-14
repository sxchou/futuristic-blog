import apiClient from './client'

export const logsApi = {
  getStats: () => apiClient.get('/logs/stats'),
  
  getOperations: (params?: any) => apiClient.get('/logs/operations', { params }),
  getLogins: (params?: any) => apiClient.get('/logs/logins', { params }),
  getAccess: (params?: any) => apiClient.get('/logs/access', { params }),
  
  clearOperations: (days: number = 30) => apiClient.delete(`/logs/operations/clear?days=${days}`),
  clearLogins: (days: number = 30) => apiClient.delete(`/logs/logins/clear?days=${days}`),
  clearAccess: (days: number = 30) => apiClient.delete(`/logs/access/clear?days=${days}`),
  
  getExportOperationsCount: (params?: any) => apiClient.get('/logs/export/operations/count', { params }),
  getExportLoginsCount: (params?: any) => apiClient.get('/logs/export/logins/count', { params }),
  getExportAccessCount: (params?: any) => apiClient.get('/logs/export/access/count', { params }),
  
  getExportProgress: (taskId: string) => apiClient.get(`/logs/export/progress/${taskId}`),
  cancelExport: (taskId: string) => apiClient.post(`/logs/export/cancel/${taskId}`),
  clearExportProgress: (taskId: string) => apiClient.delete(`/logs/export/progress/${taskId}`),
  
  exportOperations: (params?: any, config?: any) => apiClient.get('/logs/export/operations', { 
    params, 
    responseType: 'blob',
    timeout: 300000,
    ...config
  }),
  exportLogins: (params?: any, config?: any) => apiClient.get('/logs/export/logins', { 
    params, 
    responseType: 'blob',
    timeout: 300000,
    ...config
  }),
  exportAccess: (params?: any, config?: any) => apiClient.get('/logs/export/access', { 
    params, 
    responseType: 'blob',
    timeout: 300000,
    ...config
  }),
}
