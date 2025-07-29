<template>
  <div class="error-boundary">
    <div class="error-content">
      <div class="error-icon">⚠️</div>
      <h2>Something went wrong</h2>
      <p>{{ message }}</p>
      <div class="error-actions">
        <button @click="retry" class="retry-btn">Try Again</button>
        <button @click="goHome" class="home-btn">Go to Home</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

interface Props {
  message?: string
}

withDefaults(defineProps<Props>(), {
  message: 'An unexpected error occurred. Please try again.',
})

const emit = defineEmits<{
  retry: []
}>()

const router = useRouter()

const retry = () => {
  emit('retry')
}

const goHome = () => {
  router.push('/')
}
</script>

<style scoped>
.error-boundary {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: 2rem;
}

.error-content {
  text-align: center;
  max-width: 500px;
  padding: 2rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.error-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.error-content h2 {
  color: #dc3545;
  margin-bottom: 1rem;
}

.error-content p {
  color: #6c757d;
  margin-bottom: 2rem;
  line-height: 1.5;
}

.error-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.retry-btn,
.home-btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.retry-btn {
  background-color: #007bff;
  color: white;
}

.retry-btn:hover {
  background-color: #0056b3;
}

.home-btn {
  background-color: #6c757d;
  color: white;
}

.home-btn:hover {
  background-color: #545b62;
}
</style>
