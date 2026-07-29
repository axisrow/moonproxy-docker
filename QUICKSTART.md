# Quick start

```bash
make init
${EDITOR:-vi} config/config.yml
make up
```

Set the real Z.ai key only in `config/config.yml`. The file is ignored by Git.

On the machine where Claude Code runs:

```bash
export ANTHROPIC_BASE_URL="http://localhost:38440"
export ANTHROPIC_API_KEY="moonbridge-local-placeholder"
claude --model glm-4.7-flash
```

If Docker is on another machine, replace `localhost` with its address. This test deployment has no inbound authentication, so restrict the network path yourself.
