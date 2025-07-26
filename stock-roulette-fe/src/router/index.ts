import { createRouter, createWebHistory } from 'vue-router'
import GameView from '@/views/GameView.vue'
import ResultsView from '@/views/ResultsView.vue'
import SummaryView from '@/views/SummaryView.vue'

const routes = [
  // { path: '/', name: 'Home', component: HomeView },
  { path: '/', name: 'Game', component: GameView },
  { path: '/results', name: 'Results', component: ResultsView },
  { path: '/summary', name: 'Summary', component: SummaryView }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

export default router
