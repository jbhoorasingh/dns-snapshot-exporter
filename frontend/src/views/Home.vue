<template>
  <div class="home">
    <h1>DNS Snapshot Exporter</h1>
    <p class="subtitle">Backup and export DNS zones from multiple providers</p>

    <div class="features">
      <div class="feature-card">
        <h2>📋 Zone Management</h2>
        <p>Register and manage DNS zones from Infoblox and other providers</p>
        <router-link to="/zones" class="btn">Manage Zones</router-link>
      </div>

      <div class="feature-card">
        <h2>📸 Snapshots</h2>
        <p>Create point-in-time backups of your DNS records</p>
        <router-link to="/zones" class="btn">View Snapshots</router-link>
      </div>

      <div class="feature-card">
        <h2>📊 Compare</h2>
        <p>Compare snapshots to see what changed over time</p>
        <router-link to="/compare" class="btn">Compare Snapshots</router-link>
      </div>

      <div class="feature-card">
        <h2>💾 Export</h2>
        <p>Export to BIND, Terraform (AWS/Azure), or CSV</p>
        <router-link to="/zones" class="btn">Export Data</router-link>
      </div>
    </div>

    <div class="info">
      <h3>Supported Providers</h3>
      <ul>
        <li>Infoblox (WAPI)</li>
        <li>AWS Route 53 (coming soon)</li>
        <li>Azure Private DNS (coming soon)</li>
        <li>Windows DNS (coming soon)</li>
      </ul>

      <h3>Export Formats</h3>
      <ul>
        <li>BIND Zone Files (.zone)</li>
        <li>Terraform AWS Route 53 (.tf)</li>
        <li>Terraform Azure Private DNS (.tf)</li>
        <li>CSV (.csv)</li>
      </ul>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Home',
};
</script>

<style scoped>
.home {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

h1 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  color: #2c3e50;
}

.subtitle {
  font-size: 1.2rem;
  color: #666;
  margin-bottom: 3rem;
}

.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
  margin-bottom: 3rem;
}

.feature-card {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.feature-card h2 {
  font-size: 1.5rem;
  margin-bottom: 1rem;
}

.feature-card p {
  color: #666;
  margin-bottom: 1.5rem;
}

.btn {
  display: inline-block;
  padding: 0.75rem 1.5rem;
  background: #42b983;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  transition: background 0.3s;
}

.btn:hover {
  background: #369970;
}

.info {
  background: #f5f5f5;
  padding: 2rem;
  border-radius: 8px;
}

.info h3 {
  color: #2c3e50;
  margin-bottom: 1rem;
}

.info ul {
  list-style-position: inside;
  color: #666;
}

.info li {
  margin-bottom: 0.5rem;
}
</style>
