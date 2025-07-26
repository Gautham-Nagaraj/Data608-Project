<template>
  <div class="game-container">
    <h2>Stock Roulette</h2>

    <div v-if="loading">Loading game data...</div>

    <div v-else>
      <h3>📅 Game Month: {{ selectedDate.month }}/{{ selectedDate.year }}</h3>

      <ul>
        <li v-for="stock in selectedStocks" :key="stock.ticker">
          {{ stock.ticker }} ({{ stock.type }})
        </li>
      </ul>

      <button @click="startSession" :disabled="!selectedStocks.length">Start Game</button>

      <div v-if="sessionId" class="session-info">
        ✅ Session started: <strong>{{ sessionId }}</strong>
      </div>

      <!-- Live prices -->
      <div v-if="Object.keys(prices).length > 0" class="live-prices">
        <h3>📈 Live Prices</h3>
        <ul>
          <li v-for="(price, ticker) in prices" :key="ticker">
            {{ ticker }}: ${{ price.toFixed(2) }}
          </li>
        </ul>
      </div>

      <!-- Streamlit iframe -->
      <iframe
        v-if="sessionId"
        :src="`http://localhost:8501/?session_id=${sessionId}`"
        width="100%"
        height="600"
        style="border:none; margin-top: 2rem;"
      ></iframe>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import { useSessionStore } from '@/stores/sessionStore'

const store = useSessionStore()

const selectedDate = ref({ month: 0, year: 0 })
const selectedStocks = ref<{ ticker: string; type: string }[]>([])
const sessionId = ref('')
const loading = ref(true)

const prices = ref<Record<string, number>>({})
let socket: WebSocket | null = null

onMounted(async () => {
  try {
    // 1. Get eligible dates
    const res = await api.get('/api/stocks/eligible_dates')
    const dates = res.data

    // 2. Pick a random date
    const randomIndex = Math.floor(Math.random() * dates.length)
    selectedDate.value = dates[randomIndex]

    // 3. Get 3 stocks
    const stockRes = await api.get('/api/selections/roulette', {
      params: selectedDate.value,
    })
    selectedStocks.value = stockRes.data
  } catch (err) {
    console.error('Failed to load game data', err)
  } finally {
    loading.value = false
  }
})

async function startSession() {
  const tickers = selectedStocks.value.map((s) => s.ticker)

  const res = await api.post('/start-session', {
    tickers,
  })

  sessionId.value = res.data.session_id
  store.setSessionId(sessionId.value)
  store.setSelectedStocks(tickers)

  connectWebSocket(sessionId.value)
}

function connectWebSocket(sessionId: string) {
  socket = new WebSocket(`ws://localhost:8000/ws/prices/${sessionId}`)

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data)
    prices.value[data.ticker] = data.price
  }

  socket.onclose = () => {
    console.log('WebSocket closed')
  }
}
</script>

<style scoped>
.game-container {
  max-width: 600px;
  margin: 0 auto;
  text-align: center;
}
.session-info {
  margin-top: 1rem;
  font-weight: bold;
}
</style>
