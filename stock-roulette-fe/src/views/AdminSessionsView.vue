<template>
  <div class="sessions-overview">
    <div class="page-header">
      <h2>Sessions Overview</h2>
      <button @click="refreshSessions" class="refresh-btn" :disabled="loading">
        {{ loading ? 'Loading...' : 'Refresh' }}
      </button>
    </div>

    <!-- Filters -->
    <div class="filters-section">
      <div class="filters">
        <div class="filter-group">
          <label for="player-filter">Player Name</label>
          <input
            id="player-filter"
            v-model="filters.player"
            type="text"
            placeholder="Search by player name..."
          />
        </div>

        <div class="filter-group">
          <label for="status-filter">Status</label>
          <select id="status-filter" v-model="filters.status">
            <option value="all">All</option>
            <option value="active">Active</option>
            <option value="ended">Ended</option>
            <option value="finished">Finished</option>
          </select>
        </div>

        <div class="filter-group">
          <label for="date-from">Date From</label>
          <input id="date-from" v-model="filters.dateFrom" type="date" />
        </div>

        <div class="filter-group">
          <label for="date-to">Date To</label>
          <input id="date-to" v-model="filters.dateTo" type="date" />
        </div>

        <button @click="clearFilters" class="clear-filters-btn">Clear Filters</button>
      </div>
    </div>

    <!-- Sessions Table -->
    <div class="table-container">
      <div v-if="filteredSessions.length === 0" class="no-data">
        <p>No sessions found matching your criteria</p>
      </div>

      <table v-else class="sessions-table">
        <thead>
          <tr>
            <th>Session ID</th>
            <th>Player Name</th>
            <th>Date</th>
            <th>Status</th>
            <th>Balance</th>
            <th>Score</th>
            <th>Total Profit</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="session in filteredSessions" :key="session.session_id">
            <td>
              <code class="session-id">{{ session.session_id.substring(0, 8) }}...</code>
            </td>
            <td class="player-name">{{ session.player_nickname }}</td>
            <td>{{ formatDate(session.started_at) }}</td>
            <td>
              <span class="status-badge" :class="session.status">
                {{ session.status }}
              </span>
            </td>
            <td>
              <div class="balance-info">
                <span class="balance">${{ session.balance.toLocaleString() }}</span>
              </div>
            </td>
            <td>
              <span v-if="session.total_score" class="score">
                {{ session.total_score.toLocaleString() }}
              </span>
              <span v-else class="no-score">-</span>
            </td>
            <td>
              <span class="total-profit">${{ session.total_profit.toLocaleString() }}</span>
            </td>
            <td>
              <div class="actions">
                <button

                  class="action-btn view-btn"

                >
                  💬
                </button>
                <button
                  @click="resetSession(session.session_id)"
                  class="action-btn reset-btn"
                  title="Reset Session"
                  :disabled="session.status === 'finished'"
                >
                  🔄
                </button>
                <button
                  @click="archiveSession(session.session_id)"
                  class="action-btn archive-btn"
                  title="Archive Session"
                  :disabled="session.status === 'finished'"
                >
                  📁
                </button>
                <button
                  @click="deleteSession(session.session_id)"
                  class="action-btn delete-btn"
                  title="Delete Session"
                >
                  🗑️
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Confirmation Modal -->
    <div v-if="showConfirmModal" class="modal-overlay" @click="closeConfirmModal">
      <div class="modal-content" @click.stop>
        <h3>{{ confirmAction.title }}</h3>
        <p>{{ confirmAction.message }}</p>

        <div class="modal-actions">
          <button @click="closeConfirmModal" class="cancel-btn">Cancel</button>
          <button @click="executeAction" class="confirm-btn" :class="confirmAction.type">
            {{ confirmAction.confirmText }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAdminStore } from '@/stores/adminStore'

const router = useRouter()
const adminStore = useAdminStore()

const showConfirmModal = ref(false)
const confirmAction = ref({
  title: '',
  message: '',
  confirmText: '',
  type: '',
  action: () => {},
})

const filters = ref({
  player: '',
  status: 'all' as 'all' | 'active' | 'ended' | 'finished',
  dateFrom: '',
  dateTo: '',
})

const loading = computed(() => adminStore.loading)
const filteredSessions = computed(() => adminStore.filteredSessions)

// Watch filters and update store
watch(
  filters,
  (newFilters) => {
    adminStore.setSessionFilters(newFilters)
  },
  { deep: true },
)

onMounted(async () => {
  await adminStore.fetchSessions()
})

const refreshSessions = async () => {
  await adminStore.fetchSessions()
}

const clearFilters = () => {
  filters.value = {
    player: '',
    status: 'all',
    dateFrom: '',
    dateTo: '',
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString()
}



const resetSession = (sessionId: string) => {
  confirmAction.value = {
    title: 'Reset Session',
    message: 'Are you sure you want to reset this session? This will clear all progress.',
    confirmText: 'Reset',
    type: 'reset',
    action: async () => {
      await adminStore.resetSession(sessionId)
      closeConfirmModal()
    },
  }
  showConfirmModal.value = true
}

const archiveSession = (sessionId: string) => {
  confirmAction.value = {
    title: 'Archive Session',
    message: 'Are you sure you want to archive this session?',
    confirmText: 'Archive',
    type: 'archive',
    action: async () => {
      await adminStore.archiveSession(sessionId)
      closeConfirmModal()
    },
  }
  showConfirmModal.value = true
}

const deleteSession = (sessionId: string) => {
  confirmAction.value = {
    title: 'Delete Session',
    message:
      'Are you sure you want to permanently delete this session? This action cannot be undone.',
    confirmText: 'Delete',
    type: 'delete',
    action: async () => {
      await adminStore.deleteSession(sessionId)
      closeConfirmModal()
    },
  }
  showConfirmModal.value = true
}

const closeConfirmModal = () => {
  showConfirmModal.value = false
}

const executeAction = async () => {
  await confirmAction.value.action()
}
</script>

<style scoped>
.sessions-overview {
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

.refresh-btn {
  padding: 0.5rem 1rem;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background-color: #0056b3;
}

.refresh-btn:disabled {
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

.filter-group input,
.filter-group select {
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 0.9rem;
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

.table-container {
  overflow-x: auto;
}

.no-data {
  text-align: center;
  padding: 3rem;
  color: #6c757d;
}

.sessions-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 800px;
}

.sessions-table th,
.sessions-table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #dee2e6;
  vertical-align: top;
}

.sessions-table th {
  background-color: #f8f9fa;
  font-weight: 600;
  color: #495057;
  position: sticky;
  top: 0;
}

.session-id {
  background-color: #e9ecef;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.8rem;
}

.player-name {
  font-weight: 500;
}

.status-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
  text-transform: uppercase;
}

.status-badge.active {
  background-color: #d1ecf1;
  color: #0c5460;
}

.status-badge.completed {
  background-color: #d4edda;
  color: #155724;
}

.status-badge.archived {
  background-color: #e2e3e5;
  color: #383d41;
}

.stocks-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.stock-tag {
  background-color: #007bff;
  color: white;
  padding: 0.125rem 0.375rem;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 500;
}

.score {
  font-weight: 600;
  color: #28a745;
}

.portfolio-value {
  font-weight: 600;
  color: #007bff;
}

.no-score,
.no-value {
  color: #6c757d;
  font-style: italic;
}

.actions {
  display: flex;
  gap: 0.25rem;
}

.action-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.view-btn {
  background-color: #17a2b8;
}

.view-btn:hover {
  background-color: #138496;
}

.reset-btn {
  background-color: #ffc107;
}

.reset-btn:hover:not(:disabled) {
  background-color: #e0a800;
}

.archive-btn {
  background-color: #6c757d;
}

.archive-btn:hover:not(:disabled) {
  background-color: #545b62;
}

.delete-btn {
  background-color: #dc3545;
}

.delete-btn:hover {
  background-color: #c82333;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Modal Styles */
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

.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  max-width: 400px;
  width: 90%;
}

.modal-content h3 {
  margin: 0 0 1rem 0;
  color: #333;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.5rem;
}

.cancel-btn,
.confirm-btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.cancel-btn {
  background-color: #6c757d;
  color: white;
}

.cancel-btn:hover {
  background-color: #545b62;
}

.confirm-btn.reset {
  background-color: #ffc107;
  color: #212529;
}

.confirm-btn.reset:hover {
  background-color: #e0a800;
}

.confirm-btn.archive {
  background-color: #6c757d;
  color: white;
}

.confirm-btn.archive:hover {
  background-color: #545b62;
}

.confirm-btn.delete {
  background-color: #dc3545;
  color: white;
}

.confirm-btn.delete:hover {
  background-color: #c82333;
}
</style>
