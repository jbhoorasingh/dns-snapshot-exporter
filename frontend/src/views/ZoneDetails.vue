<template>
  <div class="zone-details">
    <div class="header">
      <div>
        <router-link to="/zones" class="back-link">← Back to Zones</router-link>
        <h1 v-if="zone">{{ zone.name }}</h1>
      </div>
      <button @click="createSnapshot" class="btn btn-success">Take Snapshot</button>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <div v-else>
      <div class="zone-info">
        <p v-if="zone.description">{{ zone.description }}</p>
        <div class="meta">
          <span>Provider: <strong>{{ zone.provider }}</strong></span>
          <span>Status: <strong>{{ zone.enabled ? 'Enabled' : 'Disabled' }}</strong></span>
          <span>Created: <strong>{{ formatDate(zone.created_at) }}</strong></span>
        </div>
      </div>

      <h2>Snapshots</h2>
      <div v-if="snapshots.length === 0" class="empty">
        No snapshots yet. Take your first snapshot to get started!
      </div>

      <div v-else class="snapshots-list">
        <div v-for="snapshot in snapshots" :key="snapshot.id" class="snapshot-card">
          <div class="snapshot-info">
            <h3>Snapshot #{{ snapshot.id }}</h3>
            <div class="snapshot-meta">
              <span>{{ formatDate(snapshot.created_at) }}</span>
              <span :class="['status-badge', snapshot.status]">{{ snapshot.status }}</span>
              <span v-if="snapshot.record_count">{{ snapshot.record_count }} records</span>
            </div>
            <p v-if="snapshot.error_message" class="error-message">{{ snapshot.error_message }}</p>
          </div>
          <div class="snapshot-actions">
            <router-link :to="`/snapshots/${snapshot.id}`" class="btn btn-sm">View Records</router-link>
            <button @click="exportSnapshot(snapshot.id)" class="btn btn-sm btn-primary">Export</button>
            <button @click="deleteSnapshot(snapshot.id)" class="btn btn-sm btn-danger">Delete</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { zonesAPI, snapshotsAPI } from '../api/client';

export default {
  name: 'ZoneDetails',
  props: ['id'],
  data() {
    return {
      zone: null,
      snapshots: [],
      loading: true,
      error: null,
    };
  },
  mounted() {
    this.loadData();
  },
  methods: {
    async loadData() {
      try {
        this.loading = true;
        this.error = null;
        const [zoneRes, snapshotsRes] = await Promise.all([
          zonesAPI.get(this.id),
          snapshotsAPI.listForZone(this.id),
        ]);
        this.zone = zoneRes.data;
        this.snapshots = snapshotsRes.data;
      } catch (err) {
        this.error = `Failed to load data: ${err.message}`;
      } finally {
        this.loading = false;
      }
    },
    async createSnapshot() {
      try {
        await snapshotsAPI.create(this.id);
        alert('Snapshot created successfully!');
        await this.loadData();
      } catch (err) {
        alert(`Failed to create snapshot: ${err.message}`);
      }
    },
    async deleteSnapshot(snapshotId) {
      if (!confirm('Are you sure you want to delete this snapshot?')) {
        return;
      }
      try {
        await snapshotsAPI.delete(snapshotId);
        await this.loadData();
      } catch (err) {
        alert(`Failed to delete snapshot: ${err.message}`);
      }
    },
    exportSnapshot(snapshotId) {
      this.$router.push(`/snapshots/${snapshotId}#export`);
    },
    formatDate(dateString) {
      return new Date(dateString).toLocaleString();
    },
  },
};
</script>

<style scoped>
.zone-details {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
}

.back-link {
  color: #42b983;
  text-decoration: none;
  display: block;
  margin-bottom: 0.5rem;
}

.back-link:hover {
  text-decoration: underline;
}

.zone-info {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.meta {
  display: flex;
  gap: 2rem;
  margin-top: 1rem;
  color: #666;
}

.snapshot-card {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.snapshot-info h3 {
  margin: 0 0 0.5rem 0;
}

.snapshot-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.875rem;
  color: #666;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-weight: 600;
}

.status-badge.success {
  background: #e8f5e9;
  color: #2e7d32;
}

.status-badge.failed {
  background: #ffebee;
  color: #c62828;
}

.status-badge.in_progress {
  background: #fff3e0;
  color: #ef6c00;
}

.error-message {
  color: #f44336;
  font-size: 0.875rem;
  margin-top: 0.5rem;
}

.snapshot-actions {
  display: flex;
  gap: 0.5rem;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  text-decoration: none;
  display: inline-block;
  transition: background 0.3s;
}

.btn-success {
  background: #4caf50;
  color: white;
}

.btn-primary {
  background: #42b983;
  color: white;
}

.btn-danger {
  background: #f44336;
  color: white;
}

.btn-sm {
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
  background: #e0e0e0;
  color: #333;
}

.loading,
.error,
.empty {
  text-align: center;
  padding: 2rem;
  color: #666;
}
</style>
