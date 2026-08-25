The existing Tkinter and tray application remains the desktop client.

`api_client.py` provides the shared HTTP client for gradually moving desktop actions to the backend. The current desktop UI still works locally and is intentionally not replaced yet.

Install its optional API-client dependency with:

```powershell
pip install -r desktop/requirements.txt
```
