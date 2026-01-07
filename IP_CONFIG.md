# IP Configuration

## Current IP Address: 172.20.10.3 (热点网络)

### Files Updated:
1. **frontend/vite.config.js** - API proxy target
2. **frontend/src/main.jsx** - Comment example
3. **start_webapp.sh** - Display URLs

### Ports:
- Backend: 8001
- Frontend: 5173

### Access URLs:
- Backend: http://172.20.10.3:8001
- Frontend: https://172.20.10.3:5173
- Health Check: http://172.20.10.3:8001/health

### Notes:
- Backend runs on HTTP (port 8001)
- Frontend runs on HTTPS (port 5173)
- API proxy is configured to forward `/api` requests to backend
- All services bind to `0.0.0.0` to allow external access

### To Update IP Address:
1. Update `frontend/vite.config.js` line 11
2. Update `frontend/src/main.jsx` line 17 (comment)
3. Update `start_webapp.sh` lines 60, 61, 89
4. Update this file

Last updated: 2024-12-19 (Updated IP to 172.20.10.3 - 热点网络)
