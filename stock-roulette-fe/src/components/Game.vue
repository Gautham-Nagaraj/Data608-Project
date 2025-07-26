<template>
  <div>
    <h1>Stock Roulette</h1>
    <button @click="startSession">Start Game</button>
    <div v-if="sessionId">Session ID: {{ sessionId }}</div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '@/services/api'

const sessionId = ref(null)

async function startSession() {
  const res = await api.post('/start-session')  // Adjust endpoint as needed
  sessionId.value = res.data.session_id
}
</script>
