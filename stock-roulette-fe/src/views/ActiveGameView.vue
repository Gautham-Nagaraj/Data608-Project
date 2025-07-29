<template>
  <div class="active-game-container">
    <h2>🎮 Stock Roulette - Live Game</h2>

    <div class="game-info">
      <div v-if="playerName" class="player-info">
        <span>👤 {{ playerName }}</span>
      </div>
      <div class="session-info">
        <span>Session: {{ sessionId }}</span>
      </div>
      <div class="date-info">
        <span>{{ currentDate || selectedDate }}</span>
      </div>
      <div class="cash-info">
        <span>💰 Cash: ${{ playerCash.toFixed(2) }}</span>
      </div>
      <div class="portfolio-info">
        <span>📊 Portfolio: ${{ getPortfolioValue().toFixed(2) }}</span>
      </div>
      <div class="connection-info">
        <span :class="connectionStatus.class">{{ connectionStatus.text }}</span>
      </div>
    </div>

    <!-- Debug Panel (only in development) -->
    <div v-if="showDebugPanel" class="debug-panel">
      <h4>🔧 Debug Info</h4>
      <div class="debug-item"><strong>WebSocket State:</strong> {{ getWebSocketState() }}</div>
      <div class="debug-item">
        <strong>Price Data Points:</strong>
        <ul>
          <li v-for="stock in stocks" :key="stock.ticker">
            {{ stock.ticker }}: {{ priceHistory[stock.ticker]?.length || 0 }} points (Latest: ${{
              getCurrentPrice(stock.ticker)
            }}) {{ getPriceChangeText(stock.ticker) }}
          </li>
        </ul>
      </div>
      <div class="debug-item"><strong>Chart Update Key:</strong> {{ chartDataKey }}</div>
      <div class="debug-item">
        <strong>Mock Data Running:</strong> {{ isMockDataRunning ? 'Yes' : 'No' }}
      </div>
      <button @click="toggleDebugPanel" class="debug-toggle">Hide Debug</button>
    </div>

    <div v-else class="debug-toggle-container">
      <button @click="toggleDebugPanel" class="debug-toggle">Show Debug</button>
    </div>

    <div class="charts-container">
      <div
        v-for="(stock, index) in stocks"
        :key="stock.ticker"
        class="chart-card"
        :class="stock.type.toLowerCase() + '-card'"
      >
        <div class="chart-header">
          <h3>{{ stock.type.toUpperCase() }} - {{ stock.ticker }}</h3>
          <div class="company-name">{{ stock.companyName || stock.ticker }}</div>
          <div class="current-price">${{ getCurrentPrice(stock.ticker) }}</div>
          <div class="price-change" :class="getPriceChangeClass(stock.ticker)">
            {{ getPriceChangeText(stock.ticker) }}
          </div>
          <div class="stock-owned">Owned: {{ stockOwned[stock.ticker] || 0 }} shares</div>
        </div>
        <div class="chart-wrapper">
          <div :id="`chart-${index}`" class="plotly-chart" :key="chartDataKey"></div>
        </div>
        <div class="trading-controls">
          <div class="trade-input-group">
            <label>Quantity:</label>
            <input
              type="number"
              :id="`quantity-${stock.ticker}`"
              min="1"
              :max="getMaxBuyQuantity(stock.ticker)"
              placeholder="1"
              class="quantity-input"
            />
          </div>
          <div class="trade-buttons">
            <button
              @click="buyStock(stock.ticker)"
              :disabled="!canBuyStock(stock.ticker)"
              class="buy-btn"
            >
              Buy
            </button>
            <button
              @click="sellStock(stock.ticker)"
              :disabled="!canSellStock(stock.ticker)"
              class="sell-btn"
            >
              Sell
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="game-controls">
      <button @click="endGame" class="end-game-btn">End Game</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '@/stores/sessionStore'
import Plotly from 'plotly.js-dist-min'
import api from '@/services/api'

const router = useRouter()
const store = useSessionStore()

// Game state
const sessionId = ref('')
const selectedDate = ref('')
const currentDate = ref('')
const playerName = ref('')
const playerCash = ref(500) // Starting cash
const stockOwned = ref<Record<string, number>>({}) // Track owned quantities
const stocks = ref<
  Array<{
    ticker: string
    type: string
    companyName?: string
    sector?: string
  }>
>([])

// Price data for charts
const priceHistory = ref<Record<string, number[]>>({})
const dateLabels = ref<string[]>([])
const chartDataKey = ref(0) // Force chart updates

// Debug and connection status
const showDebugPanel = ref(false)
const connectionStatus = ref({
  text: '🔌 Connecting...',
  class: 'status-connecting',
})

let socket: WebSocket | null = null
let dayUpdateInterval: number | null = null
let mockDataInterval: number | null = null
let isMockDataRunning = false

onMounted(() => {
  // Get session data from store
  sessionId.value = store.sessionId
  const storedStocks = store.selectedStocks

  if (!sessionId.value || !storedStocks.length) {
    // Redirect back to game setup if no session
    router.push('/')
    return
  }

  // Initialize stock data from store
  initializeGameData()

  // Connect to WebSocket
  connectWebSocket()
})

// Watch for changes in price history to force reactivity
watch(
  priceHistory,
  (newPriceHistory) => {
    console.log('👁️ Price history changed, skipping watcher update (manual updates used)')
    console.log('📊 Current price data:', newPriceHistory)
    // Note: Manual updates are called directly from WebSocket handler for immediate response
  },
  { deep: true },
)

// Watch for chart data key changes to recreate charts if needed (for major updates)
watch(chartDataKey, (newKey) => {
  console.log(`🔄 Chart recreate triggered with key: ${newKey}`)
  nextTick(() => {
    createAllCharts()
  })
})

onUnmounted(() => {
  if (socket) {
    socket.close()
  }
  if (dayUpdateInterval) {
    clearInterval(dayUpdateInterval)
    dayUpdateInterval = null
  }
  if (mockDataInterval) {
    clearInterval(mockDataInterval)
    mockDataInterval = null
    isMockDataRunning = false
  }
})

function initializeGameData() {
  // Get stored stock data from session store
  const storedStocks = store.selectedStocks
  const gameData = store.gameData

  console.log('🎮 Initializing game data...')
  console.log('📦 Stored stocks:', storedStocks)
  console.log('🎯 Game data:', gameData)

  if (!storedStocks.length || !gameData) {
    console.error('❌ Missing session data, redirecting to home')
    // Redirect back to game setup if no session data
    router.push('/')
    return
  }

  // Use the detailed stock information from the store
  stocks.value = gameData.stockDetails

  // Set date as a single string
  if (gameData.date) {
    if (typeof gameData.date === 'string') {
      selectedDate.value = gameData.date
    } else {
      // Convert object format to string if needed
      const monthName =
        typeof gameData.date.month === 'number'
          ? new Date(0, gameData.date.month - 1).toLocaleString('default', { month: 'long' })
          : gameData.date.month
      selectedDate.value = `${monthName} ${gameData.date.year}`
    }
  }

  playerName.value = gameData.playerName || 'Player'

  console.log('✅ Game data initialized:')
  console.log('📈 Stocks:', stocks.value)
  console.log('📅 Date:', selectedDate.value)
  console.log('👤 Player:', playerName.value)

  // Initialize price history for each stock
  stocks.value.forEach((stock) => {
    priceHistory.value[stock.ticker] = []
    stockOwned.value[stock.ticker] = 0 // Initialize with 0 shares
    console.log(`📊 Initialized price history for ${stock.ticker}`)
  })

  console.log('🔍 Price history structure:', Object.keys(priceHistory.value))

  // Create initial Plotly charts
  nextTick(() => {
    createAllCharts()
  })
}

function connectWebSocket() {
  const wsUrl = `ws://localhost:8000/ws/prices/${sessionId.value}`
  console.log('🔌 Attempting WebSocket connection to:', wsUrl)
  console.log(
    '📊 Available stocks for price updates:',
    stocks.value.map((s) => s.ticker),
  )

  connectionStatus.value = { text: '🔌 Connecting...', class: 'status-connecting' }
  socket = new WebSocket(wsUrl)

  socket.onopen = () => {
    console.log('✅ WebSocket connected successfully')
    console.log('🎯 Session ID:', sessionId.value)
    console.log(
      '📈 Expecting price data for tickers:',
      stocks.value.map((s) => s.ticker),
    )
    connectionStatus.value = { text: '✅ Connected', class: 'status-connected' }
  }

  socket.onmessage = (event) => {
    console.log('📨 WebSocket message received:', event.data)

    try {
      const data = JSON.parse(event.data)
      console.log('📋 Parsed WebSocket data:', data)

      // Check if this is an "end of historical price" message
      if (data.message && data.message.toLowerCase().includes('end of historical price')) {
        console.log('🏁 End of historical price stream detected, ending game...')
        connectionStatus.value = { text: '🏁 Stream Complete', class: 'status-complete' }

        // Show a brief message before ending the game
        setTimeout(() => {
          endGame()
        }, 2000) // Wait 2 seconds before ending
        return
      }

      // Handle new message format with prices array and stream_info
      if (data.prices && Array.isArray(data.prices)) {
        // Update current date from the WebSocket data
        if (data.current_date) {
          // Parse and format the current_date for display
          if (data.current_date.match(/^\d{4}-\d{2}-\d{2}$/)) {
            const [year, month, day] = data.current_date.split('-').map(Number)
            const date = new Date(year, month - 1, day)
            currentDate.value = date.toLocaleDateString('en-US', {
              month: 'long',
              day: 'numeric',
              year: 'numeric',
            })
          } else {
            currentDate.value = data.current_date
          }
          console.log('📅 Updated current date:', currentDate.value)
        }

        // Update date information from stream_info or current_date
        if (data.stream_info && data.stream_info.month && data.stream_info.year) {
          selectedDate.value = `${data.stream_info.month} ${data.stream_info.year}`
          console.log('📅 Updated date from stream_info:', selectedDate.value)
        } else if (data.current_date) {
          // Use current_date as fallback and format it nicely
          const date = new Date(data.current_date)
          selectedDate.value = date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
          console.log('📆 Updated date from current_date:', selectedDate.value)
        }

        // Process each price in the array
        data.prices.forEach(
          (priceData: { symbol: string; price: number; date: string; timestamp: string }) => {
            const ticker = priceData.symbol
            const price = priceData.price
            const priceDate = priceData.date

            // Check if we're tracking this ticker
            const stock = stocks.value.find((s) => s.ticker === ticker)
            if (!stock) {
              console.warn(`⚠️ Received data for unknown ticker: ${ticker}`)
              return
            }

            console.log(`💰 Adding price ${price} for ${ticker} on ${priceDate}`)

            // Initialize price history if it doesn't exist
            if (!priceHistory.value[ticker]) {
              console.log(`🆕 Initializing price history for ${ticker}`)
              priceHistory.value[ticker] = []
            }

            // Add new price data
            priceHistory.value[ticker].push(price)

            // Add the actual date to labels if it's not already there
            if (priceDate && !dateLabels.value.includes(priceDate)) {
              dateLabels.value.push(priceDate)
              console.log(`📅 Added new date label: ${priceDate}`)
            }
          },
        )

        // Ensure date labels length matches the longest price history
        const maxPriceLength = Math.max(
          ...Object.values(priceHistory.value).map((prices) => prices.length),
        )

        // If we have more price data than date labels, pad with the current date
        while (dateLabels.value.length < maxPriceLength) {
          const newDateStr =
            data.current_date ||
            data.stream_info?.current_date ||
            `Day ${dateLabels.value.length + 1}`
          dateLabels.value.push(newDateStr)
          console.log(`📅 Padded date labels with: ${newDateStr}`)
        }

        // The date labels should match the number of price data points, not the date_index + 1
        // Remove this section as it's causing the mismatch

        // Force immediate chart update
        nextTick(() => {
          updateAllCharts()
        })
        console.log(
          `🔄 Chart update triggered for ${Object.values(priceHistory.value).map((prices) => prices.length)} data points`,
        )
      } else {
        // Handle legacy single ticker format (fallback)
        if (!data.ticker || data.price === undefined) {
          console.warn('⚠️ Invalid data structure received:', data)
          return
        }

        // Check if we're tracking this ticker
        const stock = stocks.value.find((s) => s.ticker === data.ticker)
        if (!stock) {
          console.warn(`⚠️ Received data for unknown ticker: ${data.ticker}`)
          console.log(
            '📊 Currently tracking:',
            stocks.value.map((s) => s.ticker),
          )
          return
        }

        console.log(`💰 Adding price ${data.price} for ${data.ticker}`)

        // Initialize price history if it doesn't exist
        if (!priceHistory.value[data.ticker]) {
          console.log(`🆕 Initializing price history for ${data.ticker}`)
          priceHistory.value[data.ticker] = []
        }

        // Add new price data
        priceHistory.value[data.ticker].push(data.price)
        console.log(`📈 Price history for ${data.ticker}:`, priceHistory.value[data.ticker])

        // Update day labels if needed
        const currentLength = Math.max(
          ...Object.values(priceHistory.value).map((prices) => prices.length),
        )
        if (dateLabels.value.length < currentLength) {
          const newDay = dateLabels.value.length + 1
          // Use actual date if available, otherwise fall back to day number
          const dateStr = data.date || `Day ${newDay}`
          dateLabels.value.push(dateStr)
          console.log(`📅 Added ${dateStr} to labels`)
        }

        // Force immediate chart update
        nextTick(() => {
          updateAllCharts()
        })
        console.log(`🔄 Legacy format chart update triggered`)
      }
    } catch (error) {
      console.error('❌ Error parsing WebSocket message:', error)
      console.error('📄 Raw message:', event.data)
    }
  }

  socket.onclose = (event) => {
    console.log('🔌 WebSocket disconnected')
    console.log('📊 Close code:', event.code)
    console.log('📝 Close reason:', event.reason)
    console.log('🔄 Was clean close:', event.wasClean)

    connectionStatus.value = { text: '❌ Disconnected', class: 'status-disconnected' }

    // If WebSocket fails, start mock data for demo purposes
    if (!isMockDataRunning) {
      console.log('🎭 Starting mock data as fallback')
      connectionStatus.value = { text: '🎭 Using Mock Data', class: 'status-mock' }
      startMockData()
    }
  }

  socket.onerror = (error) => {
    console.error('❌ WebSocket error:', error)
    console.log('🔗 WebSocket URL:', wsUrl)
    console.log('🔌 WebSocket state:', socket?.readyState)

    connectionStatus.value = { text: '⚠️ Connection Error', class: 'status-error' }

    // If WebSocket fails, start mock data for demo purposes
    if (!isMockDataRunning) {
      console.log('🎭 Starting mock data due to WebSocket error')
      connectionStatus.value = { text: '🎭 Using Mock Data', class: 'status-mock' }
      startMockData()
    }
  }
}

function startMockData() {
  // Prevent multiple mock data sessions
  if (isMockDataRunning) {
    console.log('🎭 Mock data already running, skipping...')
    return
  }

  // Generate mock price data for demo purposes
  console.log('🎭 Starting mock data for demo...')
  console.log(
    '📈 Stocks to generate data for:',
    stocks.value.map((s) => s.ticker),
  )
  isMockDataRunning = true

  // Initialize with some starting prices
  stocks.value.forEach((stock) => {
    const basePrice = Math.random() * 100 + 50 // Random price between 50-150
    priceHistory.value[stock.ticker] = [basePrice]
    console.log(`💰 Initial mock price for ${stock.ticker}: $${basePrice.toFixed(2)}`)
  })

  dateLabels.value = ['2024-01-01'] // Start with actual date format

  // Force initial chart creation with mock data
  nextTick(() => {
    createAllCharts()
    chartDataKey.value++
  })
  console.log('📅 Initialized mock data with 2024-01-01')

  // Add new price data every 10 seconds for demo
  mockDataInterval = setInterval(() => {
    console.log('🎭 Generating mock price update...')

    stocks.value.forEach((stock) => {
      const currentPrices = priceHistory.value[stock.ticker]
      const lastPrice = currentPrices[currentPrices.length - 1]

      // Generate realistic price movement (±5% change)
      const changePercent = (Math.random() - 0.5) * 0.1 // ±5%
      const newPrice = lastPrice * (1 + changePercent)
      const finalPrice = Math.max(newPrice, 1) // Minimum price of $1

      priceHistory.value[stock.ticker].push(finalPrice)
      console.log(
        `📈 Mock price update for ${stock.ticker}: $${lastPrice.toFixed(2)} → $${finalPrice.toFixed(2)} (${changePercent > 0 ? '+' : ''}${(changePercent * 100).toFixed(2)}%)`,
      )
    })

    // Generate a mock date (starting from a base date and incrementing)
    const baseDate = new Date('2024-01-01')
    const dayOffset = dateLabels.value.length
    const currentDate = new Date(baseDate.getTime() + dayOffset * 24 * 60 * 60 * 1000)
    const dateStr = currentDate.toISOString().split('T')[0] // YYYY-MM-DD format

    const newDay = dateLabels.value.length + 1
    dateLabels.value.push(dateStr)

    // Force immediate chart update
    nextTick(() => {
      updateAllCharts()
      chartDataKey.value++
    })

    console.log(`📅 Mock data: Added ${dateStr} (Day ${newDay}), chart key: ${chartDataKey.value}`)

    // Stop after 30 days for demo
    if (dateLabels.value.length >= 30) {
      console.log('🏁 Mock data complete (30 days reached)')
      if (mockDataInterval) {
        clearInterval(mockDataInterval)
        mockDataInterval = null
        isMockDataRunning = false
      }
    }
  }, 10000) // Every 10 seconds
}

function createPlotlyChart(ticker: string, index: number) {
  const prices = priceHistory.value[ticker] || []
  const rawLabels = dateLabels.value.slice(0, prices.length)
  const labels = rawLabels.map(formatDateLabel) // Format dates for better display

  const data: Partial<Plotly.PlotData>[] = [
    {
      x: labels,
      y: prices,
      type: 'scatter',
      mode: 'lines+markers',
      line: {
        color: getStockColor(ticker),
        width: 3,
      },
      marker: {
        color: getStockColor(ticker),
        size: 6,
        line: {
          color: '#ffffff',
          width: 2,
        },
      },
      fill: 'tonexty',
      fillcolor: getStockColor(ticker, 0.2),
      name: ticker,
    },
  ]

  const layout: Partial<Plotly.Layout> = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: {
      color: '#cccccc',
      family: 'Orbitron, Courier New, Monaco, monospace',
    },
    xaxis: {
      gridcolor: 'rgba(255, 255, 255, 0.1)',
      tickcolor: '#cccccc',
      linecolor: 'rgba(255, 255, 255, 0.3)',
      title: {
        text: 'Date',
        font: { color: '#cccccc' },
      },
      tickangle: -45, // Rotate labels for better readability
      automargin: true,
    },
    yaxis: {
      gridcolor: 'rgba(255, 255, 255, 0.1)',
      tickcolor: '#cccccc',
      linecolor: 'rgba(255, 255, 255, 0.3)',
      title: {
        text: 'Price ($)',
        font: { color: '#cccccc' },
      },
    },
    showlegend: false,
    margin: { t: 10, r: 10, b: 60, l: 50 }, // Increased bottom margin for rotated labels
    hovermode: 'x unified',
    hoverlabel: {
      bgcolor: 'rgba(0, 0, 0, 0.8)',
      bordercolor: getStockColor(ticker),
      font: { color: '#ffffff' },
    },
  }

  const config: Partial<Plotly.Config> = {
    responsive: true,
    displayModeBar: false,
  }

  const chartElement = document.getElementById(`chart-${index}`)
  if (chartElement) {
    Plotly.newPlot(chartElement, data, layout, config)
  }
}

function updatePlotlyChart(ticker: string, index: number) {
  const prices = priceHistory.value[ticker] || []
  const rawLabels = dateLabels.value.slice(0, prices.length)
  const labels = rawLabels.map(formatDateLabel) // Format dates for better display

  console.log(`🔍 Updating chart for ${ticker}:`)
  console.log(`📊 Price data points: ${prices.length}`)
  console.log(`📅 Date labels available: ${dateLabels.value.length}`)
  console.log(`📈 Using ${labels.length} labels for ${prices.length} prices`)

  const chartElement = document.getElementById(`chart-${index}`)
  if (chartElement && prices.length > 0) {
    try {
      // Use Plotly.restyle for efficient updates
      Plotly.restyle(
        chartElement,
        {
          x: [labels],
          y: [prices],
        },
        0,
      )
      console.log(`📈 Updated chart for ${ticker} with ${prices.length} data points`)
    } catch (error) {
      console.warn(`⚠️ Error updating chart for ${ticker}, recreating:`, error)
      // If restyle fails, recreate the chart
      createPlotlyChart(ticker, index)
    }
  } else if (chartElement && prices.length === 0) {
    console.log(`📊 No data yet for ${ticker}, skipping update`)
  }
}

function updateAllCharts() {
  stocks.value.forEach((stock, index) => {
    updatePlotlyChart(stock.ticker, index)
  })
}

function createAllCharts() {
  stocks.value.forEach((stock, index) => {
    createPlotlyChart(stock.ticker, index)
  })
}

function getStockColor(ticker: string, alpha: number = 1) {
  const stock = stocks.value.find((s) => s.ticker === ticker)
  if (!stock) return `rgba(0, 245, 255, ${alpha})`

  switch (stock.type) {
    case 'Popular':
      return `rgba(255, 215, 0, ${alpha})` // Gold
    case 'Volatile':
      return `rgba(255, 107, 107, ${alpha})` // Red
    case 'Sector':
      return `rgba(78, 205, 196, ${alpha})` // Teal
    default:
      return `rgba(0, 245, 255, ${alpha})` // Cyan
  }
}

function getCurrentPrice(ticker: string): string {
  const prices = priceHistory.value[ticker]
  if (!prices || prices.length === 0) return '0.00'
  return prices[prices.length - 1].toFixed(2)
}

function getPriceChange(ticker: string): { value: number; percentage: number } {
  const prices = priceHistory.value[ticker]
  if (!prices || prices.length < 2) {
    return { value: 0, percentage: 0 }
  }

  const currentPrice = prices[prices.length - 1]
  const previousPrice = prices[prices.length - 2]
  const value = currentPrice - previousPrice
  const percentage = (value / previousPrice) * 100

  return { value, percentage }
}

function getPriceChangeText(ticker: string): string {
  const change = getPriceChange(ticker)

  if (change.value === 0) {
    return 'No change'
  }

  const sign = change.value > 0 ? '+' : ''
  const valueText = `${sign}$${change.value.toFixed(2)}`
  const percentText = `${sign}${change.percentage.toFixed(2)}%`

  return `${valueText} (${percentText})`
}

function getPriceChangeClass(ticker: string): string {
  const change = getPriceChange(ticker)

  if (change.value > 0) {
    return 'price-up'
  } else if (change.value < 0) {
    return 'price-down'
  } else {
    return 'price-neutral'
  }
}

function getPortfolioValue(): number {
  let totalValue = 0
  Object.keys(stockOwned.value).forEach((ticker) => {
    const shares = stockOwned.value[ticker]
    const currentPrice = parseFloat(getCurrentPrice(ticker))
    totalValue += shares * currentPrice
  })
  return totalValue
}

// Record trade via API
async function recordTrade(
  symbol: string,
  action: 'buy' | 'sell',
  qty: number,
  price: number,
): Promise<void> {
  try {
    const tradeData = {
      session_id: store.sessionId,
      symbol,
      action,
      qty,
      price,
      timestamp: new Date().toISOString(),
    }

    console.log('📝 Recording trade:', tradeData)

    // Call the API to record the trade
    const response = await api.post('/api/trades', tradeData)
    console.log('✅ Trade recorded successfully:', response.data)
  } catch (error) {
    console.error('❌ Error recording trade:', error)
    // Don't throw the error to avoid disrupting the UI trading flow
  }
}

function getMaxBuyQuantity(ticker: string): number {
  const currentPrice = parseFloat(getCurrentPrice(ticker))
  if (currentPrice === 0) return 0
  return Math.floor(playerCash.value / currentPrice)
}

function canBuyStock(ticker: string): boolean {
  const currentPrice = parseFloat(getCurrentPrice(ticker))
  return currentPrice > 0 && playerCash.value >= currentPrice
}

function canSellStock(ticker: string): boolean {
  return (stockOwned.value[ticker] || 0) > 0
}

function buyStock(ticker: string): void {
  const quantityInput = document.getElementById(`quantity-${ticker}`) as HTMLInputElement
  const quantity = parseInt(quantityInput?.value || '1')
  const currentPrice = parseFloat(getCurrentPrice(ticker))
  const totalCost = quantity * currentPrice

  if (quantity <= 0) {
    alert('Please enter a valid quantity')
    return
  }

  if (totalCost > playerCash.value) {
    alert('Insufficient funds')
    return
  }

  if (!canBuyStock(ticker)) {
    alert('Cannot buy this stock')
    return
  }

  // Execute the trade
  playerCash.value -= totalCost
  stockOwned.value[ticker] = (stockOwned.value[ticker] || 0) + quantity

  console.log(
    `🛒 Bought ${quantity} shares of ${ticker} at $${currentPrice.toFixed(2)} each. Total: $${totalCost.toFixed(2)}`,
  )
  console.log(`💰 Remaining cash: $${playerCash.value.toFixed(2)}`)
  console.log(`📊 ${ticker} shares owned: ${stockOwned.value[ticker]}`)

  // Record the trade via API
  recordTrade(ticker, 'buy', quantity, currentPrice)

  // Clear the input
  if (quantityInput) quantityInput.value = ''
}

function sellStock(ticker: string): void {
  const quantityInput = document.getElementById(`quantity-${ticker}`) as HTMLInputElement
  const quantity = parseInt(quantityInput?.value || '1')
  const currentPrice = parseFloat(getCurrentPrice(ticker))
  const totalValue = quantity * currentPrice

  if (quantity <= 0) {
    alert('Please enter a valid quantity')
    return
  }

  if (quantity > (stockOwned.value[ticker] || 0)) {
    alert('Insufficient shares to sell')
    return
  }

  if (!canSellStock(ticker)) {
    alert("You don't own any shares of this stock")
    return
  }

  // Execute the trade
  playerCash.value += totalValue
  stockOwned.value[ticker] = (stockOwned.value[ticker] || 0) - quantity

  console.log(
    `💸 Sold ${quantity} shares of ${ticker} at $${currentPrice.toFixed(2)} each. Total: $${totalValue.toFixed(2)}`,
  )
  console.log(`💰 New cash balance: $${playerCash.value.toFixed(2)}`)
  console.log(`📊 ${ticker} shares remaining: ${stockOwned.value[ticker]}`)

  // Record the trade via API
  recordTrade(ticker, 'sell', quantity, currentPrice)

  // Clear the input
  if (quantityInput) quantityInput.value = ''
}
function getWebSocketState(): string {
  if (!socket) return 'Not Connected'

  switch (socket.readyState) {
    case WebSocket.CONNECTING:
      return 'Connecting'
    case WebSocket.OPEN:
      return 'Connected'
    case WebSocket.CLOSING:
      return 'Closing'
    case WebSocket.CLOSED:
      return 'Closed'
    default:
      return 'Unknown'
  }
}

function formatDateLabel(dateStr: string): string {
  // If it's already a formatted string like "Day X", return as is
  if (dateStr.startsWith('Day ')) {
    return dateStr
  }

  // Try to parse as date and format nicely
  try {
    // Handle YYYY-MM-DD format specifically to avoid timezone issues
    if (dateStr.match(/^\d{4}-\d{2}-\d{2}$/)) {
      const [year, month, day] = dateStr.split('-').map(Number)
      const date = new Date(year, month - 1, day) // month is 0-indexed in Date constructor
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      })
    }

    // Fallback for other date formats
    const date = new Date(dateStr)
    if (!isNaN(date.getTime())) {
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      })
    }
  } catch {
    // If parsing fails, return original string
  }

  return dateStr
}

function toggleDebugPanel() {
  showDebugPanel.value = !showDebugPanel.value
}

async function endGame() {
  // Stop intervals and close connections
  if (dayUpdateInterval) {
    clearInterval(dayUpdateInterval)
    dayUpdateInterval = null
  }
  if (mockDataInterval) {
    clearInterval(mockDataInterval)
    mockDataInterval = null
    isMockDataRunning = false
  }
  if (socket) {
    socket.close()
  }
  const error = ref('')
  try {
    const session_resp = await api.post('api/sessions/' + sessionId.value + '/end')
    console.log('✅ Game session ended successfully:', session_resp.data)

    // Store the game results in the session store
    store.setGameResult(session_resp.data)
  } catch (err) {
    console.error('Failed to load game data:', err)
    error.value = `Failed to load game data: ${err}`
  }

  // Navigate to results page
  router.push('/results')
}
</script>

<style scoped>
.active-game-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
  color: #ffffff;
  padding: 2rem;
  font-family: 'Orbitron', 'Courier New', 'Monaco', monospace;
}

.active-game-container h2 {
  text-align: center;
  font-size: 2.5rem;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 3px;
  background: linear-gradient(45deg, #00f5ff, #ff00f5);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 2rem;
  text-shadow: 0 0 20px rgba(0, 245, 255, 0.3);
}

.game-info {
  display: flex;
  justify-content: center;
  gap: 2rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}

.session-info,
.date-info,
.player-info,
.cash-info,
.portfolio-info,
.connection-info {
  background: rgba(0, 0, 0, 0.3);
  padding: 0.75rem 1.5rem;
  border-radius: 10px;
  border: 1px solid rgba(0, 245, 255, 0.3);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: #00f5ff;
}

.cash-info {
  border-color: rgba(255, 215, 0, 0.3) !important;
  color: #ffd700 !important;
}

.portfolio-info {
  border-color: rgba(46, 213, 115, 0.3) !important;
  color: #2ed573 !important;
}

.status-connected {
  color: #4ecdc4 !important;
  border-color: rgba(78, 205, 196, 0.3) !important;
}

.status-disconnected {
  color: #ff6b6b !important;
  border-color: rgba(255, 107, 107, 0.3) !important;
}

.status-connecting {
  color: #ffd700 !important;
  border-color: rgba(255, 215, 0, 0.3) !important;
}

.status-error {
  color: #ff4757 !important;
  border-color: rgba(255, 71, 87, 0.3) !important;
}

.status-mock {
  color: #a55eea !important;
  border-color: rgba(165, 94, 234, 0.3) !important;
}

.status-complete {
  color: #2ed573 !important;
  border-color: rgba(46, 213, 115, 0.3) !important;
}

.debug-panel {
  background: rgba(0, 0, 0, 0.4);
  border: 2px solid rgba(0, 245, 255, 0.3);
  border-radius: 15px;
  padding: 1.5rem;
  margin: 2rem 0;
  color: #ffffff;
}

.debug-panel h4 {
  color: #00f5ff;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 2px;
  margin-bottom: 1rem;
  text-align: center;
}

.debug-item {
  margin-bottom: 1rem;
  padding: 0.5rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.debug-item strong {
  color: #00f5ff;
  display: block;
  margin-bottom: 0.5rem;
}

.debug-item ul {
  margin: 0.5rem 0 0 1rem;
  list-style-type: none;
  padding: 0;
}

.debug-item li {
  padding: 0.25rem 0;
  color: #cccccc;
  font-family: 'Courier New', monospace;
}

.debug-toggle-container {
  text-align: center;
  margin: 1rem 0;
}

.debug-toggle {
  background: rgba(0, 245, 255, 0.2);
  border: 1px solid rgba(0, 245, 255, 0.5);
  color: #00f5ff;
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: 'Orbitron', 'Courier New', monospace;
}

.debug-toggle:hover {
  background: rgba(0, 245, 255, 0.3);
  transform: translateY(-1px);
}

.charts-container {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2rem;
  margin-bottom: 2rem;
}

@media (min-width: 1200px) {
  .charts-container {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (min-width: 768px) and (max-width: 1199px) {
  .charts-container {
    grid-template-columns: repeat(2, 1fr);
  }
}

.chart-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 15px;
  padding: 1.5rem;
  border: 2px solid;
  transition: all 0.3s ease;
  min-height: 550px;
}

.popular-card {
  border-color: #ffd700;
  background: linear-gradient(145deg, rgba(255, 215, 0, 0.1), rgba(255, 140, 0, 0.05));
}

.volatile-card {
  border-color: #ff6b6b;
  background: linear-gradient(145deg, rgba(255, 107, 107, 0.1), rgba(255, 69, 58, 0.05));
}

.sector-card {
  border-color: #4ecdc4;
  background: linear-gradient(145deg, rgba(78, 205, 196, 0.1), rgba(0, 245, 255, 0.05));
}

.chart-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
}

.chart-header {
  text-align: center;
  margin-bottom: 1rem;
}

.chart-header h3 {
  font-size: 1.2rem;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 2px;
  color: #00f5ff;
  margin-bottom: 0.5rem;
}

.company-name {
  font-size: 0.9rem;
  color: #cccccc;
  margin-bottom: 0.5rem;
}

.current-price {
  font-size: 1.5rem;
  font-weight: 900;
  color: #00f5ff;
  text-shadow: 0 0 15px rgba(0, 245, 255, 0.5);
}

.price-change {
  font-size: 0.9rem;
  font-weight: 600;
  margin-top: 0.5rem;
  padding: 0.25rem 0.5rem;
  border-radius: 5px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.price-up {
  color: #2ed573;
  background: rgba(46, 213, 115, 0.1);
  border: 1px solid rgba(46, 213, 115, 0.3);
}

.price-down {
  color: #ff6b6b;
  background: rgba(255, 107, 107, 0.1);
  border: 1px solid rgba(255, 107, 107, 0.3);
}

.price-neutral {
  color: #cccccc;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.stock-owned {
  font-size: 0.8rem;
  color: #cccccc;
  margin-top: 0.25rem;
  font-weight: 500;
}

.trading-controls {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  padding: 1rem;
  margin-top: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.trade-input-group {
  margin-bottom: 0.75rem;
}

.trade-input-group label {
  display: block;
  font-size: 0.8rem;
  color: #cccccc;
  margin-bottom: 0.25rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.quantity-input {
  width: 100%;
  padding: 0.5rem;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(0, 245, 255, 0.3);
  border-radius: 5px;
  color: #ffffff;
  font-size: 0.9rem;
  font-family: 'Orbitron', 'Courier New', monospace;
}

.quantity-input:focus {
  outline: none;
  border-color: #00f5ff;
  box-shadow: 0 0 10px rgba(0, 245, 255, 0.3);
}

.trade-buttons {
  display: flex;
  gap: 0.5rem;
}

.buy-btn,
.sell-btn {
  flex: 1;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 5px;
  font-weight: 600;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: 'Orbitron', 'Courier New', monospace;
}

.buy-btn {
  background: linear-gradient(135deg, #2ed573 0%, #26d063 100%);
  color: white;
}

.buy-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 5px 15px rgba(46, 213, 115, 0.3);
}

.buy-btn:disabled {
  background: #555;
  color: #999;
  cursor: not-allowed;
}

.sell-btn {
  background: linear-gradient(135deg, #ff6b6b 0%, #ff5252 100%);
  color: white;
}

.sell-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 5px 15px rgba(255, 107, 107, 0.3);
}

.sell-btn:disabled {
  background: #555;
  color: #999;
  cursor: not-allowed;
}

.chart-wrapper {
  height: 250px;
  position: relative;
}

.plotly-chart {
  width: 100%;
  height: 100%;
}

.game-controls {
  text-align: center;
  margin-top: 2rem;
}

.end-game-btn {
  background: linear-gradient(135deg, #ff6b6b 0%, #ff4757 100%);
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
  position: relative;
  overflow: hidden;
}

.end-game-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(255, 107, 107, 0.4);
}

.end-game-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.end-game-btn:hover::before {
  left: 100%;
}

/* Responsive design */
@media (max-width: 768px) {
  .active-game-container {
    padding: 1rem;
  }

  .active-game-container h2 {
    font-size: 1.8rem;
  }

  .game-info {
    gap: 1rem;
  }

  .session-info,
  .date-info,
  .player-info,
  .cash-info,
  .portfolio-info {
    padding: 0.5rem 1rem;
    font-size: 0.9rem;
  }

  .chart-card {
    padding: 1rem;
    min-height: 450px;
  }

  .chart-wrapper {
    height: 200px;
  }
}
</style>
