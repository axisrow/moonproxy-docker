# FAQ

## Does Claude Code receive my Z.ai key?

No. Claude Code needs a non-empty placeholder `ANTHROPIC_API_KEY` to enter API-key mode. In CaptureAnthropic mode Moon Bridge strips client credentials and uses `proxy.anthropic.api_key` from the Docker-host configuration for the upstream request.

## Why doesn't `server.auth_token` protect the proxy?

`CaptureAnthropic` mode bypasses Moon Bridge's normal HTTP router entirely (that router is what enforces `auth_token`), so the field has no effect in this mode regardless of what it's set to. If you deploy the container directly with no reverse proxy in front, every client that can reach the port can use the upstream Z.ai key — bind it to localhost/a private network, or put a reverse proxy with TLS and its own bearer-token check in front of it (as the Dokku deployment in the README does).

## Which model should I choose?

Use any model name enabled for your Z.ai account, for example `glm-4.7-flash`. The proxy preserves the model chosen by `claude --model`.

## How do I update Moon Bridge?

The Dockerfile clones Moon Bridge's `main` branch at build time, so `make build` picks up the latest upstream commit; pin a specific commit in the Dockerfile if you need a reviewed, reproducible version instead.
