# DNS Snapshot Exporter

A comprehensive system for backing up, managing, and exporting DNS zones from multiple providers. Built with FastAPI (backend) and Vue.js (frontend).

## Features

- **Multi-Provider Support**: Connect to Infoblox, AWS Route 53, Azure Private DNS, and more
- **Snapshot Management**: Create point-in-time backups of DNS zones
- **Multiple Export Formats**:
  - BIND zone files (`.zone`)
  - Terraform AWS Route 53 (`.tf`)
  - Terraform Azure Private DNS (`.tf`)
  - CSV (`.csv`)
- **Snapshot Comparison**: Compare snapshots to see what changed over time
- **Scheduled Backups**: Automatic snapshots using cron or interval-based scheduling
- **REST API**: Full-featured API for integration with other tools

## Architecture

```
Backend (FastAPI)
├── Connectors (Infoblox, Route53, Azure, etc.)
├── Snapshot Service (Pull & Store)
├── Export Service (BIND, Terraform, CSV)
├── Comparison Service
└── Scheduler (APScheduler)

Frontend (Vue.js)
├── Zone Management
├── Snapshot Browsing
├── Comparison View
└── Export Interface

Database (SQLite/PostgreSQL)
├── Zones
├── Snapshots
├── Records
└── Jobs
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- Poetry (for Python dependency management)

## Quick Start

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install dependencies with Poetry
poetry install

# Create environment file
cp .env.example .env

# Edit .env with your Infoblox credentials
# INFOBLOX_URL=https://your-infoblox-server.com
# INFOBLOX_USERNAME=admin
# INFOBLOX_PASSWORD=your-password
# INFOBLOX_WAPI_VERSION=v2.12

# Initialize database (automatically done on first run)
# Start the API server
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- OpenAPI Schema: `http://localhost:8000/redoc`

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Configuration

### Backend Configuration (`.env`)

```bash
# Database
DATABASE_URL=sqlite:///./dns_snapshots.db
# For PostgreSQL: postgresql://user:password@localhost/dbname

# API Configuration
API_KEY=your-secret-api-key-here

# Infoblox Configuration
INFOBLOX_URL=https://your-infoblox-server.com
INFOBLOX_USERNAME=admin
INFOBLOX_PASSWORD=infoblox
INFOBLOX_WAPI_VERSION=v2.12
INFOBLOX_VERIFY_SSL=True

# Application Settings
EXPORT_DIR=./exports
LOG_LEVEL=INFO
```

### Frontend Configuration (`.env`)

```bash
VITE_API_URL=http://localhost:8000
```

## Usage

### 1. Add a DNS Zone

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/zones \
  -H "Content-Type: application/json" \
  -d '{
    "name": "example.com",
    "description": "My DNS zone",
    "provider": "infoblox",
    "enabled": true
  }'
```

Or use the web interface at `http://localhost:5173/zones`

### 2. Create a Snapshot

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/snapshots \
  -H "Content-Type: application/json" \
  -d '{"zone_id": 1}'
```

Or click "Take Snapshot" in the web interface.

### 3. Export a Snapshot

```bash
# Export to BIND format
curl -X POST http://localhost:8000/api/v1/exports \
  -H "Content-Type: application/json" \
  -d '{
    "snapshot_id": 1,
    "format": "bind"
  }'

# Download directly
curl -X POST http://localhost:8000/api/v1/exports/download \
  -H "Content-Type: application/json" \
  -d '{
    "snapshot_id": 1,
    "format": "terraform_aws"
  }' \
  -o zone.tf
```

Or use the export interface in the web UI.

### 4. Compare Snapshots

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/comparisons \
  -H "Content-Type: application/json" \
  -d '{
    "snapshot_id_1": 1,
    "snapshot_id_2": 2
  }'
```

Or use the comparison view at `http://localhost:5173/compare`

### 5. Schedule Automatic Snapshots

```bash
# Create a cron-based job (daily at 2 AM)
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "zone_id": 1,
    "schedule_type": "cron",
    "schedule_value": "0 2 * * *",
    "enabled": true
  }'

# Create an interval-based job (every 6 hours)
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "zone_id": 1,
    "schedule_type": "interval",
    "schedule_value": "21600",
    "enabled": true
  }'
```

## API Endpoints

### Zones
- `GET /api/v1/zones` - List all zones
- `POST /api/v1/zones` - Create a zone
- `GET /api/v1/zones/{id}` - Get zone details
- `PATCH /api/v1/zones/{id}` - Update a zone
- `DELETE /api/v1/zones/{id}` - Delete a zone

### Snapshots
- `POST /api/v1/snapshots` - Create a snapshot
- `GET /api/v1/snapshots/zone/{zone_id}` - List snapshots for a zone
- `GET /api/v1/snapshots/{id}` - Get snapshot details
- `GET /api/v1/snapshots/{id}/records` - Get snapshot records
- `DELETE /api/v1/snapshots/{id}` - Delete a snapshot

### Exports
- `GET /api/v1/exports/formats` - Get available export formats
- `POST /api/v1/exports` - Export a snapshot
- `POST /api/v1/exports/download` - Download exported file

### Comparisons
- `POST /api/v1/comparisons` - Compare two snapshots

### Jobs
- `GET /api/v1/jobs` - List all jobs
- `POST /api/v1/jobs` - Create a scheduled job
- `GET /api/v1/jobs/{id}` - Get job details
- `PATCH /api/v1/jobs/{id}` - Update a job
- `DELETE /api/v1/jobs/{id}` - Delete a job

## Export Formats

### BIND Zone File
Standard BIND zone file format suitable for BIND DNS servers.

```
; Zone file for example.com
$ORIGIN example.com.
$TTL 3600

; A Records
www                            3600   IN A      192.168.1.1
mail                           3600   IN A      192.168.1.2
```

### Terraform AWS Route 53
Terraform configuration for AWS Route 53 hosted zones.

```hcl
resource "aws_route53_zone" "example_com" {
  name = "example.com"
}

resource "aws_route53_record" "www_a" {
  zone_id = aws_route53_zone.example_com.zone_id
  name    = "www.example.com"
  type    = "A"
  ttl     = 300
  records = ["192.168.1.1"]
}
```

### Terraform Azure Private DNS
Terraform configuration for Azure Private DNS zones.

```hcl
resource "azurerm_private_dns_zone" "example_com" {
  name                = "example.com"
  resource_group_name = var.resource_group_name
}

resource "azurerm_private_dns_a_record" "www_a" {
  name                = "www"
  zone_name           = azurerm_private_dns_zone.example_com.name
  resource_group_name = var.resource_group_name
  ttl                 = 300
  records             = ["192.168.1.1"]
}
```

### CSV
Simple CSV format for data analysis or importing into other systems.

```csv
Name,Type,Value,TTL,Priority,Comment,Disabled
www.example.com,A,192.168.1.1,3600,,,false
mail.example.com,MX,mail.example.com,3600,10,,false
```

## Production Deployment

### Using Docker (Recommended)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/dns_snapshots
      - INFOBLOX_URL=${INFOBLOX_URL}
      - INFOBLOX_USERNAME=${INFOBLOX_USERNAME}
      - INFOBLOX_PASSWORD=${INFOBLOX_PASSWORD}
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=dns_snapshots
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Manual Deployment

1. Set up PostgreSQL database
2. Update `.env` with production settings
3. Run backend with `poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000`
4. Build frontend with `npm run build`
5. Serve frontend static files with nginx or similar

## Development

### Backend Development

```bash
cd backend

# Run tests
poetry run pytest

# Format code
poetry run black app/

# Lint code
poetry run flake8 app/

# Type checking
poetry run mypy app/
```

### Frontend Development

```bash
cd frontend

# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Troubleshooting

### Database Issues
- **Error**: `no such table: zones`
  - **Solution**: Database tables are created automatically on first run. Restart the backend server.

### Infoblox Connection Issues
- **Error**: `Failed to connect to Infoblox`
  - **Solution**: Verify `INFOBLOX_URL`, `INFOBLOX_USERNAME`, and `INFOBLOX_PASSWORD` in `.env`
  - Check network connectivity to Infoblox server
  - Verify SSL certificate settings (`INFOBLOX_VERIFY_SSL`)

### Snapshot Creation Fails
- **Error**: `Failed to create snapshot`
  - **Solution**: Check Infoblox credentials and permissions
  - Verify the zone exists in Infoblox
  - Check backend logs for detailed error messages

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Roadmap

- [ ] Add support for AWS Route 53 connector
- [ ] Add support for Azure Private DNS connector
- [ ] Add support for Windows DNS connector
- [ ] Add support for BlueCat connector
- [ ] Implement webhook notifications
- [ ] Add email notifications for snapshot failures
- [ ] Implement snapshot retention policies
- [ ] Add bulk zone import
- [ ] Implement diff view for comparisons
- [ ] Add support for pushing changes back to providers

## Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/your-repo/dns-snapshot-exporter/issues)
- Documentation: See `/docs` directory

## Authors

Built with ❤️ using FastAPI and Vue.js
