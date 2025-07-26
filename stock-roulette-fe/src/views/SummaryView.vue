<template>
  <div class="summary-container">
    <h2>Game Summary</h2>

    <div>
      <h3>🧾 Selected Stocks:</h3>
      <ul>
        <li v-for="ticker in store.selectedStocks" :key="ticker">
          {{ ticker }}
        </li>
      </ul>
    </div>

    <div v-if="store.gameResult">
      <h3>📊 Final Results</h3>
      <pre>{{ store.gameResult }}</pre>
    </div>
    <div v-else>
      <p>Results not available yet. Please check back later.</p>
    </div>

    <router-link to="/game">
      <button>Play Again</button>
    </router-link>
  </div>
</template>

<script setup lang="ts">
import { useSessionStore } from '@/stores/sessionStore'
const store = useSessionStore()
</script>

<style scoped>
.summary-container {
  max-width: 600px;
  margin: 0 auto;
  text-align: center;
}
</style>
