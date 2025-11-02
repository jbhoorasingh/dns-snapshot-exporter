<template>
  <div class="zones">
    <div class="header">
      <h1>DNS Zones</h1>
      <button @click="showAddForm = !showAddForm" class="btn btn-primary">
        {{ showAddForm ? 'Cancel' : '+ Add Zone' }}
      </button>
    </div>

    <div v-if="showAddForm" class="add-zone-form">
      <h2>Add New Zone</h2>
      <form @submit.prevent="addZone">
        <div class="form-group">
          <label>Zone Name (FQDN):</label>
          <input v-model="newZone.name" type="text" required placeholder="example.com" />
        </div>
        <div class="form-group">
          <label>Description:</label>
          <input v-model="newZone.description" type="text" placeholder="Optional description" />
        </div>
        <div class="form-group">
          <label>Provider:</label>
          <select v-model="newZone.provider" required>
            <option value="infoblox">Infoblox</option>
            <option value="route53" disabled>AWS Route 53 (coming soon)</option>
            <option value="azure" disabled>Azure Private DNS (coming soon)</option>
          </select>
        </div>
        <button type="submit" class="btn btn-success">Add Zone</button>
      </form>
    </div>

    <div v-if="loading" class="loading">Loading zones...</div>

    <div v-else-if="error" class="error">{{ error }}</div>

    <div v-else class="zones-list">
      <div v-if="zones.length === 0" class="empty">
        No zones found. Add your first zone to get started!
      </div>

      <div v-for="zone in zones" :key="zone.id" class="zone-card">
        <div class="zone-info">
          <h3>{{ zone.name }}</h3>
          <p v-if="zone.description">{{ zone.description }}</p>
          <div class="zone-meta">
            <span class="provider">{{ zone.provider }}</span>
            <span :class="['status', zone.enabled ? 'enabled' : 'disabled']">
              {{ zone.enabled ? 'Enabled' : 'Disabled' }}
            </span>
          </div>
        </div>
        <div class="zone-actions">
          <router-link :to="`/zones/${zone.id}`" class="btn btn-sm">View Details</router-link>
          <button @click="createSnapshot(zone.id)" class="btn btn-sm btn-success">Take Snapshot</button>
          <button @click="toggleZone(zone)" class="btn btn-sm">
            {{ zone.enabled ? 'Disable' : 'Enable' }}
          </button>
          <button @click="deleteZone(zone.id)" class="btn btn-sm btn-danger">Delete</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { zonesAPI, snapshotsAPI } from '../api/client';

export default {
  name: 'Zones',
  data() {
    return {
      zones: [],
      loading: true,
      error: null,
      showAddForm: false,
      newZone: {
        name: '',
        description: '',
        provider: 'infoblox',
        enabled: true,
      },
    };
  },
  mounted() {
    this.loadZones();
  },
  methods: {
    async loadZones() {
      try {
        this.loading = true;
        this.error = null;
        const response = await zonesAPI.list();
        this.zones = response.data;
      } catch (err) {
        this.error = `Failed to load zones: ${err.message}`;
      } finally {
        this.loading = false;
      }
    },
    async addZone() {
      try {
        await zonesAPI.create(this.newZone);
        this.showAddForm = false;
        this.newZone = { name: '', description: '', provider: 'infoblox', enabled: true };
        await this.loadZones();
      } catch (err) {
        alert(`Failed to add zone: ${err.response?.data?.detail || err.message}`);
      }
    },
    async toggleZone(zone) {
      try {
        await zonesAPI.update(zone.id, { enabled: !zone.enabled });
        await this.loadZones();
      } catch (err) {
        alert(`Failed to update zone: ${err.message}`);
      }
    },
    async deleteZone(zoneId) {
      if (!confirm('Are you sure you want to delete this zone and all its snapshots?')) {
        return;
      }
      try {
        await zonesAPI.delete(zoneId);
        await this.loadZones();
      } catch (err) {
        alert(`Failed to delete zone: ${err.message}`);
      }
    },
    async createSnapshot(zoneId) {
      try {
        await snapshotsAPI.create(zoneId);
        alert('Snapshot created successfully!');
        this.$router.push(`/zones/${zoneId}`);
      } catch (err) {
        alert(`Failed to create snapshot: ${err.response?.data?.detail || err.message}`);
      }
    },
  },
};
</script>

<style scoped>
.zones {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.add-zone-form {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 2rem;
  margin-bottom: 2rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.zone-card {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.zone-info h3 {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
}

.zone-meta {
  display: flex;
  gap: 1rem;
  margin-top: 0.5rem;
}

.provider {
  background: #e3f2fd;
  color: #1976d2;
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-size: 0.875rem;
}

.status {
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-size: 0.875rem;
}

.status.enabled {
  background: #e8f5e9;
  color: #2e7d32;
}

.status.disabled {
  background: #ffebee;
  color: #c62828;
}

.zone-actions {
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

.btn-primary {
  background: #42b983;
  color: white;
}

.btn-primary:hover {
  background: #369970;
}

.btn-success {
  background: #4caf50;
  color: white;
}

.btn-success:hover {
  background: #45a049;
}

.btn-danger {
  background: #f44336;
  color: white;
}

.btn-danger:hover {
  background: #da190b;
}

.btn-sm {
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
  background: #e0e0e0;
  color: #333;
}

.btn-sm:hover {
  background: #d0d0d0;
}

.loading,
.error,
.empty {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.error {
  color: #f44336;
}
</style>
