# AminVC Cloud Heartbeat (Phase 1B)

Long-lived HTTPS process for connection proof only.

Endpoints:

- `POST /agent/heartbeat`
- `GET /agent/status/{device_id}`

Payload is metadata only: `device_id`, `timestamp`, `status`. No project/audio files.

This service uses an **in-memory** store. It must run as **one persistent process**. Do not host it on Vercel.

## Local run

From the repository root:

```powershell
python -m cloud_api
```

Default listen address: `http://127.0.0.1:8090`

With no `AMINVC_WEB_ORIGIN`, CORS allows local Vite:

- `http://localhost:5173`
- `http://127.0.0.1:5173`
- `http://localhost:4173`
- `http://127.0.0.1:4173`

## Docker (build context = repo root)

```powershell
docker build -f cloud_api/Dockerfile -t aminvc-cloud-heartbeat .
docker run --rm -p 8090:8090 -e AMINVC_WEB_ORIGIN=https://YOUR-FRONTEND.vercel.app aminvc-cloud-heartbeat
```

## Public HTTPS (you must create the account)

This repo has no cloud provider login. Create **one** long-lived Web Service, then set:

| Variable | Where | Value |
|---|---|---|
| `AMINVC_WEB_ORIGIN` | Cloud process | Vercel frontend origin, e.g. `https://aminvc.vercel.app` |
| `AMINVC_AGENT_CLOUD_URL` | PC Local Agent | Public HTTPS origin of this service, no trailing slash |
| `VITE_AGENT_CLOUD_URL` | Vercel **build** env | Same public HTTPS origin |

Suggested provider (smallest click-ops): **Render Web Service** from this GitHub repo.

1. Create a Render account and connect `amin-ghaderi/AminVC`.
2. New **Web Service** (not Static Site, not Vercel serverless).
3. Runtime: Docker, Dockerfile path `cloud_api/Dockerfile`, context `.`
   or native Python: start command `python -m cloud_api` (Render sets `PORT`).
4. Set `AMINVC_WEB_ORIGIN` to the Vercel origin.
5. Copy the `https://....onrender.com` URL.

Then on the PC:

```powershell
$env:AMINVC_AGENT_CLOUD_URL = "https://YOUR-SERVICE.onrender.com"
uvicorn app.api.app:create_app --factory --host 127.0.0.1 --port 8080
```

Local Agent only makes **outbound** HTTPS. It does not open a WAN port.

Then in Vercel Project → Settings → Environment Variables:

- `VITE_AGENT_CLOUD_URL` = that same `https://...` origin
- Redeploy the frontend

Paste `storage/agent/device_id` into the header widget.

Expected: Connected while the agent runs; Offline ~30s after it stops.
