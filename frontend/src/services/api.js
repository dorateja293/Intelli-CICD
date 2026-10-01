import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  timeout: 15000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('intelli_ci_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authService = {
  login: (data) => api.post('/auth/login', data),
  signup: (data) => api.post('/auth/register', data),
  getMe: () => api.get('/auth/me'),
};

export const profileService = {
  getProfile: () => authService.getMe(),
};

export const githubService = {
  getOAuthUrl: (redirectUri) => api.get('/github/oauth/login', { params: { redirect_uri: redirectUri } }),
  handleCallback: (code, state, redirectUri) => api.get('/github/oauth/callback', { params: { code, state, redirect_uri: redirectUri } }),
  getStatus: () => api.get('/github/status'),
  disconnect: () => api.post('/github/disconnect'),
  getRepositories: (params) => api.get('/github/repositories', { params }),
  selectRepository: (data) => api.post('/github/repositories/select', data),
  syncRepository: (repoId) => api.post(`/github/repositories/${repoId}/sync`),
  getSyncStatus: (repoId) => api.get(`/github/repositories/${repoId}/sync-status`),
  simulateWebhook: (data) => api.post('/github/simulate-webhook', data),
};

export const projectService = {
  getProjects: (params) => api.get('/repositories', { params }),
  createProject: (data) => api.post('/repositories', data),
  syncGitHubCommits: (data) => api.post('/github/sync-public', data),
  syncRegisteredGitHubRepo: (repoId) => api.post(`/repositories/${repoId}/sync`),
};

export const pipelineService = {
  getPipelines: (params) => api.get('/pipelines', { params }),
  getPipeline: (id) => api.get(`/pipelines/${id}`),
  getJobLogs: (jobId) => api.get(`/jobs/${jobId}/logs`),
  ingestPipeline: (data) => api.post('/pipelines/ingest', data),
};

export const commitService = pipelineService;

export const analyticsService = {
  getAnalytics: (days = 30, repositoryId = null) => api.get('/analytics/overview', { params: { days, repository_id: repositoryId } }),
  getDurations: (repositoryId = null) => api.get('/analytics/durations', { params: { repository_id: repositoryId } }),
  getStages: (repositoryId = null) => api.get('/analytics/stages', { params: { repository_id: repositoryId } }),
  getFailures: (repositoryId = null) => api.get('/analytics/failures', { params: { repository_id: repositoryId } }),
  getTrends: (days = 14, repositoryId = null) => api.get('/analytics/trends', { params: { days, repository_id: repositoryId } }),
};

export const predictorService = {
  predict: (data) => api.post('/predict', data),
  getStatus: () => api.get('/ml/status'),
  getInsights: () => api.get('/ml/insights'),
};

export const logsService = {
  analyze: (data) => api.post('/analyze-logs', data),
  process: (data) => api.post('/logs/process', data),
};

export const recommendationService = {
  getRecommendations: (repositoryId = null) => api.get('/recommendations', { params: { repository_id: repositoryId } }),
};

export const healthService = {
  getHealth: () => api.get('/health'),
};

export default api;
