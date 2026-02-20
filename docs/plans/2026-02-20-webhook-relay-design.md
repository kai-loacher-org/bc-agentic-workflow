# Webhook Relay Design: Cloudflare Worker for Projects V2 Events

## Problem

GitHub Projects V2 `projects_v2_item` events are available as webhook events,
but NOT as GitHub Actions workflow triggers. The `.github` repo cannot use
`on: projects_v2_item` — GitHub Actions rejects it with "Unexpected value".

## Solution

A Cloudflare Worker acts as a relay ("Briefträger"):
1. Receives GitHub webhook events
2. Verifies the webhook signature
3. Forwards the complete payload as a `repository_dispatch` to the `.github` repo
4. GitHub Actions workflow triggers on `repository_dispatch` (this IS supported)

The Worker contains zero business logic — all filtering and decision-making
stays in GitHub Actions workflows.

## Architecture

```
Projektboard-Änderung (any status change)
       ↓
GitHub Org Webhook (projects_v2_item)
       ↓  POST https://<worker>.workers.dev
Cloudflare Worker
  - Verify webhook signature (HMAC-SHA256)
  - POST /repos/{owner}/{repo}/dispatches
    event_type: "projects_v2_item"
    client_payload: { full original event }
       ↓
GitHub Actions (.github repo)
  on: repository_dispatch
    types: [projects_v2_item]
       ↓
Workflow reads client_payload, filters, calls Orchestrator
```

## Components

### 1. Cloudflare Worker (`webhook-relay/`)

Minimal relay — receives webhook, verifies signature, forwards as repository_dispatch.

Secrets (stored encrypted in Cloudflare):
- `WEBHOOK_SECRET` — shared secret with GitHub for HMAC verification
- `GITHUB_PAT` — PAT with `repo` scope to create repository_dispatch events

### 2. GitHub Org Webhook (manual setup)

- Configured at org level: Settings → Webhooks
- URL: `https://<worker-name>.<account>.workers.dev`
- Content type: `application/json`
- Secret: same value as `WEBHOOK_SECRET` in Cloudflare
- Events: select `Projects v2 item`

### 3. Workflow in `.github` repo (replaces current project-board-trigger.yml)

Triggers on `repository_dispatch` with type `projects_v2_item`.
Reads event data from `github.event.client_payload`.
Filters for relevant changes (content_type, field_type) and calls orchestrator.

## File Structure

```
bc-agentic-workflow/
├── webhook-relay/
│   ├── wrangler.toml        # Cloudflare Worker config
│   ├── package.json         # Dependencies (none beyond wrangler)
│   └── src/
│       └── index.js         # Worker code (~50 lines)
```

## Security

- **Webhook signature verification**: Worker validates HMAC-SHA256 signature
  from GitHub using the shared `WEBHOOK_SECRET`. Rejects unsigned/invalid requests.
- **PAT storage**: Encrypted as Cloudflare Worker secret, never in code/logs.
- **Transport**: All communication over HTTPS (GitHub→Worker, Worker→GitHub API).

## What Changes

| Component | Before | After |
|-----------|--------|-------|
| `.github` repo workflow | `on: projects_v2_item` (broken) | `on: repository_dispatch` |
| Webhook delivery | Direct to GitHub Actions (impossible) | Via Cloudflare Worker relay |
| Orchestrator workflow | Unchanged | Unchanged |
| Developer/Reviewer workflows | Unchanged | Unchanged |

## Cloudflare Free Tier

- 100,000 requests/day (we use ~10-100)
- 10ms CPU time per request (we use <1ms)
- No cost expected.
