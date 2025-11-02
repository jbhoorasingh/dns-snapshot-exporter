/**
 * API client for DNS Snapshot Exporter backend
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1';

const apiClient = axios.create({
  baseURL: `${API_BASE_URL}${API_PREFIX}`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Zones API
export const zonesAPI = {
  list: (params = {}) => apiClient.get('/zones', { params }),
  get: (id) => apiClient.get(`/zones/${id}`),
  create: (data) => apiClient.post('/zones', data),
  update: (id, data) => apiClient.patch(`/zones/${id}`, data),
  delete: (id) => apiClient.delete(`/zones/${id}`),
};

// Snapshots API
export const snapshotsAPI = {
  create: (zoneId) => apiClient.post('/snapshots', { zone_id: zoneId }),
  listForZone: (zoneId, limit = 100) => apiClient.get(`/snapshots/zone/${zoneId}`, { params: { limit } }),
  get: (id) => apiClient.get(`/snapshots/${id}`),
  getRecords: (id, recordType = null) =>
    apiClient.get(`/snapshots/${id}/records`, { params: recordType ? { record_type: recordType } : {} }),
  delete: (id) => apiClient.delete(`/snapshots/${id}`),
};

// Exports API
export const exportsAPI = {
  getFormats: () => apiClient.get('/exports/formats'),
  export: (snapshotId, format) => apiClient.post('/exports', { snapshot_id: snapshotId, format }),
  download: (snapshotId, format) =>
    apiClient.post('/exports/download', { snapshot_id: snapshotId, format }, { responseType: 'blob' }),
};

// Comparisons API
export const comparisonsAPI = {
  compare: (snapshotId1, snapshotId2) =>
    apiClient.post('/comparisons', { snapshot_id_1: snapshotId1, snapshot_id_2: snapshotId2 }),
};

// Jobs API
export const jobsAPI = {
  list: (params = {}) => apiClient.get('/jobs', { params }),
  get: (id) => apiClient.get(`/jobs/${id}`),
  create: (data) => apiClient.post('/jobs', data),
  update: (id, data) => apiClient.patch(`/jobs/${id}`, data),
  delete: (id) => apiClient.delete(`/jobs/${id}`),
};

export default apiClient;
