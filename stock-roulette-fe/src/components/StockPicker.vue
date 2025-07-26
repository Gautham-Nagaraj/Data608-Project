<template>
  <div class="picker">
    <div class="stock" v-for="stock in availableStocks" :key="stock">
      <label>
        <input
          type="checkbox"
          :value="stock"
          v-model="selectedStocks"
          :disabled="selectedStocks.length >= 3 && !selectedStocks.includes(stock)"
        />
        {{ stock }}
      </label>
    </div>

    <button @click="submitSelection" :disabled="selectedStocks.length !== 3">
      Submit 3 Stocks
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, defineProps, defineEmits } from 'vue'

const props = defineProps<{
  availableStocks: string[]
}>()

const emit = defineEmits<{
  (e: 'submit', value: string[]): void
}>()

const selectedStocks = ref<string[]>([])

function submitSelection() {
  emit('submit', selectedStocks.value)
}
</script>

<style scoped>
.picker {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.stock {
  min-width: 80px;
  text-align: center;
}

button {
  padding: 0.5rem 1rem;
  font-weight: bold;
}
</style>
