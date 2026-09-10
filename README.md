# Baidu Baike MCP (百度百科)

**Generic [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server** for searching and reading [Baidu Baike](https://baike.baidu.com).

One server. **Any MCP-compatible app** — Claude Desktop, Claude Code, Cursor, Codex, ChatGPT MCP clients, custom agents, and more.

- No login  
- No API key  
- Stdio MCP  

## Capabilities

| Tool | What it does |
|------|----------------|
| `baike_search` | Search lemmas; titles, lemma IDs, blurbs, URLs |
| `get_baike_entry` | Structured entry (summary, infobox, catalog, body) by lemma, ID, or Baike URL |

**Fallbacks when cloud IPs hit Baidu WAF:** Baike desktop → Baidu OpenAPI → Chinese Wikipedia (`zh.wikipedia.org`).

Chinese text is returned UTF-8 verbatim.

## Install the server (once)

```bash
cd server
uv sync
```

Requirements: [uv](https://github.com/astral-sh/uv) or Python 3.12+.

## Add it to your app (same MCP, different config file)

Every app just needs to start this process over stdio. Copy the idea below and point `--directory` at **your** checkout’s `server/` folder.

### Generic MCP config

Use `mcp.stdio.example.json` as a template:

```json
{
  "mcpServers": {
    "baidu-baike": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/baidu-baike/server",
        "python",
        "-m",
        "baidu_baike_mcp"
      ],
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1"
      }
    }
  }
}
```

### Claude Desktop

Edit Claude’s MCP config (Claude Desktop → Settings → Developer → Edit Config) and merge the `mcpServers.baidu-baike` block above.

### Claude Code / other CLI agents

Register the same stdio server in that tool’s MCP settings (same `command` / `args` / `env`).

### Cursor

Cursor can use the **same** MCP server entry. This repo also includes optional plugin metadata (`.cursor-plugin/`, `plugin.json`, `mcp.json`) so plugin loaders can discover it — still the same generic MCP underneath.

### Codex / ChatGPT / other MCP hosts

Add a custom MCP server with the same stdio command. If the host UI only asks for “command” and “args”, paste the `uv run …` values from the generic config.

### Docker (any host that can run a container over stdio)

```bash
cd server
docker build -t baidu-baike-mcp .
docker run -i --rm baidu-baike-mcp
```

Point the app’s MCP config at that Docker command instead of `uv` if you prefer.

More cloud/proxy detail: `server/AGENT_SETUP.md`.

## Suggested agent workflow

1. `baike_search` to disambiguate  
2. `get_baike_entry` with lemma + `lemma_id` when you have it  
3. Quote Chinese verbatim; keep fallback source notes  

## License

MIT © Nishant Sharma
