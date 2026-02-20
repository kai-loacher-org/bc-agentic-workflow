export default {
  async fetch(request, env) {
    try {
      if (request.method !== "POST") {
        return new Response("Method not allowed", { status: 405 });
      }

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

      // Forward as repository_dispatch
      const event = request.headers.get("x-github-event");
      const payload = JSON.parse(body);
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
    } catch (err) {
      return new Response(`Worker error: ${err.message}`, { status: 500 });
    }
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
  const digest =
    "sha256=" +
    [...new Uint8Array(sig)]
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
  return signature === digest;
}
