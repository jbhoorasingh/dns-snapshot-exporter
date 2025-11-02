<template>
  <div class="comparison">
    <div class="header">
      <h1>Compare Snapshots</h1>
    </div>

    <div class="comparison-form">
      <div class="form-group">
        <label>First Snapshot (Older):</label>
        <input
          v-model.number="snapshotId1"
          type="number"
          placeholder="Enter snapshot ID"
          min="1"
        />
      </div>

      <div class="form-group">
        <label>Second Snapshot (Newer):</label>
        <input
          v-model.number="snapshotId2"
          type="number"
          placeholder="Enter snapshot ID"
          min="1"
        />
      </div>

      <button @click="compareSnapshots" class="btn btn-primary" :disabled="!canCompare">
        Compare
      </button>
    </div>

    <div v-if="loading" class="loading">Comparing snapshots...</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <div v-else-if="comparison" class="comparison-results">
      <div class="summary">
        <h2>Comparison Summary</h2>
        <div class="summary-grid">
          <div class="summary-card added">
            <div class="count">{{ comparison.summary.added }}</div>
            <div class="label">Added</div>
          </div>
          <div class="summary-card removed">
            <div class="count">{{ comparison.summary.removed }}</div>
            <div class="label">Removed</div>
          </div>
          <div class="summary-card modified">
            <div class="count">{{ comparison.summary.modified }}</div>
            <div class="label">Modified</div>
          </div>
          <div class="summary-card unchanged">
            <div class="count">{{ comparison.summary.unchanged }}</div>
            <div class="label">Unchanged</div>
          </div>
        </div>
      </div>

      <div v-if="comparison.added.length > 0" class="section">
        <h3>Added Records ({{ comparison.added.length }})</h3>
        <table class="records-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Value</th>
              <th>TTL</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(record, idx) in comparison.added" :key="`added-${idx}`" class="added">
              <td>{{ record.name }}</td>
              <td><span class="record-type">{{ record.type }}</span></td>
              <td>{{ record.value }}</td>
              <td>{{ record.ttl || '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="comparison.removed.length > 0" class="section">
        <h3>Removed Records ({{ comparison.removed.length }})</h3>
        <table class="records-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Value</th>
              <th>TTL</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(record, idx) in comparison.removed" :key="`removed-${idx}`" class="removed">
              <td>{{ record.name }}</td>
              <td><span class="record-type">{{ record.type }}</span></td>
              <td>{{ record.value }}</td>
              <td>{{ record.ttl || '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="comparison.modified.length > 0" class="section">
        <h3>Modified Records ({{ comparison.modified.length }})</h3>
        <div v-for="(item, idx) in comparison.modified" :key="`modified-${idx}`" class="modification">
          <div class="record-header">
            <strong>{{ item.record.name }}</strong>
            <span class="record-type">{{ item.record.type }}</span>
          </div>
          <div class="changes">
            <div v-for="(change, field) in item.changes" :key="field" class="change">
              <strong>{{ field }}:</strong>
              <span class="old-value">{{ change.old }}</span>
              →
              <span class="new-value">{{ change.new }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { comparisonsAPI } from '../api/client';

export default {
  name: 'Comparison',
  data() {
    return {
      snapshotId1: null,
      snapshotId2: null,
      comparison: null,
      loading: false,
      error: null,
    };
  },
  computed: {
    canCompare() {
      return this.snapshotId1 && this.snapshotId2 && this.snapshotId1 !== this.snapshotId2;
    },
  },
  methods: {
    async compareSnapshots() {
      if (!this.canCompare) {
        return;
      }

      try {
        this.loading = true;
        this.error = null;
        this.comparison = null;

        const response = await comparisonsAPI.compare(this.snapshotId1, this.snapshotId2);
        this.comparison = response.data;
      } catch (err) {
        this.error = `Failed to compare snapshots: ${err.response?.data?.detail || err.message}`;
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>

<style scoped>
.comparison {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

.comparison-form {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 2rem;
  margin-bottom: 2rem;
  display: flex;
  gap: 1rem;
  align-items: flex-end;
}

.form-group {
  flex: 1;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
}

.form-group input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.summary {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 2rem;
  margin-bottom: 2rem;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.summary-card {
  text-align: center;
  padding: 1.5rem;
  border-radius: 8px;
}

.summary-card.added {
  background: #e8f5e9;
  color: #2e7d32;
}

.summary-card.removed {
  background: #ffebee;
  color: #c62828;
}

.summary-card.modified {
  background: #fff3e0;
  color: #ef6c00;
}

.summary-card.unchanged {
  background: #e3f2fd;
  color: #1976d2;
}

.summary-card .count {
  font-size: 2rem;
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.section {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.records-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}

.records-table th {
  background: #f5f5f5;
  padding: 1rem;
  text-align: left;
  border-bottom: 2px solid #e0e0e0;
}

.records-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #f0f0f0;
}

.records-table tr.added {
  background: #e8f5e9;
}

.records-table tr.removed {
  background: #ffebee;
}

.record-type {
  background: #e3f2fd;
  color: #1976d2;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 600;
}

.modification {
  background: #fff3e0;
  padding: 1rem;
  border-radius: 4px;
  margin-top: 1rem;
}

.record-header {
  display: flex;
  gap: 1rem;
  align-items: center;
  margin-bottom: 0.5rem;
}

.changes {
  margin-top: 0.5rem;
}

.change {
  margin: 0.5rem 0;
  font-family: monospace;
}

.old-value {
  color: #c62828;
  text-decoration: line-through;
}

.new-value {
  color: #2e7d32;
}

.btn {
  padding: 0.5rem 1.5rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.3s;
}

.btn-primary {
  background: #42b983;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #369970;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading,
.error {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.error {
  color: #f44336;
}
</style>
