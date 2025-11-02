# Quick Start Guide

Get up and running with DNS Snapshot Exporter in minutes!

## Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- Poetry (Python dependency manager)

## Installation

### 1. Install Poetry (if not already installed)

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### 2. Backend Setup

```bash
cd backend

# Create and configure .env file
cp .env.example .env

# Edit .env with your Infoblox credentials:
# INFOBLOX_URL=https://your-infoblox-server.com
# INFOBLOX_USERNAME=admin
# INFOBLOX_PASSWORD=your-password

# Start the backend (this will auto-install dependencies)
./run.sh
```

The API will start on `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`

### 3. Frontend Setup (in a new terminal)

```bash
cd frontend

# Start the frontend (this will auto-install dependencies)
./run.sh
```

The web interface will start on `http://localhost:5173`

## First Steps

1. **Open the web interface** at `http://localhost:5173`

2. **Add your first zone**:
   - Click "Manage Zones"
   - Click "+ Add Zone"
   - Enter zone name (e.g., `example.com`)
   - Select provider (Infoblox)
   - Click "Add Zone"

3. **Create a snapshot**:
   - Click on the zone you just added
   - Click "Take Snapshot"
   - Wait for the snapshot to complete

4. **View records**:
   - Click "View Records" on the snapshot
   - Browse all DNS records pulled from Infoblox

5. **Export snapshot**:
   - Select export format (BIND, Terraform AWS, Terraform Azure, or CSV)
   - Click "Download"

6. **Compare snapshots** (after creating multiple snapshots):
   - Navigate to "Compare" in the menu
   - Enter two snapshot IDs
   - Click "Compare" to see differences

## Common Commands

### Backend

```bash
# Start backend server
cd backend && ./run.sh

# Run with specific host/port
cd backend
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000

# Run tests
cd backend
poetry run pytest

# Format code
cd backend
poetry run black app/
```

### Frontend

```bash
# Start development server
cd frontend && ./run.sh

# Build for production
cd frontend
npm run build

# Preview production build
cd frontend
npm run preview
```

## API Examples

### Create a Zone

```bash
curl -X POST http://localhost:8000/api/v1/zones \
  -H "Content-Type: application/json" \
  -d '{
    "name": "example.com",
    "provider": "infoblox",
    "enabled": true
  }'
```

### Create a Snapshot

```bash
curl -X POST http://localhost:8000/api/v1/snapshots \
  -H "Content-Type: application/json" \
  -d '{"zone_id": 1}'
```

### List Snapshots for a Zone

```bash
curl http://localhost:8000/api/v1/snapshots/zone/1
```

### Export Snapshot

```bash
curl -X POST http://localhost:8000/api/v1/exports/download \
  -H "Content-Type: application/json" \
  -d '{
    "snapshot_id": 1,
    "format": "bind"
  }' \
  -o example.zone
```

### Compare Two Snapshots

```bash
curl -X POST http://localhost:8000/api/v1/comparisons \
  -H "Content-Type: application/json" \
  -d '{
    "snapshot_id_1": 1,
    "snapshot_id_2": 2
  }'
```

### Schedule Automatic Snapshots

```bash
# Daily at 2 AM
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "zone_id": 1,
    "schedule_type": "cron",
    "schedule_value": "0 2 * * *"
  }'

# Every 6 hours
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "zone_id": 1,
    "schedule_type": "interval",
    "schedule_value": "21600"
  }'
```

## Troubleshooting

### Backend won't start

**Issue**: `ModuleNotFoundError` or dependency errors
```bash
cd backend
poetry install
```

**Issue**: Database errors
- Delete `dns_snapshots.db` and restart
- Tables are created automatically on first run

**Issue**: Can't connect to Infoblox
- Verify credentials in `.env`
- Check `INFOBLOX_URL` is correct
- Test connectivity: `curl -k https://your-infoblox-server.com`

### Frontend won't start

**Issue**: `npm` errors
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Issue**: Can't connect to backend
- Verify backend is running on `http://localhost:8000`
- Check `.env` file has correct `VITE_API_URL`

### Snapshot creation fails

**Common causes**:
1. Invalid Infoblox credentials
2. Zone doesn't exist in Infoblox
3. Network connectivity issues
4. SSL certificate issues (set `INFOBLOX_VERIFY_SSL=False` for testing)

**Solution**: Check backend logs for detailed error messages

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the API at `http://localhost:8000/docs`
- Set up scheduled snapshots for automatic backups
- Try exporting to different formats
- Compare snapshots to track DNS changes over time

## Need Help?

- Check the [README.md](README.md) for full documentation
- View API documentation at `http://localhost:8000/docs`
- Check application logs for error messages
