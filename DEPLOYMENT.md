# Deployment notes

## Test deployment

1. Initialise the local config: `make init`.
2. Edit `config/config.yml`; replace the Z.ai API-key placeholder.
3. Start: `make up`.
4. Verify configuration loading: `make health`.

The Compose file publishes `38440` to every interface. This is only suitable for a trusted test network.

## Production hardening

Before production, do all of the following:

1. Publish only `127.0.0.1:38440:38440`, or place the service behind a firewall/VPN.
2. Put an authenticated reverse proxy in front of Moon Bridge if clients need remote access. `CaptureAnthropic` does not apply `server.auth_token` to proxied requests.
3. Terminate TLS at that reverse proxy if any traffic leaves the host.
4. Restrict file permissions for `config/config.yml` and back up the configuration securely.
5. Never add the live configuration or an API key to Git.

Restart Moon Bridge after every configuration change: `make restart`.
