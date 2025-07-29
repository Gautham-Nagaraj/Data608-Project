<template>
  <div class="leaderboard-view">
    <div class="page-header">
      <h2>Leaderboard</h2>
      <div class="header-actions">
        <div class="auto-refresh-info">
          <span class="refresh-counter"> Next refresh in: {{ countdown }}s </span>
          <button
            @click="toggleAutoRefresh"
            class="auto-refresh-btn"
            :class="{ active: isAutoRefresh }"
          >
            {{ isAutoRefresh ? 'Stop Auto-refresh' : 'Start Auto-refresh' }}
          </button>
        </div>
        <button @click="refreshLeaderboard" class="refresh-btn" :disabled="loading">
          {{ loading ? 'Loading...' : 'Refresh' }}
        </button>
        <button @click="downloadCSV" class="download-btn" :disabled="loading">Download CSV</button>
      </div>
    </div>

    <!-- Stats Summary -->
    <div class="stats-summary">
      <div class="stat-card">
        <h3>Total Players</h3>
        <div class="stat-value">{{ leaderboard.length }}</div>
      </div>
      <div class="stat-card">
        <h3>Highest Score</h3>
        <div class="stat-value">{{ highestScore.toLocaleString() }}</div>
      </div>
      <div class="stat-card">
        <h3>Average Score</h3>
        <div class="stat-value">{{ averageScore.toLocaleString() }}</div>
      </div>
    </div>

    <!-- Sort Controls -->
    <div class="sort-controls">
      <label for="sort-by">Sort by:</label>
      <select id="sort-by" v-model="sortBy">
        <option value="total_score">Total Score</option>
        <option value="total_profit">Total Profit</option>
      </select>

      <button @click="toggleSortOrder" class="sort-order-btn">
        {{ sortOrder === 'desc' ? '↓ Descending' : '↑ Ascending' }}
      </button>
    </div>

    <!-- Leaderboard Table -->
    <div class="table-container">
      <div v-if="sortedLeaderboard.length === 0" class="no-data">
        <p>No leaderboard data available</p>
      </div>

      <table v-else class="leaderboard-table">
        <thead>
          <tr>
            <th class="rank-col">Rank</th>
            <th>Player Name</th>
            <th class="numeric-col">Total Score</th>
            <th class="numeric-col">Total Profit</th>
            <th class="numeric-col">Total Trades</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(player, index) in sortedLeaderboard"
            :key="player.nickname"
            :class="{ 'top-player': index < 3 }"
          >
            <td class="rank-col">
              <div class="rank-badge" :class="getRankClass(index)">
                {{ index + 1 }}
              </div>
            </td>
            <td class="player-name">
              <div class="player-info">
                <span class="name">{{ player.nickname }}</span>
                <div class="medals" v-if="index < 3">
                  <span class="medal" :class="getMedalClass(index)">
                    {{ getMedalEmoji(index) }}
                  </span>
                </div>
              </div>
            </td>
            <td class="numeric-col">
              <span class="score-value">
                {{ player.total_score.toLocaleString() }}
              </span>
            </td>
            <td class="numeric-col">
              <span class="total-profit"> ${{ player.total_profit.toLocaleString() }} </span>
            </td>
            <td class="numeric-col">
              <span class="total-trades"> {{ player.total_trades.toLocaleString() }} </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Performance Chart -->
    <div class="chart-section">
      <h3>Score Distribution</h3>
      <div class="chart-container">
        <div class="score-chart">
          <div
            v-for="(player, index) in sortedLeaderboard.slice(0, 10)"
            :key="player.nickname"
            class="score-bar"
          >
            <div class="bar-container">
              <div
                class="bar"
                :style="{ width: getBarWidth(player.total_score) + '%' }"
                :class="getBarClass(index)"
              ></div>
            </div>
            <div class="bar-label">
              <span class="player-name">{{ player.nickname }}</span>
              <span class="score">{{ player.total_score.toLocaleString() }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { useAdminStore } from '@/stores/adminStore'

const adminStore = useAdminStore()

const sortBy = ref<'total_score' | 'total_profit'>('total_score')
const sortOrder = ref<'asc' | 'desc'>('desc')

// Auto-refresh functionality
const isAutoRefresh = ref(true)
const countdown = ref(10)
let refreshInterval: ReturnType<typeof setInterval> | null = null
let countdownInterval: ReturnType<typeof setInterval> | null = null

const loading = computed(() => adminStore.loading)
const leaderboard = computed(() => adminStore.leaderboard)

const sortedLeaderboard = computed(() => {
  const sorted = [...leaderboard.value].sort((a, b) => {
    const aValue = a[sortBy.value]
    const bValue = b[sortBy.value]

    if (sortOrder.value === 'desc') {
      return bValue - aValue
    } else {
      return aValue - bValue
    }
  })

  return sorted
})

const highestScore = computed(() => {
  return leaderboard.value.length > 0 ? Math.max(...leaderboard.value.map((p) => p.total_score)) : 0
})

const averageScore = computed(() => {
  if (leaderboard.value.length === 0) return 0
  const totalScore = leaderboard.value.reduce((sum, player) => sum + player.total_score, 0)
  return Math.round(totalScore / leaderboard.value.length)
})

onMounted(async () => {
  await adminStore.fetchLeaderboard()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})

const startAutoRefresh = () => {
  if (refreshInterval) return

  // Start countdown
  countdownInterval = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      countdown.value = 10
    }
  }, 1000)

  // Refresh leaderboard every 10 seconds
  refreshInterval = setInterval(async () => {
    await adminStore.fetchLeaderboard()
    countdown.value = 10
  }, 10000)
}

const stopAutoRefresh = () => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
  if (countdownInterval) {
    clearInterval(countdownInterval)
    countdownInterval = null
  }
}

const toggleAutoRefresh = () => {
  isAutoRefresh.value = !isAutoRefresh.value

  if (isAutoRefresh.value) {
    countdown.value = 10
    startAutoRefresh()
  } else {
    stopAutoRefresh()
    countdown.value = 0
  }
}

const refreshLeaderboard = async () => {
  await adminStore.fetchLeaderboard()
}

const downloadCSV = async () => {
  await adminStore.exportData('sessions')
}

const toggleSortOrder = () => {
  sortOrder.value = sortOrder.value === 'desc' ? 'asc' : 'desc'
}

const getRankClass = (index: number) => {
  if (index === 0) return 'gold'
  if (index === 1) return 'silver'
  if (index === 2) return 'bronze'
  return ''
}

const getMedalClass = (index: number) => {
  if (index === 0) return 'gold'
  if (index === 1) return 'silver'
  if (index === 2) return 'bronze'
  return ''
}

const getMedalEmoji = (index: number) => {
  if (index === 0) return '🥇'
  if (index === 1) return '🥈'
  if (index === 2) return '🥉'
  return ''
}

const getBarWidth = (score: number) => {
  if (highestScore.value === 0) return 0
  return (score / highestScore.value) * 100
}

const getBarClass = (index: number) => {
  if (index === 0) return 'bar-gold'
  if (index === 1) return 'bar-silver'
  if (index === 2) return 'bar-bronze'
  return 'bar-default'
}
</script>

<style scoped>
.leaderboard-view {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #dee2e6;
}

.page-header h2 {
  margin: 0;
  color: #333;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.auto-refresh-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.refresh-counter {
  font-size: 0.85rem;
  color: #6c757d;
  font-weight: 500;
  min-width: 120px;
  text-align: center;
}

.auto-refresh-btn {
  padding: 0.4rem 0.8rem;
  border: 2px solid #6c757d;
  border-radius: 6px;
  background: white;
  color: #6c757d;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
  font-size: 0.85rem;
}

.auto-refresh-btn:hover {
  background-color: #6c757d;
  color: white;
}

.auto-refresh-btn.active {
  background-color: #28a745;
  color: white;
  border-color: #28a745;
}

.auto-refresh-btn.active:hover {
  background-color: #218838;
  border-color: #218838;
}

.refresh-btn,
.download-btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
  font-weight: 500;
}

.refresh-btn {
  background-color: #007bff;
  color: white;
}

.refresh-btn:hover:not(:disabled) {
  background-color: #0056b3;
}

.download-btn {
  background-color: #28a745;
  color: white;
}

.download-btn:hover:not(:disabled) {
  background-color: #218838;
}

.refresh-btn:disabled,
.download-btn:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

.stats-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.stat-card h3 {
  margin: 0 0 0.5rem 0;
  font-size: 0.9rem;
  opacity: 0.9;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
  margin: 0;
}

.sort-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 6px;
}

.sort-controls label {
  font-weight: 500;
  color: #333;
}

.sort-controls select {
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  background: white;
}

.sort-order-btn {
  padding: 0.5rem 1rem;
  background-color: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
}

.sort-order-btn:hover {
  background-color: #545b62;
}

.table-container {
  overflow-x: auto;
  margin-bottom: 2rem;
}

.no-data {
  text-align: center;
  padding: 3rem;
  color: #6c757d;
}

.leaderboard-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 700px;
}

.leaderboard-table th,
.leaderboard-table td {
  padding: 1rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid #dee2e6;
  vertical-align: middle;
}

.leaderboard-table th {
  background-color: #f8f9fa;
  font-weight: 600;
  color: #495057;
  position: sticky;
  top: 0;
}

.rank-col,
.numeric-col {
  text-align: center;
}

.top-player {
  background-color: #fff9e6;
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  font-weight: bold;
  color: white;
}

.rank-badge.gold {
  background: linear-gradient(135deg, #ffd700, #ffed4a);
  color: #333;
}

.rank-badge.silver {
  background: linear-gradient(135deg, #c0c0c0, #e5e5e5);
  color: #333;
}

.rank-badge.bronze {
  background: linear-gradient(135deg, #cd7f32, #daa520);
  color: white;
}

.rank-badge:not(.gold):not(.silver):not(.bronze) {
  background-color: #6c757d;
}

.player-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.player-info .name {
  font-weight: 500;
  font-size: 1.1rem;
}

.medal {
  font-size: 1.2rem;
}

.score-value {
  font-weight: 600;
  color: #28a745;
  font-size: 1.1rem;
}

.total-profit,
.total-trades {
  font-weight: 500;
  color: #17a2b8;
}

.session-count {
  background-color: #e9ecef;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.9rem;
  font-weight: 500;
}

.chart-section {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid #dee2e6;
}

.chart-section h3 {
  margin-bottom: 1rem;
  color: #333;
}

.score-chart {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.score-bar {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.bar-container {
  flex: 1;
  height: 24px;
  background-color: #e9ecef;
  border-radius: 12px;
  overflow: hidden;
  position: relative;
}

.bar {
  height: 100%;
  border-radius: 12px;
  transition: width 0.5s ease;
}

.bar-gold {
  background: linear-gradient(90deg, #ffd700, #ffed4a);
}

.bar-silver {
  background: linear-gradient(90deg, #c0c0c0, #e5e5e5);
}

.bar-bronze {
  background: linear-gradient(90deg, #cd7f32, #daa520);
}

.bar-default {
  background: linear-gradient(90deg, #007bff, #0056b3);
}

.bar-label {
  display: flex;
  flex-direction: column;
  min-width: 120px;
  font-size: 0.9rem;
}

.bar-label .player-name {
  font-weight: 500;
}

.bar-label .score {
  color: #6c757d;
  font-size: 0.8rem;
}
</style>
