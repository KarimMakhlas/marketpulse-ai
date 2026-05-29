# Deployment (v0.4)

This is the runbook for deploying the MarketPulse AI stack to a single Hetzner
Cloud VM and exposing it over HTTPS with a Cloudflare Tunnel. Everything up to
this point (Dockerfile, `docker-compose.yml`, migrations, CI) is in the repo and
verified; these are the steps that require **your** Hetzner and Cloudflare
accounts, so they're documented rather than automated.

> Cost note: a Hetzner CX22 is ~€4–5/month. The Gemini free tier (20 req/day,
> and each `/query` spends 2 calls) is the real ceiling for multi-user use —
> plan to move `GeminiProvider` to a paid key or a self-hosted model before
> opening it up. Nothing here incurs spend until you create the VM.

## 0. Prerequisites

- A Hetzner Cloud project + an SSH key uploaded to it.
- A domain on Cloudflare (free plan is fine) — e.g. `marketpulse.example.com`.
- Your `GEMINI_API_KEY` and a generated `JWT_SECRET_KEY`:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(48))"
  ```

## 1. Provision the VM

Create a CX22 (2 vCPU / 4 GB) running Ubuntu 24.04. SSH in, then install Docker:

```bash
curl -fsSL https://get.docker.com | sh
```

Embeddings (`bge-small`, pulls torch) need the RAM — 4 GB is the practical floor.

## 2. Ship the code + secrets

```bash
git clone <your-repo-url> marketpulse && cd marketpulse
cp .env.example .env
# Edit .env: set GEMINI_API_KEY and JWT_SECRET_KEY.
# Leave DATABASE_URL / REDIS_URL blank — docker-compose.yml sets them to the
# in-network postgres/redis services automatically.
```

Never commit `.env` (it's gitignored). For a real setup, prefer Hetzner's
secret handling or Docker secrets over a plaintext file.

## 3. Bring up the stack

```bash
make stack-up          # build + start API + Postgres + Redis + Kafka
docker compose logs -f api
```

The API container runs `alembic upgrade head` on startup, then serves on
`:8000`. Verify locally on the VM:

```bash
curl localhost:8000/health      # -> {"status":"ok","version":"0.4.0"}
```

Seed the index once (from the VM, outside the container, or via a one-off
`docker compose run`):

```bash
make ingest
```

## 4. Expose via Cloudflare Tunnel

A tunnel avoids opening port 8000 / managing TLS certs on the box.

```bash
# Install cloudflared, then authenticate (opens a browser auth flow):
cloudflared tunnel login
cloudflared tunnel create marketpulse
cloudflared tunnel route dns marketpulse marketpulse.example.com
```

Create `~/.cloudflared/config.yml`:

```yaml
tunnel: marketpulse
credentials-file: /root/.cloudflared/<TUNNEL_ID>.json
ingress:
  - hostname: marketpulse.example.com
    service: http://localhost:8000
  - service: http_status:404
```

Run it as a service:

```bash
cloudflared service install
systemctl enable --now cloudflared
```

`https://marketpulse.example.com/docs` should now serve the Swagger UI.
WebSockets (`wss://.../query/stream`) work through Cloudflare without extra config.

## 5. First user + smoke test

```bash
BASE=https://marketpulse.example.com
curl -X POST $BASE/auth/register -H 'Content-Type: application/json' \
  -d '{"username":"me","password":"a-strong-password"}'
TOKEN=$(curl -s -X POST $BASE/auth/token \
  -d 'username=me&password=a-strong-password' | python -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
curl -X POST $BASE/query -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"query":"What did the Fed do this week?","k":5}'
```

## 6. Operations

- **Update:** `git pull && make stack-up` (rebuilds the API image; migrations
  re-run idempotently).
- **Migrations:** `make migrate` (or let the API container run it on boot).
- **Backups:** `docker compose exec postgres pg_dump -U postgres marketpulse > backup.sql`.
- **Tear down:** `make stack-down ARGS=-v` (the `-v` also wipes volumes).

## Hardening checklist before real traffic

- [ ] Set a strong `JWT_SECRET_KEY` (≥32 bytes) — without it tokens reset on restart.
- [ ] Restrict CORS `allow_origins` in `api/app.py` from `*` to your frontend origin.
- [ ] Set `REDIS_URL` so rate limits hold across API restarts / multiple workers.
- [ ] Move off the Gemini free tier (20 req/day) or self-host the LLM.
- [ ] Put real secrets in a secret store, not a plaintext `.env`.
