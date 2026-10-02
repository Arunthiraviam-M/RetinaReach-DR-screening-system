import { api } from './client';

// ---- Auth ----
export const authApi = {
  register: (payload) => api.post('/auth/register', payload).then((r) => r.data),
  login: (payload) => api.post('/auth/login', payload).then((r) => r.data),
  me: () => api.get('/auth/me').then((r) => r.data),
  updatePreferences: (payload) => api.patch('/auth/me/preferences', payload).then((r) => r.data),
};

// ---- Patients ----
export const patientsApi = {
  create: (payload) => api.post('/patients', payload).then((r) => r.data),
  list: (params) => api.get('/patients', { params }).then((r) => r.data),
  get: (id) => api.get(`/patients/${id}`).then((r) => r.data),
  history: (id) => api.get(`/patients/${id}/history`).then((r) => r.data),
};

// ---- Studies ----
export const studiesApi = {
  create: (patientId) => api.post(`/studies?patient_id=${patientId}`).then((r) => r.data),
  upload: (studyId, modality, laterality, file, onProgress) => {
    const form = new FormData();
    form.append('file', file);
    const params = new URLSearchParams({ modality });
    if (laterality) params.append('laterality', laterality);
    return api
      .post(`/studies/${studyId}/upload?${params.toString()}`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: onProgress
          ? (evt) => onProgress(Math.round((evt.loaded * 100) / (evt.total || 1)))
          : undefined,
      })
      .then((r) => r.data);
  },
  analyze: (studyId) => api.post(`/studies/${studyId}/analyze`).then((r) => r.data),
  get: (studyId) => api.get(`/studies/${studyId}`).then((r) => r.data),
  listRecent: (limit = 20) => api.get('/studies', { params: { limit } }).then((r) => r.data),
};

// ---- Reports ----
export const reportsApi = {
  generate: (studyId) => api.post(`/studies/${studyId}/report`).then((r) => r.data),
  getLatest: (studyId) => api.get(`/studies/${studyId}/report`).then((r) => r.data),
  // Downloads the PDF as a blob (auth header is required, so a plain <a href>
  // won't work) and triggers a browser save via a temporary object URL.
  download: async (studyId, suggestedFilename = 'dr_screening_report.pdf') => {
    const response = await api.get(`/studies/${studyId}/report/download`, { responseType: 'blob' });
    const blobUrl = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = suggestedFilename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(blobUrl);
  },
};

// ---- Dashboard ----
export const dashboardApi = {
  get: (limit = 15) => api.get('/dashboard', { params: { limit } }).then((r) => r.data),
  districtReport: () => api.get('/dashboard/district-report').then((r) => r.data),
};

// ---- Simulation ----
export const simulationApi = {
  run: (payload) => api.post('/simulation/workflow', payload).then((r) => r.data),
  list: () => api.get('/simulation/workflow').then((r) => r.data),
};
