<template>
  <div class="snapshot-details">
    <div class="header">
      <div>
        <router-link to="/zones" class="back-link">← Back to Zones</router-link>
        <h1 v-if="snapshot">Snapshot #{{ snapshot.id }}</h1>
      </div>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <div v-else>
      <div class="snapshot-info">
        <div class="info-grid">
          <div>
            <strong>Zone:</strong>
            <router-link v-if="snapshot.zone_id" :to="`/zones/${snapshot.zone_id}`">
              {{ snapshot.meta_info?.zone_name || `Zone ${snapshot.zone_id}` }}
            </router-link>
          </div>
          <div><strong>Created:</strong> {{ formatDate(snapshot.created_at) }}</div>
          <div><strong>Status:</strong> <span :class="['status-badge', snapshot.status]">{{ snapshot.status }}</span></div>
          <div><strong>Records:</strong> {{ snapshot.record_count }}</div>
        </div>
      </div>

      <div id="export" class="export-section">
        <h2>Export Snapshot</h2>
        <div class="export-controls">
          <select v-model="exportFormat">
            <option value="bind">BIND Zone File</option>
            <option value="terraform_aws">Terraform AWS Route 53</option>
            <option value="terraform_azure">Terraform Azure Private DNS</option>
            <option value="csv">CSV</option>
          </select>
          <button @click="downloadExport" class="btn btn-success">Download</button>
        </div>
      </div>

      <div class="records-section">
        <div class="records-header">
          <h2>DNS Records</h2>
          <div class="filter">
            <select v-model="filterType">
              <option value="">All Types</option>
              <option v-for="type in recordTypes" :key="type" :value="type">{{ type }}</option>
            </select>
          </div>
        </div>

        <div v-if="filteredRecords.length === 0" class="empty">
          No records found.
        </div>

        <table v-else class="records-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Value</th>
              <th>TTL</th>
              <th>Priority</th>
              <th>Comment</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="record in filteredRecords" :key="record.id" :class="{ disabled: record.disabled === 'true' }">
              <td>{{ record.name }}</td>
              <td><span class="record-type">{{ record.record_type }}</span></td>
              <td class="value">{{ record.value }}</td>
              <td>{{ record.ttl || '-' }}</td>
              <td>{{ record.priority || '-' }}</td>
              <td>{{ record.comment || '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { snapshotsAPI, exportsAPI } from '../api/client';

export default {
  name: 'SnapshotDetails',
  props: ['id'],
  data() {
    return {
      snapshot: null,
      records: [],
      loading: true,
      error: null,
      exportFormat: 'bind',
      filterType: '',
    };
  },
  computed: {
    recordTypes() {
      const types = new Set(this.records.map(r => r.record_type));
      return Array.from(types).sort();
    },
    filteredRecords() {
      if (!this.filterType) {
        return this.records;
      }
      return this.records.filter(r => r.record_type === this.filterType);
    },
  },
  mounted() {
    this.loadData();
  },
  methods: {
    async loadData() {
      try {
        this.loading = true;
        this.error = null;
        const [snapshotRes, recordsRes] = await Promise.all([
          snapshotsAPI.get(this.id),
          snapshotsAPI.getRecords(this.id),
        ]);
        this.snapshot = snapshotRes.data;
        this.records = recordsRes.data;
      } catch (err) {
        this.error = `Failed to load data: ${err.message}`;
      } finally {
        this.loading = false;
      }
    },
    async downloadExport() {
      try {
        const response = await exportsAPI.download(this.id, this.exportFormat);
        const blob = new Blob([response.data], { type: response.headers['content-type'] });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;

        // Extract filename from Content-Disposition header
        const contentDisposition = response.headers['content-disposition'];
        let filename = `snapshot_${this.id}_${this.exportFormat}`;
        if (contentDisposition) {
          const matches = /filename="([^"]+)"/.exec(contentDisposition);
          if (matches && matches[1]) {
            filename = matches[1];
          }
        }

        link.setAttribute('download', filename);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      } catch (err) {
        alert(`Failed to export: ${err.message}`);
      }
    },
    formatDate(dateString) {
      return new Date(dateString).toLocaleString();
    },
  },
};
</script>

<style scoped>
.snapshot-details {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

.header {
  margin-bottom: 2rem;
}

.back-link {
  color: #42b983;
  text-decoration: none;
  display: block;
  margin-bottom: 0.5rem;
}

.snapshot-info {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
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

.export-section {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.export-controls {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.export-controls select {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.records-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.filter select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.records-table {
  width: 100%;
  background: white;
  border-collapse: collapse;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.records-table th {
  background: #f5f5f5;
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  border-bottom: 2px solid #e0e0e0;
}

.records-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #f0f0f0;
}

.records-table tr:hover {
  background: #fafafa;
}

.records-table tr.disabled {
  opacity: 0.5;
  background: #fff3cd;
}

.record-type {
  background: #e3f2fd;
  color: #1976d2;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 600;
}

.value {
  max-width: 400px;
  word-break: break-all;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.3s;
}

.btn-success {
  background: #4caf50;
  color: white;
}

.btn-success:hover {
  background: #45a049;
}

.loading,
.error,
.empty {
  text-align: center;
  padding: 2rem;
  color: #666;
}
</style>
