# Moon Bridge Z.ai proxy for Claude Code

Docker deployment of [Moon Bridge](https://github.com/ZhiYi-R/moon-bridge) for Claude Code. It runs Moon Bridge in `CaptureAnthropic` mode: Claude Code sends requests to this proxy with a disposable local value, and the proxy replaces it with the Z.ai key stored only on the Docker host.

## Security boundary

Moon Bridge's `CaptureAnthropic` mode has no built-in authentication: it never inspects the incoming request and strips the client's `Authorization` header before forwarding upstream, so it cannot enforce `server.auth_token` (that field only applies to the `Transform` mode's router, which speaks a different client protocol). Access control for the deployed instance is therefore provided entirely by the reverse proxy in front of it — TLS termination and a bearer-token check happen in nginx, not in Moon Bridge itself. If you deploy this without a proxy in front (e.g. running `docker compose up` directly and reaching it on `38440`), anyone who can reach that port can spend the Z.ai account behind it; keep it bound to localhost or a private network in that case.

The actual Z.ai secret is stored only in `config/config.yml`, which Git ignores. The key configured in Claude Code (`ANTHROPIC_API_KEY`) is a non-secret placeholder required by the Claude API-key client mode; the real access-control secret is a separate bearer token (see below).

## Start

```bash
make init
# Edit config/config.yml and replace REPLACE_WITH_YOUR_ZAI_API_KEY.
make up
make health
```

`./start.sh` performs the same guarded setup: it creates the local configuration template and refuses to start while the placeholder key remains.

## Native Claude Code configuration

Configure the host that runs Claude Code, not the container.

- Behind a proxy with TLS and a bearer-token gate (e.g. the Dokku deployment described below), point Claude Code at the public HTTPS URL and supply the token via `ANTHROPIC_AUTH_TOKEN` — Claude Code sends it as `Authorization: Bearer <token>`, which is exactly what the reverse proxy checks:

  ```bash
  export ANTHROPIC_BASE_URL="https://your-proxy-domain"
  export ANTHROPIC_AUTH_TOKEN="the-bearer-token-configured-on-the-proxy"
  export ANTHROPIC_API_KEY="moonbridge-local-placeholder"
  claude --model glm-4.7-flash
  ```

  Note: `ANTHROPIC_API_KEY` cannot double as this token — Claude Code sends it as `x-api-key`, a different header, and Moon Bridge's `CaptureAnthropic` mode ignores it entirely (see Security boundary above). Embedding `user:pass@` in `ANTHROPIC_BASE_URL` for HTTP Basic Auth does not work either — Claude Code's HTTP client drops URL userinfo before sending the request.

- Running directly against the container with no proxy in front (`PROXY_HOST:38440`, localhost/private network only):

  ```bash
  export ANTHROPIC_BASE_URL="http://PROXY_HOST:38440"
  export ANTHROPIC_API_KEY="moonbridge-local-placeholder"
  claude --model glm-4.7-flash
  ```

`ANTHROPIC_API_KEY` must be non-empty so Claude Code selects API-key mode, but it is never forwarded upstream. Moon Bridge removes incoming credentials and sends `proxy.anthropic.api_key` from `config/config.yml` as `x-api-key` to `https://api.z.ai/api/anthropic/v1/messages`.

Choose a different available Z.ai model with `claude --model ...`; Capture mode preserves the requested model name.

## Operations

```bash
make build     # build from the Moon Bridge source (cloned at build time)
make logs      # follow container logs
make ps        # container status
make restart   # restart after changing config/config.yml
make down      # stop container
make test      # upstream tests for credential replacement and SSE proxying
```

The Dockerfile clones Moon Bridge's `main` branch directly during the image build, so no submodule checkout is required after cloning this repository.

## Configuration

Only `config/config.example.yml` is committed. Create `config/config.yml` with `make init` and set:

- `proxy.anthropic.api_key`: real Z.ai API key;
- `proxy.anthropic.base_url`: Z.ai's Anthropic-compatible base URL;
- `proxy.anthropic.version`: API version expected by the upstream.

Restart the service after changes: `make restart`.

## Quota dashboard

`docker-compose.yml` also runs `zai-dashboard`, a small Python service (`dashboard/`) that reads
the same `proxy.anthropic.api_key` from `config/config.yml` and renders an HTML page with the
Z.ai Coding Plan quota — model-token pool, MCP-tool pool, reset countdown, and a peak-window
(14:00-18:00 UTC+8) warning. It reuses the quota-fetching logic from
[`zai-limits`](https://github.com/axisrow/zai-limits) instead of duplicating it.

It listens on `127.0.0.1:8081` only — like Moon Bridge itself, it has no authentication of its
own and relies entirely on the reverse proxy in front of it. On the Dokku deployment described
below, the root path `/` of the public domain is routed to this dashboard (via a
`nginx.conf.d/dashboard.conf` include) while every other path, including `/v1/messages`, keeps
going to Moon Bridge on `38440` — both are behind the same bearer-token gate.
