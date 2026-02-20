# Webhook Relay Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deploy a Cloudflare Worker that relays GitHub Projects V2 webhook events as `repository_dispatch` to the `.github` repo, enabling GitHub Actions to react to project board changes.

**Architecture:** A minimal Cloudflare Worker receives `projects_v2_item` webhook POSTs from GitHub, verifies the HMAC-SHA256 signature, and forwards the full payload as a `repository_dispatch` event to `kai-loacher-org/.github`. The workflow in the `.github` repo triggers on `repository_dispatch`, filters relevant events, and calls the existing Orchestrator.

**Tech Stack:** Cloudflare Workers (JavaScript/ES Modules), Wrangler CLI, GitHub REST API, GitHub Actions

---

### Task 1: Create the Cloudflare Worker project

**Files:**
- Create: `webhook-relay/package.json`
- Create: `webhook-relay/wrangler.toml`
- Create: `webhook-relay/src/index.js`
- Create: `webhook-relay/.gitignore`

**Step 1: Create `webhook-relay/.gitignore`**

```
node_modules/
.dev.vars
.wrangler/
```

**Step 2: Create `webhook-relay/package.json`**

```json
{
  "name": "github-webhook-relay",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "wrangler dev",
    "deploy": "wrangler deploy"
  },
  "devDependencies": {
    "wrangler": "^3"
  }
}
```

**Step 3: Create `webhook-relay/wrangler.toml`**

```toml
name = "github-webhook-relay"
main = "src/index.js"
compatibility_date = "2026-02-20"

[vars]
GITHUB_REPO = "kai-loacher-org/.github"
```

Note: `GITHUB_PAT` and `WEBHOOK_SECRET` are set as encrypted secrets via `wrangler secret put`, not in this file.

**Step 4: Create `webhook-relay/src/index.js`**

```javascript
export default {
  async fetch(request, env) {
    // Only accept POST
    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    // Read body as text (needed for both signature verification and parsing)
    const body = await request.text();

    // Verify GitHub webhook signature
    const signature = request.headers.get("x-hub-signature-256");
    if (!signature) {
      return new Response("Missing signature", { status: 401 });
    }

    const valid = await verifySignature(env.WEBHOOK_SECRET, body, signature);
    if (!valid) {
      return new Response("Invalid signature", { status: 401 });
    }

    // Parse the event
    const event = request.headers.get("x-github-event");
    const payload = JSON.parse(body);

    // Forward as repository_dispatch
    const [owner, repo] = env.GITHUB_REPO.split("/");
    const response = await fetch(
      `https://api.github.com/repos/${owner}/${repo}/dispatches`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${env.GITHUB_PAT}`,
          Accept: "application/vnd.github+json",
          "User-Agent": "github-webhook-relay",
          "X-GitHub-Api-Version": "2022-11-28",
        },
        body: JSON.stringify({
          event_type: event,
          client_payload: payload,
        }),
      }
    );

    if (!response.ok) {
      const error = await response.text();
      return new Response(`GitHub API error: ${response.status} ${error}`, {
        status: 502,
      });
    }

    return new Response("OK", { status: 200 });
  },
};

async function verifySignature(secret, payload, signature) {
  const encoder = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const sig = await crypto.subtle.sign("HMAC", key, encoder.encode(payload));
  const digest = "sha256=" + [...new Uint8Array(sig)]
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
  return signature === digest;
}
```

**Step 5: Commit**

```bash
git add webhook-relay/
git commit -m "feat: add Cloudflare Worker webhook relay for Projects V2 events"
```

---

### Task 2: Update the `.github` repo workflow

**Files:**
- Modify: workflow in `kai-loacher-org/.github` repo (`.github/workflows/orchestrator-trigger.yml`)

**Step 1: Update the workflow trigger from `projects_v2_item` to `repository_dispatch`**

Replace the entire file with:

```yaml
name: Project Board Trigger

on:
  repository_dispatch:
    types: [projects_v2_item]

permissions:
  contents: write
  pull-requests: write
  issues: write
  actions: write

jobs:
  orchestrate:
    # Only trigger for issues when a single-select field (e.g. Status) changes
    if: >-
      github.event.client_payload.projects_v2_item.content_type == 'Issue' &&
      github.event.client_payload.changes.field_value.field_type == 'single_select'
    uses: kai-loacher-org/bc-agentic-workflow/.github/workflows/orchestrator.yml@main
    with:
      item_node_id: ${{ github.event.client_payload.projects_v2_item.node_id }}
      content_node_id: ${{ github.event.client_payload.projects_v2_item.content_node_id }}
      project_node_id: ${{ github.event.client_payload.projects_v2_item.project_node_id }}
    secrets: inherit
```

Key changes:
- `on: repository_dispatch` instead of `on: projects_v2_item`
- Event data accessed via `github.event.client_payload.*` instead of `github.event.*`

**Step 2: Push the updated workflow to the `.github` repo**

**Step 3: Commit reference update in `bc-agentic-workflow`**

Also update `project-board-trigger.yml` in this repo to match (so the template stays in sync).

```bash
git add .github/workflows/project-board-trigger.yml
git commit -m "fix: update project-board-trigger to use repository_dispatch"
```

---

### Task 3: Deploy the Worker and configure secrets

**Step 1: Install dependencies**

```bash
cd webhook-relay
npm install
```

**Step 2: Deploy the Worker**

```bash
npx wrangler deploy
```

Note: This will prompt for Cloudflare login if not already authenticated.
The output will show the Worker URL, e.g.: `https://github-webhook-relay.<account>.workers.dev`

**Step 3: Set the Worker secrets**

```bash
npx wrangler secret put WEBHOOK_SECRET
# Enter a strong random string (save it — needed for GitHub webhook config too)

npx wrangler secret put GITHUB_PAT
# Enter the same PAT used as WORKFLOW_PAT in GitHub org secrets
```

---

### Task 4: Configure the GitHub Org Webhook (manual)

This step must be done manually in the GitHub UI.

**Step 1: Go to org webhook settings**

URL: `https://github.com/organizations/kai-loacher-org/settings/hooks`

**Step 2: Click "Add webhook"**

- **Payload URL**: The Worker URL from Task 3 (e.g. `https://github-webhook-relay.<account>.workers.dev`)
- **Content type**: `application/json`
- **Secret**: The same value entered as `WEBHOOK_SECRET` in Task 3
- **Events**: Select "Let me select individual events" → check "Projects v2 item"
- **Active**: checked

**Step 3: Save and test**

GitHub will send a ping event. The Worker will forward it but GitHub Actions will ignore it (no matching `event_type`). That's expected.

---

### Task 5: End-to-end test

**Step 1: Move an issue to "Ready" on the project board**

Go to: `https://github.com/orgs/kai-loacher-org/projects/3/views/1`

**Step 2: Verify the Worker received the event**

Check Cloudflare dashboard → Workers → github-webhook-relay → Logs

**Step 3: Verify the workflow triggered**

Check: `https://github.com/kai-loacher-org/.github/actions`
The "Project Board Trigger" workflow should appear and run.

**Step 4: Verify the Orchestrator was called**

The orchestrator should validate the "Ready" status and dispatch the developer workflow.
