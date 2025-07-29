<template>
  <div class="admin-dashboard">
    <header class="admin-header">
      <div class="header-content">
        <h1>Admin Dashboard</h1>
        <div class="header-actions">
          <button @click="exportData" class="export-btn">Export Data</button>
          <button @click="logout" class="logout-btn">Logout</button>
        </div>
      </div>
    </header>

    <nav class="admin-nav">
      <router-link to="/admin/sessions" class="nav-item" active-class="active">
        Sessions Overview
      </router-link>
      <router-link to="/admin/leaderboard" class="nav-item" active-class="active">
        Leaderboard
      </router-link>
      <router-link to="/admin/chat-logs" class="nav-item" active-class="active">
        Chat Logs
      </router-link>
    </nav>

    <main class="admin-content">
      <router-view />
    </main>

    <!-- Export Modal -->
    <div v-if="showExportModal" class="modal-overlay" @click="showExportModal = false">
      <div class="modal-content" @click.stop>
        <h3>Export Data</h3>
        <p>Choose what data to export:</p>

        <div class="export-options">
          <button @click="handleExport('sessions')" class="export-option">Sessions Data</button>
          <button @click="handleExport('logs')" class="export-option">Chat Logs</button>
          <button @click="handleExport('all')" class="export-option">All Data</button>
        </div>

        <div class="modal-actions">
          <button @click="showExportModal = false" class="cancel-btn">Cancel</button>
        </div>
      </div>
    </div>

    <!-- Loading Spinner -->
    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
    </div>

    <!-- Error Toast -->
    <div v-if="error" class="error-toast">
      <p>{{ error }}</p>
      <button @click="clearError" class="close-btn">&times;</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAdminStore } from '@/stores/adminStore'

const router = useRouter()
const adminStore = useAdminStore()

const showExportModal = ref(false)

const loading = computed(() => adminStore.loading)
const error = computed(() => adminStore.error)

onMounted(() => {
  // Check authentication
  adminStore.checkAuth()
  if (!adminStore.isAuthenticated) {
    router.push('/admin/login')
  }
})

const logout = () => {
  adminStore.logout()
  router.push('/admin/login')
}

const exportData = () => {
  showExportModal.value = true
}

const handleExport = async (type: 'sessions' | 'logs' | 'all') => {
  await adminStore.exportData(type)
  showExportModal.value = false
}

const clearError = () => {
  adminStore.clearError()
}
</script>

<style scoped>
.admin-dashboard {
  min-height: 100vh;
  background-color: #f8f9fa;
}

.admin-header {
  background: white;
  border-bottom: 1px solid #dee2e6;
  padding: 1rem 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h1 {
  margin: 0;
  color: #333;
  font-size: 1.8rem;
}

.header-actions {
  display: flex;
  gap: 1rem;
}

.export-btn,
.logout-btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.export-btn {
  background-color: #007bff;
  color: white;
}

.export-btn:hover {
  background-color: #0056b3;
}

.logout-btn {
  background-color: #6c757d;
  color: white;
}

.logout-btn:hover {
  background-color: #545b62;
}

.admin-nav {
  background: white;
  border-bottom: 1px solid #dee2e6;
  padding: 0;
}

.admin-nav {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  padding: 0 1rem;
}

.nav-item {
  padding: 1rem 1.5rem;
  text-decoration: none;
  color: #6c757d;
  font-weight: 500;
  border-bottom: 3px solid transparent;
  transition: all 0.2s;
}

.nav-item:hover {
  color: #007bff;
  background-color: #f8f9fa;
}

.nav-item.active {
  color: #007bff;
  border-bottom-color: #007bff;
}

.admin-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1rem;
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

.export-options {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin: 1rem 0;
}

.export-option {
  padding: 0.75rem;
  border: 2px solid #dee2e6;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.export-option:hover {
  border-color: #007bff;
  background-color: #f8f9fa;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 1.5rem;
}

.cancel-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #6c757d;
  border-radius: 6px;
  background: white;
  color: #6c757d;
  cursor: pointer;
  transition: all 0.2s;
}

.cancel-btn:hover {
  background-color: #6c757d;
  color: white;
}

/* Loading Spinner */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

/* Error Toast */
.error-toast {
  position: fixed;
  top: 1rem;
  right: 1rem;
  background-color: #dc3545;
  color: white;
  padding: 1rem;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  display: flex;
  align-items: center;
  gap: 1rem;
  z-index: 1001;
  max-width: 400px;
}

.error-toast p {
  margin: 0;
  flex: 1;
}

.close-btn {
  background: none;
  border: none;
  color: white;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  opacity: 0.8;
}
</style>
