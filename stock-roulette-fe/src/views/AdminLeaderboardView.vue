<template>
  <div class="leaderboard-view">
    <div class="page-header">
      <h2>Leaderboard - Top 10 Players</h2>
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
      <div v-if="top10Leaderboard.length === 0" class="no-data">
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
            v-for="player in top10Leaderboard"
            :key="player.nickname"
            :class="{ 'top-player': player.rank <= 3 }"
          >
            <td class="rank-col">
              <div class="rank-badge" :class="getRankClass(player.rank - 1)">
                {{ player.rank }}
              </div>
            </td>
            <td class="player-name">
              <div class="player-info">
                <span class="name">{{ player.nickname }}</span>
                <div class="medals" v-if="player.rank <= 3">
                  <span class="medal" :class="getMedalClass(player.rank - 1)">
                    {{ getMedalEmoji(player.rank - 1) }}
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

      <div class="table-footer" v-if="leaderboard.length > 10">
        <p class="total-players-note">
          Showing top 10 of {{ leaderboard.length.toLocaleString() }} total players
        </p>
      </div>
    </div>

    <!-- Performance Chart -->
    <div class="chart-section">
      <h3>Score Distribution</h3>
      <div class="histogram-controls">
        <div class="bins-control">
          <label for="bins-slider">Number of Bins: {{ histogramBins }}</label>
          <input
            id="bins-slider"
            v-model="histogramBins"
            type="range"
            :min="5"
            :max="50"
            step="1"
            class="bins-slider"
            @input="updateHistogram"
          />
          <div class="bins-range">
            <span>5</span>
            <span>50</span>
          </div>
        </div>
        <button @click="resetBinsToOptimal" class="reset-bins-btn">
          Reset to Optimal ({{ optimalBins }})
        </button>
      </div>
      <div class="chart-container">
        <div id="score-histogram" class="plotly-chart"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted, nextTick, watch } from 'vue'
import { useAdminStore } from '@/stores/adminStore'
import Plotly from 'plotly.js-dist-min'

const adminStore = useAdminStore()

const sortBy = ref<'total_score' | 'total_profit'>('total_score')
const sortOrder = ref<'asc' | 'desc'>('desc')

// Histogram controls
const histogramBins = ref(20)
const defaultBins = 20

// Auto-refresh functionality
const isAutoRefresh = ref(true)
const countdown = ref(10)
let refreshInterval: ReturnType<typeof setInterval> | null = null
let countdownInterval: ReturnType<typeof setInterval> | null = null

const loading = computed(() => adminStore.loading)
const leaderboard = computed(() => adminStore.leaderboard)

// Calculate optimal bins based on data
const optimalBins = computed(() => {
  if (leaderboard.value.length === 0) return defaultBins
  return Math.min(Math.ceil(Math.sqrt(leaderboard.value.length)), 20)
})

const sortedLeaderboard = computed(() => {
  // If we have rank data from backend, sort by rank first to maintain proper order
  const sorted = [...leaderboard.value].sort((a, b) => {
    // Sort by rank first (ascending order for rank)
    return a.rank - b.rank
  })

  // If user wants to sort by other criteria, apply that sorting
  if (sortBy.value !== 'total_score' || sortOrder.value !== 'desc') {
    const sortedByUser = [...sorted].sort((a, b) => {
      const aValue = a[sortBy.value]
      const bValue = b[sortBy.value]

      if (sortOrder.value === 'desc') {
        return bValue - aValue
      } else {
        return aValue - bValue
      }
    })

    return sortedByUser
  }

  return sorted
})

// Top 10 players for table display
const top10Leaderboard = computed(() => {
  return sortedLeaderboard.value.slice(0, 10)
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
  // Initialize bins to optimal value
  histogramBins.value = optimalBins.value
  startAutoRefresh()
  await createScoreHistogram()
})

onUnmounted(() => {
  stopAutoRefresh()
})

// Watch for leaderboard changes to update the histogram
watch(leaderboard, async () => {
  await createScoreHistogram()
}, { deep: true })

const createScoreHistogram = async () => {
  await nextTick()

  if (leaderboard.value.length === 0) return

  const scores = leaderboard.value.map(player => player.total_score)

  // Calculate statistics for the distribution curve
  const mean = scores.reduce((sum, score) => sum + score, 0) / scores.length
  const variance = scores.reduce((sum, score) => sum + Math.pow(score - mean, 2), 0) / scores.length
  const stdDev = Math.sqrt(variance)

  // Generate normal distribution curve points
  const minScore = Math.min(...scores)
  const maxScore = Math.max(...scores)
  const range = maxScore - minScore
  const curvePoints = 100
  const xCurve = []
  const yCurve = []

  for (let i = 0; i <= curvePoints; i++) {
    const x = minScore + (range * i / curvePoints)
    const y = (1 / (stdDev * Math.sqrt(2 * Math.PI))) *
              Math.exp(-0.5 * Math.pow((x - mean) / stdDev, 2))
    xCurve.push(x)
    yCurve.push(y)
  }

  // Scale the curve to match histogram frequency
  const maxCurveY = Math.max(...yCurve)
  const scaleFactor = (scores.length / histogramBins.value) / maxCurveY
  const scaledYCurve = yCurve.map(y => y * scaleFactor)

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const histogramTrace: any = {
    x: scores,
    type: 'histogram',
    nbinsx: histogramBins.value,
    name: 'Score Distribution',
    marker: {
      color: 'rgba(0, 123, 255, 0.6)',
      line: {
        color: 'rgba(0, 123, 255, 1)',
        width: 1
      }
    },
    opacity: 0.7
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const curveTrace: any = {
    x: xCurve,
    y: scaledYCurve,
    type: 'scatter',
    mode: 'lines',
    name: 'Normal Distribution',
    line: {
      color: 'rgba(255, 99, 132, 1)',
      width: 3
    }
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const layout: any = {
    title: {
      text: 'Player Score Distribution with Normal Curve',
      font: { size: 16, color: '#333' }
    },
    xaxis: {
      title: { text: 'Score' },
      gridcolor: 'rgba(0,0,0,0.1)',
      tickformat: ',d'
    },
    yaxis: {
      title: { text: 'Frequency' },
      gridcolor: 'rgba(0,0,0,0.1)'
    },
    plot_bgcolor: 'rgba(0,0,0,0)',
    paper_bgcolor: 'rgba(0,0,0,0)',
    font: {
      family: 'system-ui, -apple-system, sans-serif',
      size: 12,
      color: '#333'
    },
    margin: {
      l: 60,
      r: 30,
      t: 60,
      b: 60
    },
    legend: {
      x: 0.7,
      y: 0.9,
      bgcolor: 'rgba(255,255,255,0.8)',
      bordercolor: 'rgba(0,0,0,0.1)',
      borderwidth: 1
    },
    hovermode: 'closest'
  }

  const config = {
    responsive: true,
    displayModeBar: false
  }

  const data = [histogramTrace, curveTrace]

  try {
    await Plotly.newPlot('score-histogram', data, layout, config)
  } catch (error) {
    console.error('Error creating histogram:', error)
  }
}

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

// Histogram control functions
const updateHistogram = async () => {
  await createScoreHistogram()
}

const resetBinsToOptimal = async () => {
  histogramBins.value = optimalBins.value
  await createScoreHistogram()
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

.table-footer {
  margin-top: 1rem;
  padding: 0.75rem;
  background-color: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #dee2e6;
}

.total-players-note {
  margin: 0;
  text-align: center;
  color: #6c757d;
  font-size: 0.9rem;
  font-style: italic;
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

.chart-container {
  background: white;
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.plotly-chart {
  min-height: 400px;
  width: 100%;
}

/* Histogram controls styling */
.histogram-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #dee2e6;
}

.bins-control {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
}

.bins-control label {
  font-weight: 500;
  color: #333;
  font-size: 0.9rem;
}

.bins-slider {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #ddd;
  outline: none;
  opacity: 0.7;
  transition: opacity 0.2s;
  cursor: pointer;
}

.bins-slider:hover {
  opacity: 1;
}

.bins-slider::-webkit-slider-thumb {
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #007bff;
  cursor: pointer;
  transition: background 0.2s;
}

.bins-slider::-webkit-slider-thumb:hover {
  background: #0056b3;
}

.bins-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #007bff;
  cursor: pointer;
  border: none;
}

.bins-range {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: #6c757d;
  margin-top: 0.25rem;
}

.reset-bins-btn {
  padding: 0.5rem 1rem;
  background-color: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  white-space: nowrap;
  transition: background-color 0.2s;
}

.reset-bins-btn:hover {
  background-color: #545b62;
}

@media (max-width: 768px) {
  .histogram-controls {
    flex-direction: column;
    align-items: stretch;
  }

  .bins-control {
    margin-bottom: 0.5rem;
  }
}
</style>
