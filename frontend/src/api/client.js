import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.message || 'Request failed'
    console.error('[API]', err.config?.url, msg)
    return Promise.reject(new Error(msg))
  },
)

export default api

export const accountsApi = {
  list: (params) => api.get('/api/accounts', { params }).then((r) => r.data),
  create: (payload) => api.post('/api/accounts', payload).then((r) => r.data),
  update: (id, payload) => api.put(`/api/accounts/${id}`, payload).then((r) => r.data),
  remove: (id) => api.delete(`/api/accounts/${id}`),
}

export const categoriesApi = {
  list: (params) => api.get('/api/categories', { params }).then((r) => r.data),
  create: (payload) => api.post('/api/categories', payload).then((r) => r.data),
  update: (id, payload) => api.put(`/api/categories/${id}`, payload).then((r) => r.data),
  remove: (id) => api.delete(`/api/categories/${id}`),
}

export const transactionsApi = {
  list: (params) => api.get('/api/transactions', { params }).then((r) => r.data),
  create: (payload) => api.post('/api/transactions', payload).then((r) => r.data),
  update: (id, payload) => api.put(`/api/transactions/${id}`, payload).then((r) => r.data),
  remove: (id) => api.delete(`/api/transactions/${id}`),
}

export const reportsApi = {
  dashboard: (params) => api.get('/api/reports/dashboard', { params }).then((r) => r.data),
  incomeStatement: (params) => api.get('/api/reports/income-statement', { params }).then((r) => r.data),
  balanceSheet: (params) => api.get('/api/reports/balance-sheet', { params }).then((r) => r.data),
  cashFlow: (params) => api.get('/api/reports/cash-flow', { params }).then((r) => r.data),
}
