# Management UI - Streamlit Dashboard

A real-time monitoring and analytics dashboard for the task backend system.

## Features

- 📊 **Real-time Dashboard**: Monitor task status, throughput, and system health
- 💰 **Cost Tracking**: Analyze costs by user, task type, and time period
- 🔍 **Task Search**: Detailed task inspection with input/output viewer
- 📈 **Auto-refresh**: Live updates every 10 seconds

## Quick Start

### Local Development

1. **Install dependencies**:
   ```bash
   cd monitoring/ui
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   Create a `.env` file or export variables:
   ```bash
   export DATABASE_URL="postgresql+asyncpg://openwebui:password@localhost:5432/openwebui"
   export TASK_API_URL="http://localhost:8000"
   ```

3. **Run the app**:
   ```bash
   streamlit run app.py
   ```

4. **Open browser**: Navigate to `http://localhost:8501`

### Docker Deployment

The UI is automatically deployed with the full stack:

```bash
# Start all services including management UI
docker-compose up -d management-ui

# Or start the entire stack
docker-compose up -d
```

Access the UI at: `http://localhost:8501`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://openwebui:password@postgres:5432/openwebui` | PostgreSQL connection string |
| `TASK_API_URL` | `http://task-api:8000` | Task API endpoint |
| `UI_REFRESH_INTERVAL` | `10` | Auto-refresh interval (seconds) |
| `UI_MAX_TASKS_DISPLAY` | `100` | Max tasks in dashboard table |
| `UI_COST_ALERT_THRESHOLD` | `100.0` | Monthly cost alert threshold (USD) |

## Pages

### 📊 Dashboard
- Task status overview (pending, running, done, error)
- Recent tasks table with filters
- Real-time auto-refresh
- Success/error rates

### 💰 Costs
- Cost summary metrics
- Daily cost trends chart
- Top spenders by user
- Token usage analysis
- Cost projections

### 🔍 Task Search
- Search by task ID (UUID)
- Full task details viewer
- Input/output JSON inspector
- Link to distributed traces (Grafana Tempo)

## Architecture

```
monitoring/ui/
├── app.py                     # Main Streamlit app
├── config.py                  # Configuration
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container image
├── data/
│   └── database.py           # Database client & queries
└── pages/
    ├── 1_📊_Dashboard.py     # Task monitoring
    ├── 2_💰_Costs.py         # Cost analytics
    └── 3_🔍_Task_Search.py   # Task search
```

## Development

### Adding New Queries

Add new database queries in `data/database.py`:

```python
async def get_custom_metric(self) -> dict:
    query = text("SELECT ...")
    async with self.async_session() as session:
        result = await session.execute(query)
        return dict(result.first()._mapping)
```

### Creating New Pages

Create a new file in `pages/` with format: `N_emoji_PageName.py`

Example: `pages/4_📈_Analytics.py`

```python
import streamlit as st

st.title("📈 Analytics")
# Your page content here
```

## Troubleshooting

### Database Connection Errors

**Error**: `connection refused` or `authentication failed`

**Solution**:
- Check `DATABASE_URL` environment variable
- Ensure PostgreSQL is running: `docker-compose ps postgres`
- Verify credentials in `.env` file

### No Data Showing

**Error**: UI loads but shows no tasks

**Solution**:
- Check that tasks exist: `docker exec -it postgres psql -U openwebui -c "SELECT COUNT(*) FROM tasks;"`
- Verify database migrations have run
- Check `TASK_API_URL` is correct

### Auto-refresh Not Working

**Solution**:
- Streamlit auto-refresh uses `st.rerun()` with a sleep timer
- Check browser console for errors
- Try manually refreshing with sidebar button

## Performance Notes

- **Caching**: Queries are cached with TTL (60s for costs, 10s for dashboard)
- **Large datasets**: Dashboard table is limited to `UI_MAX_TASKS_DISPLAY` rows
- **Database load**: Auto-refresh queries run every `UI_REFRESH_INTERVAL` seconds

For high-traffic systems, consider:
- Increasing cache TTL
- Using read replicas for queries
- Adding database connection pooling

## Future Enhancements

Potential features for future versions:
- [ ] WebSocket integration for real-time updates without polling
- [ ] Administrative actions (retry failed tasks, cancel running tasks)
- [ ] User authentication and RBAC
- [ ] Custom dashboards and saved views
- [ ] Export to CSV/PDF
- [ ] Email/Slack alerts for cost thresholds
- [ ] Historical analytics with time-series aggregations
