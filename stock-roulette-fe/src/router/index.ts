import { createRouter, createWebHistory } from 'vue-router'
import GameView from '@/views/GameView.vue'
import ActiveGameView from '@/views/ActiveGameView.vue'
import ResultsView from '@/views/ResultsView.vue'
import SummaryView from '@/views/SummaryView.vue'
import AdminLoginView from '@/views/AdminLoginView.vue'
import AdminDashboardView from '@/views/AdminDashboardView.vue'
import AdminSessionsView from '@/views/AdminSessionsView.vue'
import AdminLeaderboardView from '@/views/AdminLeaderboardView.vue'

import { useAdminStore } from '@/stores/adminStore'

const routes = [
  // Player routes
  { path: '/', name: 'Game', component: GameView },
  { path: '/active-game', name: 'ActiveGame', component: ActiveGameView },
  { path: '/results', name: 'Results', component: ResultsView },
  { path: '/summary', name: 'Summary', component: SummaryView },

  // Admin routes
  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: AdminLoginView,
  },
  {
    path: '/admin',
    component: AdminDashboardView,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/admin/sessions',
      },
      {
        path: 'dashboard',
        redirect: '/admin/sessions',
      },
      {
        path: 'sessions',
        name: 'AdminSessions',
        component: AdminSessionsView,
      },
      {
        path: 'leaderboard',
        name: 'AdminLeaderboard',
        component: AdminLeaderboardView,
      },
      {

      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// Navigation guard for admin routes
router.beforeEach((to) => {
  if (to.meta.requiresAuth) {
    const adminStore = useAdminStore()
    adminStore.checkAuth()

    if (!adminStore.isAuthenticated) {
      return '/admin/login'
    }
  }
})

export default router
