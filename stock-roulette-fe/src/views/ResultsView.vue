<template>
  <div class="results-container">
    <h2>🎮 Game Results</h2>

    <div v-if="gameResult" class="results-content">
      <div class="score-display">
        <h3>🏆 Final Score</h3>
        <div class="total-score">
          ${{
            typeof gameResult.total_score === 'number' ? gameResult.total_score.toFixed(2) : '0.00'
          }}
        </div>
      </div>

      <div class="details-section">
        <h4>📊 Game Details</h4>
        <div class="details-grid">
          <div class="detail-item" v-if="gameResult.session_id">
            <span class="label">Session ID:</span>
            <span class="value">{{ gameResult.session_id }}</span>
          </div>
          <div class="detail-item" v-if="gameResult.player_name">
            <span class="label">Player:</span>
            <span class="value">{{ gameResult.player_name }}</span>
          </div>
          <div class="detail-item" v-if="gameResult.final_cash">
            <span class="label">Final Cash:</span>
            <span class="value"
              >${{
                typeof gameResult.final_cash === 'number'
                  ? gameResult.final_cash.toFixed(2)
                  : '0.00'
              }}</span
            >
          </div>
          <div class="detail-item" v-if="gameResult.portfolio_value">
            <span class="label">Portfolio Value:</span>
            <span class="value"
              >${{
                typeof gameResult.portfolio_value === 'number'
                  ? gameResult.portfolio_value.toFixed(2)
                  : '0.00'
              }}</span
            >
          </div>
        </div>
      </div>

      <div class="raw-data-section">
        <h4>🔍 Raw Data</h4>
        <pre class="raw-data">{{ gameResult }}</pre>
      </div>
    </div>

    <div v-else class="no-results">
      <p>No game results available.</p>
    </div>

    <div class="actions">
      <button @click="playAgain" class="play-again-btn">Play Again</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useSessionStore } from '@/stores/sessionStore'

const router = useRouter()
const store = useSessionStore()
const gameResult = store.gameResult

function playAgain() {
  // Clear the session data and navigate to home
  store.setGameResult(null)
  store.setSessionId('')
  store.setSelectedStocks([])
  store.setGameData(null)
  router.push('/')
}
</script>

<style scoped>
.results-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
  color: #ffffff;
  padding: 2rem;
  font-family: 'Orbitron', 'Courier New', 'Monaco', monospace;
}

.results-container h2 {
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

.results-content {
  max-width: 800px;
  margin: 0 auto;
}

.score-display {
  text-align: center;
  background: rgba(255, 255, 255, 0.05);
  border: 2px solid #ffd700;
  border-radius: 15px;
  padding: 2rem;
  margin-bottom: 2rem;
  background: linear-gradient(145deg, rgba(255, 215, 0, 0.1), rgba(255, 140, 0, 0.05));
}

.score-display h3 {
  color: #ffd700;
  font-size: 1.5rem;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 2px;
  margin-bottom: 1rem;
}

.total-score {
  font-size: 3rem;
  font-weight: 900;
  color: #00f5ff;
  text-shadow: 0 0 20px rgba(0, 245, 255, 0.5);
  letter-spacing: 2px;
}

.details-section {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(0, 245, 255, 0.3);
  border-radius: 15px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.details-section h4 {
  color: #00f5ff;
  font-size: 1.2rem;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 1rem;
  text-align: center;
}

.details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(0, 0, 0, 0.2);
  padding: 0.75rem;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.detail-item .label {
  color: #cccccc;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-item .value {
  color: #00f5ff;
  font-weight: 700;
}

.raw-data-section {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.raw-data-section h4 {
  color: #cccccc;
  font-size: 1rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 1rem;
  text-align: center;
}

.raw-data {
  background: rgba(0, 0, 0, 0.4);
  color: #cccccc;
  padding: 1rem;
  border-radius: 8px;
  font-size: 0.8rem;
  font-family: 'Courier New', monospace;
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.no-results {
  text-align: center;
  background: rgba(255, 107, 107, 0.1);
  border: 1px solid rgba(255, 107, 107, 0.3);
  border-radius: 15px;
  padding: 2rem;
  color: #ff6b6b;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.actions {
  text-align: center;
  margin-top: 2rem;
}

.play-again-btn {
  background: linear-gradient(135deg, #2ed573 0%, #26d063 100%);
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

.play-again-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(46, 213, 115, 0.4);
}

.play-again-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.play-again-btn:hover::before {
  left: 100%;
}

/* Responsive design */
@media (max-width: 768px) {
  .results-container {
    padding: 1rem;
  }

  .results-container h2 {
    font-size: 1.8rem;
  }

  .total-score {
    font-size: 2rem;
  }

  .details-grid {
    grid-template-columns: 1fr;
  }

  .detail-item {
    flex-direction: column;
    gap: 0.5rem;
    text-align: center;
  }
}
</style>
