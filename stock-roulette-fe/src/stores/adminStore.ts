import { defineStore } from 'pinia'
import api from '@/services/api'

interface ApiError {
  response?: {
    data?: {
      message?: string
    }
  }
}

export interface Session {
  session_id: string
  player_id: number
  player_nickname: string
  started_at: string
  ended_at: string | null
  status: 'active' | 'ended' | 'finished'
  balance: number
  total_score: number
  total_profit: number
  total_trades: number
}



export interface LeaderboardEntry {
  rank: number
  player_id: number
  nickname: string
  total_score: number
  total_profit: number
  total_trades: number
  sessions_played: number
  average_score: number
  win_rate: number
}

export const useAdminStore = defineStore('admin', {
  state: () => ({
    isAuthenticated: false,
    sessions: [] as Session[],

    leaderboard: [] as LeaderboardEntry[],
    loading: false,
    error: null as string | null,
    sessionFilters: {
      player: '',
      dateFrom: '',
      dateTo: '',
      status: 'all' as 'all' | 'active' | 'ended' | 'finished',
    },
  }),

  getters: {
    filteredSessions: (state) => {
      if (!Array.isArray(state.sessions)) {
        return []
      }
      return state.sessions.filter((session) => {
        const matchesPlayer =
          !state.sessionFilters.player ||
          session.player_nickname.toLowerCase().includes(state.sessionFilters.player.toLowerCase())

        const matchesStatus =
          state.sessionFilters.status === 'all' || session.status === state.sessionFilters.status

        const matchesDateFrom =
          !state.sessionFilters.dateFrom ||
          new Date(session.started_at) >= new Date(state.sessionFilters.dateFrom)

        const matchesDateTo =
          !state.sessionFilters.dateTo ||
          new Date(session.started_at) <= new Date(state.sessionFilters.dateTo)

        return matchesPlayer && matchesStatus && matchesDateFrom && matchesDateTo
      })
    },

    sortedLeaderboard: (state) => {
      if (!Array.isArray(state.leaderboard)) {
        return []
      }
      return [...state.leaderboard].sort((a, b) => b.total_score - a.total_score)
    },
  },

  actions: {
    async login(username: string, password: string) {
      try {
        this.loading = true
        this.error = null

        // Create form data for the request
        const formData = new URLSearchParams()
        formData.append('login', username)
        formData.append('password', password)

        const response = await api.post('/api/admin/login', formData, {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        })

        // Check if login was successful based on the actual response structure
        if (response.data.token && response.data.message === 'Logged in') {
          this.isAuthenticated = true
          // Store auth token
          localStorage.setItem('adminToken', response.data.token)
          api.defaults.headers.common['Authorization'] = `Bearer ${response.data.token}`
          return true
        }
        return false
      } catch (error: unknown) {
        const axiosError = error as { response?: { data?: { message?: string } } }
        this.error = axiosError.response?.data?.message || 'Login failed'
        return false
      } finally {
        this.loading = false
      }
    },

    logout() {
      this.isAuthenticated = false
      localStorage.removeItem('adminToken')
      delete api.defaults.headers.common['Authorization']
    },

    checkAuth() {
      const token = localStorage.getItem('adminToken')
      if (token) {
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`
        this.isAuthenticated = true
      }
    },

    async fetchSessions() {
      try {
        this.loading = true
        this.error = null

        const response = await api.get('/api/admin/sessions')
        // Handle the nested sessions structure from the API
        const sessionsData = response.data.sessions || response.data
        this.sessions = Array.isArray(sessionsData) ? sessionsData : []
      } catch (error: unknown) {
        const axiosError = error as ApiError
        this.error = axiosError.response?.data?.message || 'Failed to fetch sessions'
        this.sessions = [] // Ensure sessions is always an array
      } finally {
        this.loading = false
      }
    },



    async fetchLeaderboard() {
      try {
        this.loading = true
        this.error = null

        const response = await api.get('/api/admin/leaderboard')
        // Handle the nested leaderboard structure from the API
        const leaderboardData = response.data.leaderboard || response.data
        this.leaderboard = Array.isArray(leaderboardData) ? leaderboardData : []
      } catch (error: unknown) {
        const axiosError = error as ApiError
        this.error = axiosError.response?.data?.message || 'Failed to fetch leaderboard'
        this.leaderboard = [] // Ensure leaderboard is always an array
      } finally {
        this.loading = false
      }
    },

    async deleteSession(sessionId: string) {
      try {
        this.loading = true
        this.error = null

        await api.delete(`/api/admin/sessions/${sessionId}`)
        if (Array.isArray(this.sessions)) {
          this.sessions = this.sessions.filter((s) => s.session_id !== sessionId)
        }
      } catch (error: unknown) {
        const axiosError = error as ApiError
        this.error = axiosError.response?.data?.message || 'Failed to delete session'
      } finally {
        this.loading = false
      }
    },

    async resetSession(sessionId: string) {
      try {
        this.loading = true
        this.error = null

        await api.post(`/api/admin/sessions/${sessionId}/reset`)
        await this.fetchSessions() // Refresh the list
      } catch (error: unknown) {
        const axiosError = error as ApiError
        this.error = axiosError.response?.data?.message || 'Failed to reset session'
      } finally {
        this.loading = false
      }
    },

    async archiveSession(sessionId: string) {
      try {
        this.loading = true
        this.error = null

        await api.post(`/api/admin/sessions/${sessionId}/archive`)
        await this.fetchSessions() // Refresh the list
      } catch (error: unknown) {
        const axiosError = error as ApiError
        this.error = axiosError.response?.data?.message || 'Failed to archive session'
      } finally {
        this.loading = false
      }
    },

  async exportData(type: 'sessions' | 'all') {
      try {
        this.loading = true
        this.error = null

        const response = await api.get(`/api/admin/export/${type}`, {
          responseType: 'blob',
        })

        // Create download link
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute(
          'download',
          `stock-roulette-${type}-${new Date().toISOString().split('T')[0]}.csv`,
        )
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
      } catch (error: unknown) {
        const axiosError = error as ApiError
        this.error = axiosError.response?.data?.message || 'Failed to export data'
      } finally {
        this.loading = false
      }
    },

    setSessionFilters(filters: Partial<typeof this.sessionFilters>) {
      this.sessionFilters = { ...this.sessionFilters, ...filters }
    },

    clearError() {
      this.error = null
    },
  },
})
