# FAQ

## Does Claude Code receive my Z.ai key?

No. Claude Code needs a non-empty placeholder `ANTHROPIC_API_KEY` to enter API-key mode. In CaptureAnthropic mode Moon Bridge strips client credentials and uses `proxy.anthropic.api_key` from the Docker-host configuration for the upstream request.

## Why is the port open without a token?

That is the requested test configuration. It is unsafe on a public or shared network because every reachable client can use the upstream key. `CaptureAnthropic` does not apply `server.auth_token` to proxy traffic, so use a firewall/VPN or an authenticated reverse proxy before production.

## Which model should I choose?

Use any model name enabled for your Z.ai account, for example `glm-4.7-flash`. The proxy preserves the model chosen by `claude --model`.

## How do I update Moon Bridge?

Update the `moon-bridge` submodule deliberately to a reviewed upstream commit, then rebuild with `make build` and restart the container.
