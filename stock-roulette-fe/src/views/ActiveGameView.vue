<template>
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
              <button @click="toggleDebugPanel" class="debug-toggle">Hide Debug</button>
            </div>
            <div v-else class="debug-toggle-container">
              <button @click="toggleDebugPanel" class="debug-toggle">Show Debug</button>
            </div>
            <div v-if="tradingError" class="trading-error-banner">
              <div class="error-content">
                <span class="error-icon">💸</span>
                <span class="error-message">{{ tradingError }}</span>
                <button @click="clearTradingError" class="close-error-btn">×</button>
              </div>
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
                  <div class="trade-input-section">
                    <div class="trade-input-group">
                      <label for="`quantity-${stock.ticker}`">Quantity:</label>
                      <div class="input-with-buttons">
                        <input
                          v-model.number="tradeQuantities[stock.ticker]"
                          :id="`quantity-${stock.ticker}`"
                          type="number"
                          min="1"
                          :max="getMaxBuyQuantity(stock.ticker)"
                          class="quantity-input"
                          :disabled="!canBuyStock(stock.ticker) && !canSellStock(stock.ticker)"
                        />
                        <div class="max-buttons">
                          <button
                            class="max-btn buy-max"
                            @click="setMaxBuy(stock.ticker)"
                            :disabled="!canBuyStock(stock.ticker)"
                          >
                            Max Buy
                          </button>
                          <button
                            class="max-btn sell-max"
                            @click="setMaxSell(stock.ticker)"
                            :disabled="!canSellStock(stock.ticker)"
                          >
                            Max Sell
                          </button>
                        </div>
                      </div>
                    </div>
                    <div class="trade-hints">
                      <div class="buy-hint" v-if="canBuyStock(stock.ticker)">
                        <span class="hint-text">You can buy up to {{ getMaxBuyQuantity(stock.ticker) }} shares</span>
                      </div>
                      <div class="sell-hint" v-if="canSellStock(stock.ticker)">
                        <span class="hint-text">You can sell up to {{ getMaxSellQuantity(stock.ticker) }} shares</span>
                      </div>
                      <div class="no-trade-hint" v-if="!canBuyStock(stock.ticker) && !canSellStock(stock.ticker)">
                        <span class="hint-text">Insufficient funds & no shares owned</span>
                      </div>
                    </div>
                  </div>
                  <div class="trade-buttons">
                    <button
                      @click="buyStock(stock.ticker)"
                      :disabled="!canBuyStock(stock.ticker)"
                      class="buy-btn"
                      :title="
                        canBuyStock(stock.ticker)
                          ? `Buy up to ${getMaxBuyQuantity(stock.ticker)} shares`
                          : 'Insufficient funds'
                      "
                    >
                      💰 Buy
                    </button>
                    <button
                      @click="sellStock(stock.ticker)"
                      :disabled="!canSellStock(stock.ticker)"
                      class="sell-btn"
                      :title="
                        canSellStock(stock.ticker)
                          ? `Sell up to ${getMaxSellQuantity(stock.ticker)} shares`
                          : 'No shares owned'
                      "
                    >
                      💸 Sell
                    </button>
                  </div>
                </div>
              </div>
            </div>
            <div class="game-controls">
              <button @click="endGame" class="end-game-btn">End Game</button>
            </div>
          </div>
          <div class="advice-section-fixed">
            <div class="advice-section">
              <div class="advice-header">
                <h3>🤖 AI Trading Advisor</h3>
                <div class="advice-controls">
                  <button
                    @click="getAIAdvice"
                    :disabled="isLoadingAdvice || stocks.length === 0"
                    class="advice-btn"
                  >
                    {{ isLoadingAdvice ? '🔄 AI Analyzing...' : '🎯 Get AI Advice' }}
                  </button>
                </div>
              </div>
              <div v-if="showDebugPanel" class="advice-debug">
                <h5>🔧 AI Advice Debug Info</h5>
                <div class="debug-item"><strong>Session ID:</strong> {{ sessionId || 'None' }}</div>
                <div class="debug-item">
                  <strong>Available Stocks:</strong> {{ stocks.map((s) => s.ticker).join(', ') || 'None' }}
                </div>
                <div class="debug-item">
                  <strong>API Endpoint:</strong> POST /sessions/{{ sessionId }}/advise
                </div>
                <div class="debug-item">
                  <strong>Last Response:</strong>
                  <pre v-if="lastAdviceResponse">{{ JSON.stringify(getOrderedAdviceResponse(), null, 2) }}</pre>
                  <span v-else>No response yet</span>
                </div>
              </div>
              <div v-if="isLoadingAdvice" class="advice-loading">
                <div class="loading-spinner"></div>
                <p>AI is analyzing market trends and your portfolio...</p>
              </div>
              <div v-if="adviceError" class="advice-error">
                <p>❌ {{ adviceError }}</p>
                <button @click="clearAdviceError" class="clear-error-btn">Clear</button>
              </div>
              <div v-if="tradingAdvice.length > 0 && !isLoadingAdvice" class="advice-results">
                <h4>💡 Trading Recommendations</h4>
                <div class="advice-cards">
                  <div
                    v-for="advice in tradingAdvice"
                    :key="advice.symbol"
                    class="advice-card"
                    :class="getAdviceActionClass(advice.action)"
                  >
                    <div class="advice-card-header">
                      <span class="stock-symbol">{{ advice.symbol }}</span>
                      <span class="advice-action" :class="getAdviceActionClass(advice.action)">
                        {{ advice.action }}
                      </span>
                    </div>
                    <div class="advice-reason">
                      {{ advice.reason }}
                    </div>
                    <div class="current-position">
                      Currently own: {{ stockOwned[advice.symbol] || 0 }} shares
                    </div>
                  </div>
                </div>
                <div class="advice-disclaimer">
                  <small
                    >⚠️ This is AI-generated advice for educational purposes. Always do your own
                    research.</small
                  >
                </div>
              </div>
            </div>
          </div>
        </div>



const router = useRouter()
const store = useSessionStore()

// Game state
const sessionId = ref('')
const selectedDate = ref('')
const currentDate = ref('')
const playerName = ref('')
const playerCash = ref(500) // Starting cash

// --- TypeScript types moved to separate block to avoid Vue parser errors ---
<script lang="ts">
export type StockOwned = Record<string, number>;
export type Stock = {
  ticker: string;
  type: string;
  companyName?: string;
  sector?: string;
};
export type PriceHistory = Record<string, number[]>;
</script>
<script setup lang="ts">

const stockOwned = ref({} as StockOwned); // Track owned quantities
const stocks = ref([] as Stock[]);
const priceHistory = ref({} as PriceHistory);
const dateLabels = ref([] as string[]);
const chartDataKey = ref(0) // Force chart updates

// Debug and connection status
const showDebugPanel = ref(false)
const connectionStatus = ref({
  text: '🔌 Connecting...',
  class: 'status-connecting',
})

// AI Trading Advice state
const tradingAdvice = ref<
  Array<{
    symbol: string
    action: 'BUY' | 'SELL' | 'HOLD'
    reason: string
  }>
>([])
const isLoadingAdvice = ref(false)
const adviceError = ref('')
const lastAdviceResponse = ref<object | null>(null)

// Trading error state for user-friendly error messages
const tradingError = ref('')

// AI advice throttling
let lastAdviceRequestTime = 0
const ADVICE_THROTTLE_MS = 5000 // 5 seconds between automatic advice requests

let socket: WebSocket | null = null
let dayUpdateInterval: number | null = null

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
    socket = null
  }
  // Clear WebSocket from store
  store.setWebSocket(null)
  if (dayUpdateInterval) {
    clearInterval(dayUpdateInterval)
    dayUpdateInterval = null
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
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  const wsUrl = `${apiUrl.replace('http', 'ws')}/ws/prices/${sessionId.value}`
  console.log('🔌 Attempting WebSocket connection to:', wsUrl)
  console.log(
    '📊 Available stocks for price updates:',
    stocks.value.map((s) => s.ticker),
  )

  connectionStatus.value = { text: '🔌 Connecting...', class: 'status-connecting' }
  socket = new WebSocket(wsUrl)

  // Store the WebSocket reference in the session store
  store.setWebSocket(socket)

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

        // Automatically get AI advice when new stock prices are received
        console.log('🤖 New stock prices received, automatically requesting AI advice...')
        getAIAdviceThrottled()
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

        // Automatically get AI advice when new stock prices are received
        console.log(
          '🤖 New stock price received (legacy format), automatically requesting AI advice...',
        )
        getAIAdviceThrottled()
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
  }

  socket.onerror = (error) => {
    console.error('❌ WebSocket error:', error)
    console.log('🔗 WebSocket URL:', wsUrl)
    console.log('🔌 WebSocket state:', socket?.readyState)

    connectionStatus.value = { text: '⚠️ Connection Error', class: 'status-error' }
  }
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

function getMaxSellQuantity(ticker: string): number {
  return stockOwned.value[ticker] || 0
}

function setMaxBuyQuantity(ticker: string): void {
  const quantityInput = document.getElementById(`quantity-${ticker}`) as HTMLInputElement
  if (quantityInput) {
    quantityInput.value = getMaxBuyQuantity(ticker).toString()
  }
}

function setMaxSellQuantity(ticker: string): void {
  const quantityInput = document.getElementById(`quantity-${ticker}`) as HTMLInputElement
  if (quantityInput) {
    quantityInput.value = getMaxSellQuantity(ticker).toString()
  }
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
    showTradingError('Please enter a valid quantity (1 or more shares)')
    return
  }

  if (totalCost > playerCash.value) {
    showTradingError(
      `Oops! You need $${totalCost.toFixed(2)} but only have $${playerCash.value.toFixed(2)} available`,
    )
    return
  }

  if (!canBuyStock(ticker)) {
    showTradingError('This stock is currently unavailable for purchase')
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
    showTradingError('Please enter a valid quantity (1 or more shares)')
    return
  }

  if (quantity > (stockOwned.value[ticker] || 0)) {
    showTradingError(
      `You only own ${stockOwned.value[ticker] || 0} shares of ${ticker}, but tried to sell ${quantity}`,
    )
    return
  }

  if (!canSellStock(ticker)) {
    showTradingError(`You don't own any shares of ${ticker} to sell`)
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

// Chart Update Functions
function updateAllCharts() {
  console.log('📊 Executing chart update')
  stocks.value.forEach((stock, index) => {
    updatePlotlyChart(stock.ticker, index)
  })
}

// AI Trading Advice Functions
// Throttled version for automatic calls to prevent too many requests
function getAIAdviceThrottled() {
  const now = Date.now()
  if (now - lastAdviceRequestTime < ADVICE_THROTTLE_MS) {
    console.log('🤖 Throttling AI advice request, too soon since last request')
    return
  }

  lastAdviceRequestTime = now
  console.log('🤖 Throttled AI advice request approved, making call...')

  getAIAdvice().catch((error) => {
    console.warn('⚠️ Throttled AI advice request failed:', error)
    // Don't show error to user for automatic requests
  })
}

async function getAIAdvice() {
  if (!sessionId.value) {
    adviceError.value = 'No active session found'
    console.warn('🤖 No session ID available for AI advice request')
    return
  }

  if (stocks.value.length === 0) {
    adviceError.value = 'No stocks selected for this session'
    console.warn('🤖 No stocks available for AI advice request')
    return
  }

  isLoadingAdvice.value = true
  adviceError.value = ''
  tradingAdvice.value = []

  try {
    console.log('🤖 Requesting AI advice for session:', sessionId.value)
    console.log(
      '🤖 Available stocks:',
      stocks.value.map((s) => s.ticker),
    )
    console.log('🤖 API endpoint:', `/api/sessions/${sessionId.value}/advise`)

    const response = await api.post(`/api/sessions/${sessionId.value}/advise`)
    console.log('✅ AI advice response status:', response.status)
    console.log('✅ AI advice response data:', response.data)

    // Store response for debugging
    lastAdviceResponse.value = response.data

    // Handle the advice field - it can be either an array or a JSON string
    if (response.data && response.data.advice) {
      console.log('🔍 Raw advice data:', response.data.advice)

      let recommendations: Array<{
        symbol: string
        action: 'BUY' | 'SELL' | 'HOLD'
        reason: string
      }>

      // Check if advice is already an array (new format)
      if (Array.isArray(response.data.advice)) {
        console.log('✅ Advice is already an array, using directly')
        recommendations = response.data.advice
      } else if (typeof response.data.advice === 'string') {
        console.log('🔍 Advice is a string, attempting to parse as JSON')

        // Clean the advice string - remove markdown code blocks if present
        let cleanAdvice = response.data.advice.trim()

        // Check if the response is wrapped in markdown code blocks
        if (cleanAdvice.startsWith('```json') && cleanAdvice.endsWith('```')) {
          console.log('🧹 Removing markdown code blocks from advice response')
          cleanAdvice = cleanAdvice.replace(/^```json\s*/, '').replace(/\s*```$/, '')
        } else if (cleanAdvice.startsWith('```') && cleanAdvice.endsWith('```')) {
          console.log('🧹 Removing generic code blocks from advice response')
          cleanAdvice = cleanAdvice.replace(/^```\s*/, '').replace(/\s*```$/, '')
        }

        console.log('🔍 Cleaned advice string:', cleanAdvice)

        try {
          recommendations = JSON.parse(cleanAdvice)
        } catch (parseError) {
          console.error('❌ Error parsing advice JSON:', parseError)
          console.error('❌ Raw advice data:', response.data.advice)
          console.error('❌ Cleaned advice data:', cleanAdvice)
          throw new Error('Failed to parse AI advice response')
        }
      } else {
        throw new Error('Invalid advice format: expected array or string')
      }

      console.log('💡 Processing trading recommendations:', recommendations)

      // Validate the recommendations structure
      if (Array.isArray(recommendations) && recommendations.length > 0) {
        // Ensure each recommendation has required fields
        const validRecommendations = recommendations.filter(
          (rec) => rec.symbol && rec.action && rec.reason,
        )

        if (validRecommendations.length > 0) {
          // Sort recommendations to match UI order: Popular (left), Volatile (middle), Sector (right)
          const sortedRecommendations = validRecommendations.sort((a, b) => {
            const stockA = stocks.value.find(s => s.ticker === a.symbol)
            const stockB = stocks.value.find(s => s.ticker === b.symbol)

            const typeOrderA = getStockTypeOrder(stockA?.type || '')
            const typeOrderB = getStockTypeOrder(stockB?.type || '')

            return typeOrderA - typeOrderB
          })

          tradingAdvice.value = sortedRecommendations
          console.log('✅ Successfully set trading advice (sorted by UI order):', sortedRecommendations)
        } else {
          throw new Error('No valid recommendations found in response')
        }
      } else {
        throw new Error('Invalid recommendations format: expected non-empty array')
      }
    } else {
      console.error('❌ No advice field in response:', response.data)
      throw new Error('No advice data received from API')
    }
  } catch (error: unknown) {
    console.error('❌ Error getting AI advice:', error)

    // Handle specific HTTP error codes
    if (error && typeof error === 'object' && 'response' in error) {
      const axiosError = error as {
        response?: { status?: number; data?: { detail?: string; message?: string } }
      }
      console.error('❌ Axios error details:', {
        status: axiosError.response?.status,
        data: axiosError.response?.data,
      })

      if (axiosError.response?.status === 404) {
        adviceError.value = 'Session not found. Please start a new game.'
      } else if (axiosError.response?.status === 400) {
        adviceError.value = 'No stocks selected yet for this session.'
      } else if (axiosError.response?.status === 500) {
        adviceError.value = 'Price history missing for selected stocks. Please wait for more data.'
      } else {
        const errorMsg =
          axiosError.response?.data?.detail ||
          axiosError.response?.data?.message ||
          'Failed to get AI advice. Please try again.'
        adviceError.value = errorMsg
      }
    } else if (error instanceof Error) {
      adviceError.value = error.message
    } else {
      adviceError.value = 'Failed to get AI advice. Please try again.'
    }
  } finally {
    isLoadingAdvice.value = false
  }
}

function clearAdviceError() {
  adviceError.value = ''
}

function clearTradingError() {
  tradingError.value = ''
}

function showTradingError(message: string) {
  tradingError.value = message
  // Auto-clear the error after 5 seconds
  setTimeout(() => {
    if (tradingError.value === message) {
      tradingError.value = ''
    }
  }, 5000)
}

function getAdviceActionClass(action: string): string {
  switch (action.toUpperCase()) {
    case 'BUY':
      return 'advice-buy'
    case 'SELL':
      return 'advice-sell'
    case 'HOLD':
      return 'advice-hold'
    default:
      return 'advice-neutral'
  }
}

function getStockTypeOrder(type: string): number {
  // Define order to match UI layout: Popular (left), Volatile (middle), Sector (right)
  switch (type) {
    case 'Popular':
      return 0
    case 'Volatile':
      return 1
    case 'Sector':
      return 2
    default:
      return 999 // Unknown types go to the end
  }
}

function getOrderedAdviceResponse(): object | null {
  if (!lastAdviceResponse.value) return null

  // Create a copy of the response to avoid mutating the original
  const orderedResponse = { ...lastAdviceResponse.value } as any

  // If the response has an advice field that's an array, sort it
  if (orderedResponse.advice && Array.isArray(orderedResponse.advice)) {
    orderedResponse.advice = [...orderedResponse.advice].sort((a: any, b: any) => {
      const stockA = stocks.value.find(s => s.ticker === a.symbol)
      const stockB = stocks.value.find(s => s.ticker === b.symbol)

      const typeOrderA = getStockTypeOrder(stockA?.type || '')
      const typeOrderB = getStockTypeOrder(stockB?.type || '')

      return typeOrderA - typeOrderB
    })
  }

  return orderedResponse
}

async function endGame() {
  // Stop intervals and close connections
  if (dayUpdateInterval) {
    clearInterval(dayUpdateInterval)
    dayUpdateInterval = null
  }
  if (socket) {
    socket.close()
    socket = null
  }
  // Clear WebSocket from store
  store.setWebSocket(null)
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


.active-game-root {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  height: 100vh;
  width: 100vw;
  box-sizing: border-box;
  background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
  color: #ffffff;
  font-family: 'Orbitron', 'Courier New', 'Monaco', monospace;
  overflow: hidden;
}

.main-content {
  flex: 1 1 auto;
  overflow-y: auto;
  padding: 2vw 2vw 0 2vw;
  min-height: 0;
}

.advice-section-fixed {
  flex-shrink: 0;
  width: 100vw;
  background: rgba(0,0,0,0.85);
  box-shadow: 0 -2px 16px rgba(0,0,0,0.12);
  border-top: 1px solid #222;
  z-index: 10;
}

.advice-section {
  margin: 0 auto;
  max-width: 1800px;
  border-radius: 15px;
  padding: 1.5rem 2vw 1rem 2vw;
  border: 2px solid rgba(0, 245, 255, 0.3);
  background: rgba(255,255,255,0.05);
}

@media (max-width: 900px) {
  .advice-section {
    padding: 1rem 1vw 0.5rem 1vw;
  }
}

/* Remove duplicated .active-game-container and .advice-section styles below */

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
  gap: 2vw;
  margin-bottom: 2vw;
  width: 100%;
  max-width: 1800px;
  box-sizing: border-box;
  justify-items: center;
}

@media (min-width: 1200px) {
  .charts-container {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (min-width: 768px) and (max-width: 1199px) {
  .charts-container {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}


.chart-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 15px;
  padding: 2vw 1.5vw;
  border: 2px solid;
  transition: all 0.3s ease;
  min-height: 40vh;
  min-width: 280px;
  max-width: 98vw;
  width: 100%;
  box-sizing: border-box;
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

.trade-input-section {
  margin-bottom: 0.75rem;
}

.trade-input-group {
  margin-bottom: 0.5rem;
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

.input-with-buttons {
  display: flex;
  gap: 0.5rem;
  align-items: flex-start;
}

.quantity-input {
  flex: 1;
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

.max-buttons {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.max-btn {
  padding: 0.25rem 0.5rem;
  border: none;
  border-radius: 3px;
  font-size: 0.7rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: 'Orbitron', monospace;
  white-space: nowrap;
}

.buy-max {
  background: rgba(46, 213, 115, 0.8);
  color: white;
  border: 1px solid rgba(46, 213, 115, 0.5);
}

.buy-max:hover {
  background: rgba(46, 213, 115, 1);
  transform: translateY(-1px);
}

.sell-max {
  background: rgba(255, 107, 107, 0.8);
  color: white;
  border: 1px solid rgba(255, 107, 107, 0.5);
}

.sell-max:hover {
  background: rgba(255, 107, 107, 1);
  transform: translateY(-1px);
}

.trade-hints {
  display: flex;
  gap: 1rem;
  margin-top: 0.5rem;
  font-size: 0.75rem;
  flex-wrap: wrap;
}

.buy-hint,
.sell-hint {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.buy-hint {
  border-color: rgba(46, 213, 115, 0.3);
  background: rgba(46, 213, 115, 0.1);
}

.sell-hint {
  border-color: rgba(255, 107, 107, 0.3);
  background: rgba(255, 107, 107, 0.1);
}

.no-trade-hint {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #999;
  font-style: italic;
}

.hint-label {
  color: #cccccc;
  font-weight: 500;
}

.hint-value {
  color: #00f5ff;
  font-weight: 600;
  font-family: 'Orbitron', monospace;
}

.hint-text {
  color: #999;
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
  height: 28vh;
  min-height: 180px;
  max-height: 350px;
  position: relative;
}

.plotly-chart {
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
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

/* AI Trading Advice Styles */
.advice-section {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 15px;
  padding: 1.5rem;
  margin: 2rem 0;
  border: 2px solid rgba(0, 245, 255, 0.3);
}

.advice-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.advice-controls {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.advice-header h3 {
  font-size: 1.5rem;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 2px;
  color: #00f5ff;
  margin: 0;
  text-shadow: 0 0 15px rgba(0, 245, 255, 0.3);
}

.advice-btn {
  background: linear-gradient(135deg, #00f5ff 0%, #0084ff 100%);
  border: none;
  color: white;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: 'Orbitron', 'Courier New', monospace;
  position: relative;
  overflow: hidden;
}

.advice-btn.test-btn {
  background: linear-gradient(135deg, #a55eea 0%, #8854d0 100%);
}

.advice-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(0, 245, 255, 0.4);
}

.advice-btn.test-btn:hover:not(:disabled) {
  box-shadow: 0 10px 25px rgba(165, 94, 234, 0.4);
}

.advice-debug {
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(165, 94, 234, 0.3);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1.5rem;
  font-size: 0.9rem;
}

.advice-debug h5 {
  color: #a55eea;
  font-weight: 700;
  margin: 0 0 1rem 0;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.advice-debug .debug-item {
  margin-bottom: 0.75rem;
}

.advice-debug .debug-item strong {
  color: #a55eea;
  display: inline-block;
  min-width: 120px;
}

.advice-debug pre {
  background: rgba(0, 0, 0, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  padding: 0.5rem;
  font-size: 0.8rem;
  color: #cccccc;
  overflow-x: auto;
  max-height: 200px;
  margin: 0.5rem 0 0 0;
}

.advice-btn:disabled {
  background: #555;
  color: #999;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.advice-loading {
  text-align: center;
  padding: 2rem;
  color: #cccccc;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(0, 245, 255, 0.3);
  border-top: 4px solid #00f5ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.advice-error {
  background: rgba(255, 107, 107, 0.1);
  border: 1px solid rgba(255, 107, 107, 0.3);
  border-radius: 8px;
  padding: 1rem;
  margin: 1rem 0;
  text-align: center;
}

.advice-error p {
  color: #ff6b6b;
  margin: 0 0 0.5rem;
  font-weight: 600;
}

.clear-error-btn {
  background: rgba(255, 107, 107, 0.2);
  border: 1px solid rgba(255, 107, 107, 0.5);
  color: #ff6b6b;
  padding: 0.5rem 1rem;
  border-radius: 5px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  transition: all 0.3s ease;
}

.clear-error-btn:hover {
  background: rgba(255, 107, 107, 0.3);
}

.advice-results h4 {
  color: #00f5ff;
  font-size: 1.2rem;
  font-weight: 700;
  margin-bottom: 1rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.advice-cards {
  display: grid;
  gap: 1rem;
  margin-bottom: 1rem;
}

@media (min-width: 768px) {
  .advice-cards {
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  }
}

.advice-card {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 10px;
  padding: 1rem;
  border: 2px solid;
  transition: all 0.3s ease;
}

.advice-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
}

.advice-buy {
  border-color: #2ed573;
  background: linear-gradient(145deg, rgba(46, 213, 115, 0.1), rgba(46, 213, 115, 0.05));
}

.advice-sell {
  border-color: #ff6b6b;
  background: linear-gradient(145deg, rgba(255, 107, 107, 0.1), rgba(255, 107, 107, 0.05));
}

.advice-hold {
  border-color: #ffd700;
  background: linear-gradient(145deg, rgba(255, 215, 0, 0.1), rgba(255, 215, 0, 0.05));
}

.advice-neutral {
  border-color: #cccccc;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
}

.advice-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.stock-symbol {
  font-size: 1.1rem;
  font-weight: 900;
  color: #00f5ff;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.advice-action {
  padding: 0.25rem 0.75rem;
  border-radius: 15px;
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.advice-action.advice-buy {
  background: #2ed573;
  color: white;
}

.advice-action.advice-sell {
  background: #ff6b6b;
  color: white;
}

.advice-action.advice-hold {
  background: #ffd700;
  color: #333;
}

.advice-reason {
  color: #cccccc;
  font-size: 0.9rem;
  line-height: 1.4;
  margin-bottom: 0.5rem;
}

.current-position {
  color: #00f5ff;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.advice-disclaimer {
  text-align: center;
  padding: 1rem;
  background: rgba(255, 215, 0, 0.1);
  border: 1px solid rgba(255, 215, 0, 0.3);
  border-radius: 8px;
  margin-top: 1rem;
}

.advice-disclaimer small {
  color: #ffd700;
  font-size: 0.8rem;
  font-weight: 600;
}

/* Responsive design */
@media (max-width: 768px) {
  .active-game-container {
    padding: 2vw 1vw;
  }

  .active-game-container h2 {
    font-size: 1.5rem;
  }

  .game-info {
    gap: 1vw;
  }

  .session-info,
  .date-info,
  .player-info,
  .cash-info,
  .portfolio-info {
    padding: 0.5rem 0.5rem;
    font-size: 0.9rem;
  }

  .chart-card {
    padding: 1vw;
    min-height: 30vh;
  }

  .chart-wrapper {
    height: 18vh;
    min-height: 120px;
  }

  .advice-header {
    flex-direction: column;
    align-items: stretch;
  }

  .advice-header h3 {
    text-align: center;
    margin-bottom: 1rem;
  }

  .advice-btn {
    width: 100%;
  }

  .advice-cards {
    grid-template-columns: 1fr;
  }
}

/* Trading Error Banner Styles */
.trading-error-banner {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  max-width: 500px;
  width: 90%;
  animation: slideDown 0.3s ease-out;
}

.error-content {
  background: linear-gradient(135deg, #ff6b6b, #ffa06b);
  color: white;
  padding: 1rem 1.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(255, 107, 107, 0.3);
  display: flex;
  align-items: center;
  gap: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.error-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.error-message {
  flex: 1;
  font-weight: 500;
  line-height: 1.4;
}

.close-error-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 18px;
  flex-shrink: 0;
  transition: background-color 0.2s ease;
}

.close-error-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

/* Responsive styles for mobile devices */
@media (max-width: 768px) {
  .input-with-buttons {
    flex-direction: column;
    gap: 0.5rem;
  }

  .max-buttons {
    flex-direction: row;
    justify-content: center;
  }

  .trade-hints {
    flex-direction: column;
    gap: 0.5rem;
  }

  .buy-hint,
  .sell-hint,
  .no-trade-hint {
    justify-content: center;
    text-align: center;
  }

  .trade-buttons {
    gap: 0.75rem;
  }

  .buy-btn,
  .sell-btn {
    padding: 0.75rem 1rem;
    font-size: 0.9rem;
  }
}

@media (max-width: 480px) {
  .trading-controls {
    padding: 0.75rem;
  }

  .max-btn {
    padding: 0.3rem 0.6rem;
    font-size: 0.65rem;
  }

  .trade-hints {
    font-size: 0.7rem;
  }

  .quantity-input {
    font-size: 0.85rem;
    padding: 0.6rem;
  }
}
</style>
