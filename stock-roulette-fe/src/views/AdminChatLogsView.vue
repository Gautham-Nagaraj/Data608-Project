<template>
  <div class="chat-logs-view">
    <div class="page-header">
      <h2>AI Agent Chat Logs</h2>
      <div class="header-actions">
        <button @click="refreshChatLogs" class="refresh-btn" :disabled="loading">
          {{ loading ? 'Loading...' : 'Refresh' }}
        </button>
        <button @click="exportChatLogs" class="export-btn" :disabled="loading">Export Logs</button>
      </div>
    </div>

    <!-- Filters -->
    <div class="filters-section">
      <div class="filters">
        <div class="filter-group">
          <label for="session-filter">Session ID</label>
          <input
            id="session-filter"
            v-model="sessionFilter"
            type="text"
            placeholder="Filter by session ID..."
          />
        </div>

        <div class="filter-group">
          <label for="sender-filter">Sender</label>
          <select id="sender-filter" v-model="senderFilter">
            <option value="all">All</option>
            <option value="player">Player</option>
            <option value="agent">AI Agent</option>
          </select>
        </div>

        <div class="filter-group">
          <label for="suggestions-only">AI Suggestions Only</label>
          <input id="suggestions-only" v-model="suggestionsOnly" type="checkbox" />
        </div>

        <button @click="clearFilters" class="clear-filters-btn">Clear Filters</button>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="stats-summary">
      <div class="stat-card">
        <h3>Total Messages</h3>
        <div class="stat-value">{{ filteredChatLogs.length }}</div>
      </div>
      <div class="stat-card">
        <h3>Player Messages</h3>
        <div class="stat-value">{{ playerMessageCount }}</div>
      </div>
      <div class="stat-card">
        <h3>Agent Messages</h3>
        <div class="stat-value">{{ agentMessageCount }}</div>
      </div>
      <div class="stat-card">
        <h3>AI Suggestions</h3>
        <div class="stat-value">{{ aiSuggestionCount }}</div>
      </div>
    </div>

    <!-- Chat Logs -->
    <div class="chat-logs-container">
      <div v-if="filteredChatLogs.length === 0" class="no-data">
        <p>No chat logs found matching your criteria</p>
      </div>

      <div v-else class="chat-logs">
        <div
          v-for="log in filteredChatLogs"
          :key="log.id"
          class="chat-message"
          :class="[log.sender, { 'has-suggestion': log.ai_suggestion }]"
        >
          <div class="message-header">
            <div class="sender-info">
              <span class="sender-badge" :class="log.sender">
                {{ log.sender === 'player' ? '👤' : '🤖' }}
                {{ log.sender === 'player' ? 'Player' : 'AI Agent' }}
              </span>
              <span class="session-id"> Session: {{ log.session_id.substring(0, 8) }}... </span>
            </div>
            <div class="timestamp">
              {{ formatTimestamp(log.timestamp) }}
            </div>
          </div>

          <div class="message-content">
            <div class="message-text">
              {{ log.message }}
            </div>

            <div v-if="log.ai_suggestion" class="ai-suggestion">
              <div class="suggestion-label">
                <span class="icon">💡</span>
                AI Suggestion
              </div>
              <div class="suggestion-content">
                {{ log.ai_suggestion }}
              </div>
            </div>

            <div v-if="log.decision_outcome" class="decision-outcome">
              <div class="outcome-label">
                <span class="icon">📊</span>
                Decision Outcome
              </div>
              <div class="outcome-content">
                {{ log.decision_outcome }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Session Chat Modal -->
    <div v-if="showSessionModal" class="modal-overlay" @click="closeSessionModal">
      <div class="modal-content session-chat-modal" @click.stop>
        <div class="modal-header">
          <h3>Session Chat: {{ selectedSessionId?.substring(0, 8) }}...</h3>
          <button @click="closeSessionModal" class="close-btn">&times;</button>
        </div>

        <div class="session-chat">
          <div
            v-for="message in sessionChatLogs"
            :key="message.id"
            class="session-message"
            :class="message.sender"
          >
            <div class="message-bubble">
              <div class="sender">{{ message.sender }}</div>
              <div class="content">{{ message.message }}</div>
              <div class="time">{{ formatTime(message.timestamp) }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAdminStore } from '@/stores/adminStore'

const route = useRoute()
const adminStore = useAdminStore()

const sessionFilter = ref('')
const senderFilter = ref<'all' | 'player' | 'agent'>('all')
const suggestionsOnly = ref(false)
const showSessionModal = ref(false)
const selectedSessionId = ref<string | null>(null)

const loading = computed(() => adminStore.loading)
const chatLogs = computed(() => adminStore.chatLogs)

const filteredChatLogs = computed(() => {
  let filtered = chatLogs.value

  if (sessionFilter.value) {
    filtered = filtered.filter((log) =>
      log.session_id.toLowerCase().includes(sessionFilter.value.toLowerCase()),
    )
  }

  if (senderFilter.value !== 'all') {
    filtered = filtered.filter((log) => log.sender === senderFilter.value)
  }

  if (suggestionsOnly.value) {
    filtered = filtered.filter((log) => log.ai_suggestion)
  }

  return filtered.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
})

const sessionChatLogs = computed(() => {
  if (!selectedSessionId.value) return []

  return chatLogs.value
    .filter((log) => log.session_id === selectedSessionId.value)
    .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
})

const playerMessageCount = computed(() => {
  return filteredChatLogs.value.filter((log) => log.sender === 'player').length
})

const agentMessageCount = computed(() => {
  return filteredChatLogs.value.filter((log) => log.sender === 'agent').length
})

const aiSuggestionCount = computed(() => {
  return filteredChatLogs.value.filter((log) => log.ai_suggestion).length
})

// Watch for session parameter in route
watch(
  () => route.query.session,
  (sessionId) => {
    if (sessionId && typeof sessionId === 'string') {
      sessionFilter.value = sessionId
    }
  },
  { immediate: true },
)

onMounted(async () => {
  await adminStore.fetchChatLogs()
})

const refreshChatLogs = async () => {
  await adminStore.fetchChatLogs()
}

const exportChatLogs = async () => {
  await adminStore.exportData('logs')
}

const clearFilters = () => {
  sessionFilter.value = ''
  senderFilter.value = 'all'
  suggestionsOnly.value = false
}

const formatTimestamp = (timestamp: string) => {
  const date = new Date(timestamp)
  return date.toLocaleString()
}

const formatTime = (timestamp: string) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString()
}

const closeSessionModal = () => {
  showSessionModal.value = false
  selectedSessionId.value = null
}
</script>

<style scoped>
.chat-logs-view {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #dee2e6;
}

.page-header h2 {
  margin: 0;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 1rem;
}

.refresh-btn,
.export-btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
  font-weight: 500;
}

.refresh-btn {
  background-color: #007bff;
  color: white;
}

.refresh-btn:hover:not(:disabled) {
  background-color: #0056b3;
}

.export-btn {
  background-color: #28a745;
  color: white;
}

.export-btn:hover:not(:disabled) {
  background-color: #218838;
}

.refresh-btn:disabled,
.export-btn:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

.filters-section {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 6px;
}

.filters {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  align-items: end;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.filter-group label {
  font-weight: 500;
  color: #333;
  font-size: 0.9rem;
}

.filter-group input[type='text'],
.filter-group select {
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 0.9rem;
}

.filter-group input[type='checkbox'] {
  width: 20px;
  height: 20px;
  margin-top: 0.5rem;
}

.clear-filters-btn {
  padding: 0.5rem 1rem;
  background-color: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  height: fit-content;
}

.clear-filters-btn:hover {
  background-color: #545b62;
}

.stats-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.stat-card h3 {
  margin: 0 0 0.5rem 0;
  font-size: 0.9rem;
  opacity: 0.9;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
  margin: 0;
}

.chat-logs-container {
  max-height: 600px;
  overflow-y: auto;
  border: 1px solid #dee2e6;
  border-radius: 8px;
}

.no-data {
  text-align: center;
  padding: 3rem;
  color: #6c757d;
}

.chat-logs {
  padding: 1rem;
}

.chat-message {
  margin-bottom: 1.5rem;
  border-radius: 8px;
  padding: 1rem;
  border-left: 4px solid #dee2e6;
  background-color: #f8f9fa;
}

.chat-message.player {
  border-left-color: #007bff;
}

.chat-message.agent {
  border-left-color: #28a745;
}

.chat-message.has-suggestion {
  border-left-color: #ffc107;
  background-color: #fff9e6;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.sender-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.sender-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
  color: white;
}

.sender-badge.player {
  background-color: #007bff;
}

.sender-badge.agent {
  background-color: #28a745;
}

.session-id {
  font-family: monospace;
  font-size: 0.8rem;
  color: #6c757d;
  background-color: #e9ecef;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
}

.timestamp {
  font-size: 0.8rem;
  color: #6c757d;
}

.message-content {
  color: #333;
}

.message-text {
  margin-bottom: 0.75rem;
  line-height: 1.5;
}

.ai-suggestion,
.decision-outcome {
  margin-top: 1rem;
  padding: 1rem;
  border-radius: 6px;
  border: 1px solid #dee2e6;
}

.ai-suggestion {
  background-color: #fff3cd;
  border-color: #ffc107;
}

.decision-outcome {
  background-color: #d1ecf1;
  border-color: #17a2b8;
}

.suggestion-label,
.outcome-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #333;
}

.suggestion-content,
.outcome-content {
  font-style: italic;
  color: #495057;
}

/* Session Chat Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.session-chat-modal {
  width: 90%;
  max-width: 800px;
  height: 80vh;
  background: white;
  border-radius: 8px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #dee2e6;
}

.modal-header h3 {
  margin: 0;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6c757d;
}

.close-btn:hover {
  color: #333;
}

.session-chat {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.session-message {
  display: flex;
}

.session-message.player {
  justify-content: flex-end;
}

.session-message.agent {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 70%;
  padding: 1rem;
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.session-message.player .message-bubble {
  background-color: #007bff;
  color: white;
}

.session-message.agent .message-bubble {
  background-color: #e9ecef;
  color: #333;
}

.message-bubble .sender {
  font-size: 0.8rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
  opacity: 0.8;
}

.message-bubble .content {
  margin-bottom: 0.5rem;
  line-height: 1.4;
}

.message-bubble .time {
  font-size: 0.7rem;
  opacity: 0.7;
}
</style>
