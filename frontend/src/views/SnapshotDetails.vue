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
          <button @click="handleDownload" class="btn btn-success">Download</button>
        </div>
      </div>

      <!-- SOA Configuration Modal -->
      <div v-if="showSOAModal" class="modal-overlay" @click.self="closeSOAModal">
        <div class="modal-content">
          <div class="modal-header">
            <h3>Configure SOA Record for BIND Export</h3>
            <button @click="closeSOAModal" class="btn-close">×</button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label for="mname">Primary Nameserver (MNAME) *</label>
              <input
                v-model="soaConfig.mname"
                id="mname"
                type="text"
                placeholder="ns1.example.com."
                required
              />
              <small>Include trailing dot for absolute names (e.g., ns1.example.com.)</small>
            </div>
            <div class="form-group">
              <label for="rname">Admin Email (RNAME) *</label>
              <input
                v-model="soaConfig.rname"
                id="rname"
                type="text"
                placeholder="admin.example.com."
                required
              />
              <small>Use dot instead of @ and include trailing dot for absolute (e.g., admin.example.com.)</small>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label for="refresh">Refresh (seconds)</label>
                <input v-model.number="soaConfig.refresh" id="refresh" type="number" />
              </div>
              <div class="form-group">
                <label for="retry">Retry (seconds)</label>
                <input v-model.number="soaConfig.retry" id="retry" type="number" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label for="expire">Expire (seconds)</label>
                <input v-model.number="soaConfig.expire" id="expire" type="number" />
              </div>
              <div class="form-group">
                <label for="minimum">Minimum TTL (seconds)</label>
                <input v-model.number="soaConfig.minimum" id="minimum" type="number" />
              </div>
            </div>
            <div class="form-group">
              <label for="serial">Serial Number</label>
              <input v-model.number="soaConfig.serial" id="serial" type="number" placeholder="Auto-generated if empty" />
              <small>Leave empty to auto-generate from timestamp</small>
            </div>
          </div>
          <div class="modal-footer">
            <button @click="closeSOAModal" class="btn btn-secondary">Cancel</button>
            <button @click="downloadWithSOA" class="btn btn-success">Download BIND Zone</button>
          </div>
        </div>
      </div>

      <div class="records-section">
        <div class="records-header">
          <h2>DNS Records</h2>
          <div class="filter-controls">
            <div class="search-box">
              <input
                v-model="searchQuery"
                type="text"
                placeholder="Search records (name, value, comment...)"
                class="search-input"
              />
              <button v-if="searchQuery || filterType" @click="clearFilters" class="btn-clear" title="Clear filters">
                ✕
              </button>
            </div>
            <select v-model="filterType" class="filter-select">
              <option value="">All Types</option>
              <option v-for="type in recordTypes" :key="type" :value="type">{{ type }}</option>
            </select>
          </div>
        </div>

        <div class="results-info" v-if="records.length > 0">
          Showing <strong>{{ filteredRecords.length }}</strong> of <strong>{{ records.length }}</strong> records
          <span v-if="searchQuery || filterType" class="filter-active">
            (filtered)
          </span>
        </div>

        <div v-if="filteredRecords.length === 0 && records.length > 0" class="empty">
          No records match your search criteria. <button @click="clearFilters" class="link-button">Clear filters</button>
        </div>

        <div v-if="filteredRecords.length === 0 && records.length === 0" class="empty">
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
      searchQuery: '',
      showSOAModal: false,
      soaConfig: {
        mname: '',
        rname: '',
        refresh: 10800,
        retry: 3600,
        expire: 2419200,
        minimum: 900,
        serial: null,
      },
    };
  },
  computed: {
    recordTypes() {
      const types = new Set(this.records.map(r => r.record_type));
      return Array.from(types).sort();
    },
    filteredRecords() {
      let filtered = this.records;

      // Filter by record type
      if (this.filterType) {
        filtered = filtered.filter(r => r.record_type === this.filterType);
      }

      // Filter by search query
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase().trim();
        filtered = filtered.filter(record => {
          // Search across multiple fields
          const searchableText = [
            record.name,
            record.record_type,
            record.value,
            record.comment,
            record.ttl?.toString(),
            record.priority?.toString(),
          ]
            .filter(Boolean) // Remove null/undefined values
            .join(' ')
            .toLowerCase();

          return searchableText.includes(query);
        });
      }

      return filtered;
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
    handleDownload() {
      // Show SOA modal for BIND exports, otherwise download directly
      if (this.exportFormat === 'bind') {
        this.showSOAModal = true;
      } else {
        this.downloadExport();
      }
    },
    closeSOAModal() {
      this.showSOAModal = false;
    },
    async downloadWithSOA() {
      // Validate required fields
      if (!this.soaConfig.mname || !this.soaConfig.rname) {
        alert('Please provide both Primary Nameserver and Admin Email');
        return;
      }

      this.closeSOAModal();
      await this.downloadExport(this.soaConfig);
    },
    async downloadExport(soaConfig = null) {
      try {
        const response = await exportsAPI.download(this.id, this.exportFormat, soaConfig);
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
    clearFilters() {
      this.searchQuery = '';
      this.filterType = '';
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
  gap: 1rem;
  flex-wrap: wrap;
}

.filter-controls {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex: 1;
  justify-content: flex-end;
}

.search-box {
  position: relative;
  flex: 1;
  max-width: 400px;
}

.search-input {
  width: 100%;
  padding: 0.5rem 2.5rem 0.5rem 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.95rem;
  transition: border-color 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #42b983;
  box-shadow: 0 0 0 2px rgba(66, 185, 131, 0.1);
}

.btn-clear {
  position: absolute;
  right: 0.5rem;
  top: 50%;
  transform: translateY(-50%);
  background: #e0e0e0;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.875rem;
  color: #666;
  transition: background 0.2s;
}

.btn-clear:hover {
  background: #d0d0d0;
  color: #333;
}

.filter-select {
  padding: 0.5rem 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.95rem;
  min-width: 140px;
  cursor: pointer;
  transition: border-color 0.2s;
}

.filter-select:focus {
  outline: none;
  border-color: #42b983;
  box-shadow: 0 0 0 2px rgba(66, 185, 131, 0.1);
}

.results-info {
  padding: 0.75rem 1rem;
  background: #f5f5f5;
  border-radius: 6px;
  margin-bottom: 1rem;
  color: #555;
  font-size: 0.95rem;
}

.filter-active {
  color: #42b983;
  font-weight: 600;
}

.link-button {
  background: none;
  border: none;
  color: #42b983;
  cursor: pointer;
  text-decoration: underline;
  padding: 0;
  font-size: inherit;
}

.link-button:hover {
  color: #359268;
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

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e0e0e0;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  color: #333;
}

.btn-close {
  background: none;
  border: none;
  font-size: 2rem;
  color: #999;
  cursor: pointer;
  line-height: 1;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background 0.2s;
}

.btn-close:hover {
  background: #f0f0f0;
  color: #666;
}

.modal-body {
  padding: 1.5rem;
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #333;
  font-size: 0.95rem;
}

.form-group input {
  width: 100%;
  padding: 0.6rem 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.95rem;
  transition: border-color 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: #42b983;
  box-shadow: 0 0 0 2px rgba(66, 185, 131, 0.1);
}

.form-group small {
  display: block;
  margin-top: 0.375rem;
  color: #666;
  font-size: 0.875rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid #e0e0e0;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.btn-secondary {
  background: #e0e0e0;
  color: #333;
}

.btn-secondary:hover {
  background: #d0d0d0;
}
</style>
