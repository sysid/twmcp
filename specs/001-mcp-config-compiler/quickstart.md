# Quickstart: twmcp

## 1. Install

```bash
pip install twmcp
# or from source:
pip install -e .
```

## 2. Create canonical config

```bash
mkdir -p ~/.config/twmcp
cat > ~/.config/twmcp/config.toml << 'EOF'
# Optional: load secrets from dotenv file
# env_file = "~/.config/twmcp/secrets.env"

[servers.github]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-github"]
type = "stdio"
env.GITHUB_TOKEN = "${GITHUB_TOKEN}"

[servers.atlassian]
type = "http"
url = "https://atc.bmwgroup.net/mcp/"
headers.X-Token = "${CONFLUENCE_TOKEN}"
tools = ["*"]

# Override type for copilot-cli (uses "local" instead of "stdio")
[servers.github.overrides.copilot-cli]
type = "local"
EOF
```

## 3. Set secrets

Either via environment variables:

```bash
export GITHUB_TOKEN="ghp_..."
export CONFLUENCE_TOKEN="..."
```

Or via a dotenv file (uncomment `env_file` in config.toml):

```bash
cat > ~/.config/twmcp/secrets.env << 'EOF'
GITHUB_TOKEN=ghp_...
CONFLUENCE_TOKEN=...
EOF
```

## 4. Preview output

```bash
twmcp compile copilot-cli --dry-run
```

## 5. Compile for one agent

```bash
twmcp compile copilot-cli
# Writes ~/.copilot/mcp-config.json
```

## 6. Compile for all agents

```bash
twmcp compile --all
# Writes config for copilot-cli, intellij, claude-desktop
```

## 7. List supported agents

```bash
twmcp agents
```

## Validation

After running `twmcp compile copilot-cli`, verify:

```bash
cat ~/.copilot/mcp-config.json | python -m json.tool
```

The output should contain resolved values (no `${...}` placeholders)
and use the correct format for the agent (`mcpServers` key, `local`
type for stdio servers).
