# Moon Bridge Z.ai proxy for Claude Code

Docker deployment of [Moon Bridge](https://github.com/ZhiYi-R/moon-bridge) for Claude Code. It runs Moon Bridge in `CaptureAnthropic` mode: Claude Code sends requests to this proxy with a disposable local value, and the proxy replaces it with the Z.ai key stored only on the Docker host.

## Security boundary

This repository is configured for the explicitly requested **unauthenticated test setup**. Docker publishes `38440` on all interfaces. Anyone who can reach this port can spend the Z.ai account behind it. Do not expose it on an untrusted network. `CaptureAnthropic` does not enforce Moon Bridge's console token on proxied requests, so production access control must be provided by localhost binding, a firewall/VPN, or an authenticated reverse proxy with TLS.

The actual Z.ai secret is stored only in `config/config.yml`, which Git ignores. The key configured in Claude Code is a non-secret placeholder required by the Claude API-key client mode.

## Start

```bash
make init
# Edit config/config.yml and replace REPLACE_WITH_YOUR_ZAI_API_KEY.
make up
make health
```

`./start.sh` performs the same guarded setup: it creates the local configuration template and refuses to start while the placeholder key remains.

## Native Claude Code configuration

Configure the host that runs Claude Code, not the container. Replace `PROXY_HOST` with the Docker host address (`localhost` on the same machine).

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
