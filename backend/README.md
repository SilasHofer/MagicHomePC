# Backend

FastAPI service for controlling Flux LED bulbs. Devices are stored in SQLite at `data/devices.db`. If that database is empty, the existing `data/devices.csv` is imported automatically once.

Start locally with:

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

The service reads the database path from `DEVICES_DB` and exposes interactive API documentation at `/docs`.

If a device request returns `504`, verify that the bulb is powered on, connected to the same network as the Docker host, and that its address in `data/devices.csv` is current. The service uses the bulb's local TCP connection and cannot control an unreachable device.
