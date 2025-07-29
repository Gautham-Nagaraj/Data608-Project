<template>
  <div class="game-container">
    <div class="game-content">
      <h2>Stock Roulette</h2>

      <div v-if="loading">Loading game data...</div>

      <div v-else-if="error" class="error">
        {{ error }}
      </div>

      <div v-else>
        <h3>📅 Game Month: {{ selectedDate.month }}/{{ selectedDate.year }}</h3>

        <!-- Player Name Input -->
        <div class="player-input-section">
          <label for="player-name" class="player-label">👤 Enter Your Name:</label>
          <input
            id="player-name"
            v-model="playerName"
            type="text"
            class="player-input"
            placeholder="Enter your name to start playing..."
            maxlength="50"
            @keyup.enter="startSession"
          />
          <div v-if="nameError" class="name-error">{{ nameError }}</div>
        </div>

        <div class="stocks-table">
          <div class="category-column popular-column">
            <div class="category-header">🌟 POPULAR</div>
            <div class="stock-content">
              <div
                v-for="stock in selectedStocks.filter((s) => s.type === 'Popular')"
                :key="stock.ticker"
                class="stock-card"
              >
                <div class="ticker">{{ stock.ticker }}</div>
                <div class="company-name">{{ stock.companyName }}</div>
              </div>
            </div>
          </div>

          <div class="category-column volatile-column">
            <div class="category-header">⚡ VOLATILE</div>
            <div class="stock-content">
              <div
                v-for="stock in selectedStocks.filter((s) => s.type === 'Volatile')"
                :key="stock.ticker"
                class="stock-card"
              >
                <div class="ticker">{{ stock.ticker }}</div>
                <div class="company-name">{{ stock.companyName }}</div>
              </div>
            </div>
          </div>

          <div class="category-column sector-column">
            <div class="category-header">🏢 SECTOR</div>
            <div class="stock-content">
              <div
                v-for="stock in selectedStocks.filter((s) => s.type === 'Sector')"
                :key="stock.ticker"
                class="stock-card"
              >
                <div class="ticker">{{ stock.ticker }}</div>
                <div class="company-name">{{ stock.companyName }}</div>
                <div v-if="stock.sector" class="sector">{{ stock.sector }}</div>
              </div>
            </div>
          </div>
        </div>

        <button @click="startSession" :disabled="!selectedStocks.length || !playerName.trim()">
          Start Game
        </button>

        <div v-if="sessionId" class="session-info">
          ✅ Session started: <strong>{{ sessionId }}</strong>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import { useSessionStore } from '@/stores/sessionStore'

const router = useRouter()
const store = useSessionStore()

const selectedDate = ref({ month: 0, year: 0 })
const selectedStocks = ref<
  { ticker: string; type: string; companyName?: string; sector?: string }[]
>([])
const sessionId = ref('')
const loading = ref(true)
const error = ref('')
const playerName = ref('')
const nameError = ref('')

onMounted(async () => {
  try {
    console.log('Starting to load game data...')

    // 1. Get random month and year from backend
    console.log('Calling /api/stocks/eligible_dates/roulette...')
    const dateRes = await api.get('/api/stocks/eligible_dates/roulette')
    console.log('Date response:', dateRes.data)
    selectedDate.value = dateRes.data

    // 2. Get 3 random stocks for that month/year
    const params = { month: selectedDate.value.month, year: selectedDate.value.year }
    console.log('Calling /api/selections/roulette with params:', params)
    const stockRes = await api.get('/api/selections/roulette', {
      params: params,
    })
    console.log('Stock response:', stockRes.data)
    console.log('Stock response type:', typeof stockRes.data)

    // Transform the API response into the expected format
    const responseData = stockRes.data
    const stocksWithoutDetails = [
      { ticker: responseData.popular_symbol, type: 'Popular' },
      { ticker: responseData.volatile_symbol, type: 'Volatile' },
      { ticker: responseData.sector_symbol, type: 'Sector' },
    ]

    // 3. Fetch stock details for each ticker
    console.log('Fetching stock details...')
    const stocksWithDetails = await Promise.all(
      stocksWithoutDetails.map(async (stock) => {
        try {
          const detailsRes = await api.get(`/api/stocks/${stock.ticker}`)
          console.log(`Details for ${stock.ticker}:`, detailsRes.data)
          return {
            ...stock,
            companyName: detailsRes.data.company_name || detailsRes.data.name || stock.ticker,
            // Only include sector for sector stocks (not volatile)
            sector: stock.type === 'Sector' ? detailsRes.data.sector || null : null,
          }
        } catch (err) {
          console.warn(`Failed to fetch details for ${stock.ticker}:`, err)
          return {
            ...stock,
            companyName: stock.ticker, // Fallback to ticker if API call fails
            sector: null,
          }
        }
      }),
    )

    selectedStocks.value = stocksWithDetails

    console.log('Game data loaded successfully!')
    console.log('selectedStocks after transformation:', selectedStocks.value)
  } catch (err) {
    console.error('Failed to load game data:', err)
    error.value = `Failed to load game data: ${err}`
  } finally {
    loading.value = false
  }
})

async function startSession() {
  // Clear any previous name error
  nameError.value = ''

  // Validate player name
  if (!playerName.value.trim()) {
    nameError.value = 'Please enter your name to start the game'
    return
  }

  if (playerName.value.trim().length < 2) {
    nameError.value = 'Name must be at least 2 characters long'
    return
  }

  try {
    // Step 1: Create player
    let player_res
    try {
      player_res = await api.post('api/player', {
        nickname: playerName.value.trim(),
      })
      console.log('Player created successfully:', player_res.data)
    } catch (err) {
      console.error('Failed to create player:', err)
      nameError.value = 'Failed to create player. Please try again.'
      return
    }

    const tickers = selectedStocks.value.map((s) => s.ticker)

    // Step 2: Create session
    let res
    try {
      res = await api.post('/api/sessions', {
        started_at: new Date().toISOString(),
        balance: 500, // Default balance for the session
        player_id: player_res.data.id, // Use player ID from the player creation response
        status: 'active', // Required status field
      })
      console.log('Session created successfully:', res.data)
    } catch (err) {
      console.error('Failed to create session:', err)
      nameError.value = 'Failed to start game session. Please try again.'
      return
    }

    // Step 3: Create selections
    let selections_res
    try {
      selections_res = await api.post('/api/selections/' + res.data.session_id, {
        player_id: player_res.data.id,
        popular_symbol: selectedStocks.value.find((s) => s.type === 'Popular')?.ticker,
        volatile_symbol: selectedStocks.value.find((s) => s.type === 'Volatile')?.ticker,
        sector_symbol: selectedStocks.value.find((s) => s.type === 'Sector')?.ticker,
        month: selectedDate.value.month,
        year: selectedDate.value.year,
      })
      console.log('Selections created successfully:', selections_res.data)
    } catch (err) {
      console.error('Failed to create selections:', err)
      nameError.value = 'Failed to save stock selections. Please try again.'
      return
    }

    // If all API calls succeed, proceed with navigation
    sessionId.value = res.data.session_id
    store.setSessionId(sessionId.value)
    store.setSelectedStocks(tickers)

    // Store the selected date, stock details, and player name for the active game
    store.setGameData({
      date: selectedDate.value,
      stockDetails: selectedStocks.value,
      playerName: playerName.value.trim(),
    })

    // Navigate to the active game page
    router.push('/active-game')
  } catch (err) {
    // Catch any unexpected errors
    console.error('Unexpected error during session start:', err)
    nameError.value = 'An unexpected error occurred. Please try again.'
  }
}
</script>

<style scoped>
.game-container {
  min-height: 100vh;
  width: 100%;
  margin: 0;
  padding: 2rem;
  text-align: center;
  font-family: 'Orbitron', 'Courier New', 'Monaco', monospace;
  background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
  color: #ffffff;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.game-content {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
}

.game-container h2 {
  font-size: 2.5rem;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 3px;
  background: linear-gradient(45deg, #00f5ff, #ff00f5);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 1rem;
  text-shadow: 0 0 20px rgba(0, 245, 255, 0.3);
}

.game-container h3 {
  color: #00f5ff;
  font-weight: 700;
  font-size: 1.3rem;
  margin-bottom: 2rem;
  text-transform: uppercase;
  letter-spacing: 2px;
}

/* Player Input Section */
.player-input-section {
  margin: 2rem 0;
  text-align: center;
}

.player-label {
  display: block;
  color: #00f5ff;
  font-weight: 700;
  font-size: 1.1rem;
  margin-bottom: 1rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  text-shadow: 0 0 10px rgba(0, 245, 255, 0.3);
}

.player-input {
  width: 100%;
  max-width: 400px;
  padding: 1rem 1.5rem;
  font-size: 1rem;
  font-family: 'Orbitron', 'Courier New', 'Monaco', monospace;
  background: rgba(255, 255, 255, 0.1);
  border: 2px solid rgba(0, 245, 255, 0.3);
  border-radius: 10px;
  color: #ffffff;
  text-align: center;
  transition: all 0.3s ease;
  margin-bottom: 0.5rem;
}

.player-input:focus {
  outline: none;
  border-color: #00f5ff;
  background: rgba(255, 255, 255, 0.15);
  box-shadow: 0 0 20px rgba(0, 245, 255, 0.3);
  transform: scale(1.02);
}

.player-input::placeholder {
  color: rgba(255, 255, 255, 0.5);
  font-style: italic;
}

.name-error {
  color: #ff6b6b;
  font-size: 0.9rem;
  font-weight: 600;
  margin-top: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  background: rgba(255, 107, 107, 0.1);
  padding: 0.5rem 1rem;
  border-radius: 5px;
  border: 1px solid rgba(255, 107, 107, 0.3);
  display: inline-block;
}

/* Gaming-style table layout */
.stocks-table {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 1.5rem;
  margin: 2rem 0;
  perspective: 1000px;
}

.category-column {
  background: rgba(255, 255, 255, 0.05);
  border: 2px solid;
  border-radius: 15px;
  overflow: hidden;
  transition: all 0.3s ease;
  transform-style: preserve-3d;
}

.category-column:hover {
  transform: rotateY(5deg) translateZ(10px);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
}

.popular-column {
  border-color: #ffd700;
  background: linear-gradient(145deg, rgba(255, 215, 0, 0.1), rgba(255, 140, 0, 0.05));
}

.volatile-column {
  border-color: #ff6b6b;
  background: linear-gradient(145deg, rgba(255, 107, 107, 0.1), rgba(255, 69, 58, 0.05));
}

.sector-column {
  border-color: #4ecdc4;
  background: linear-gradient(145deg, rgba(78, 205, 196, 0.1), rgba(0, 245, 255, 0.05));
}

.category-header {
  padding: 1rem;
  font-size: 1.2rem;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 2px;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.popular-column .category-header {
  background: linear-gradient(135deg, #ffd700, #ffb347);
  color: #000;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.volatile-column .category-header {
  background: linear-gradient(135deg, #ff6b6b, #ff4757);
  color: #fff;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

.sector-column .category-header {
  background: linear-gradient(135deg, #4ecdc4, #00f5ff);
  color: #000;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.category-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.5s;
}

.category-column:hover .category-header::before {
  left: 100%;
}

.stock-content {
  padding: 1.5rem;
  min-height: 120px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.stock-card {
  background: rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 1rem;
  margin-bottom: 0.5rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.stock-card:hover {
  background: rgba(255, 255, 255, 0.15);
  transform: translateY(-3px);
  border-color: rgba(255, 255, 255, 0.3);
}

.stock-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.6), transparent);
  transform: translateX(-100%);
  transition: transform 0.6s ease;
}

.stock-card:hover::before {
  transform: translateX(100%);
}

.ticker {
  font-weight: 900;
  font-size: 1.2rem;
  color: #00f5ff;
  letter-spacing: 1px;
  text-transform: uppercase;
  margin-bottom: 0.3rem;
  text-shadow: 0 0 10px rgba(0, 245, 255, 0.5);
}

.company-name {
  font-size: 0.85rem;
  color: #cccccc;
  line-height: 1.3;
  margin-bottom: 0.5rem;
  font-weight: 400;
}

.sector {
  font-size: 0.75rem;
  color: #4ecdc4;
  background: rgba(78, 205, 196, 0.2);
  padding: 0.3rem 0.6rem;
  border-radius: 15px;
  border: 1px solid rgba(78, 205, 196, 0.4);
  display: inline-block;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Gaming button style */
button {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
  padding: 1rem 2rem;
  font-size: 1.1rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: 'Orbitron', 'Courier New', monospace;
  margin: 2rem 0;
  position: relative;
  overflow: hidden;
}

button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

button:hover:not(:disabled)::before {
  left: 100%;
}

.session-info {
  margin-top: 2rem;
  font-weight: 700;
  color: #00f5ff;
  background: rgba(0, 245, 255, 0.1);
  padding: 1rem;
  border-radius: 10px;
  border: 1px solid rgba(0, 245, 255, 0.3);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.error {
  color: #ff6b6b;
  background: rgba(255, 107, 107, 0.1);
  padding: 1rem;
  border: 2px solid #ff6b6b;
  border-radius: 10px;
  margin: 1rem 0;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* Responsive design */
@media (max-width: 768px) {
  .stocks-table {
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .game-container {
    padding: 1rem;
    min-height: 100vh;
  }

  .game-container h2 {
    font-size: 1.8rem;
  }
}
</style>
