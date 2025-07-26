<template>
  <div>
    <h2>Game Results</h2>
    <pre>{{ gameResult }}</pre>
  </div>
</template>

<script setup lang="ts">
import { useSessionStore } from '@/stores/sessionStore'
const store = useSessionStore()
const gameResult = store.gameResult
</script>
