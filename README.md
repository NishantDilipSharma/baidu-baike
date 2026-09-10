# Baidu Baike MCP (百度百科)

**Generic [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server** by **Nishant Dilip Sharma** for searching and reading [Baidu Baike](https://baike.baidu.com).

One server for **any MCP-compatible app** — Claude Desktop, Claude Code, Cursor, Codex, ChatGPT MCP clients, custom agents, and more.

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

## Author

**Nishant Dilip Sharma** · GitHub: [NishantDilipSharma](https://github.com/NishantDilipSharma)

## 1. Install the server (once)

```bash
git clone https://github.com/NishantDilipSharma/baidu-baike.git
cd baidu-baike/server
uv sync
```

Requirements: [uv](https://github.com/astral-sh/uv) (recommended) or Python 3.12+.

Keep the absolute path to `…/baidu-baike/server` handy — every app below needs it.

## 2. How to add it to your app

All apps run the **same** stdio command. Only the config file / UI differs.

### Shared MCP block (copy this)

Replace `/absolute/path/to/baidu-baike/server` with your real path:

```json
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
```

Full file example: [`mcp.stdio.example.json`](./mcp.stdio.example.json).

---

### Claude Desktop

1. Open **Claude Desktop → Settings → Developer → Edit Config**  
2. Open `claude_desktop_config.json`  
3. Under `mcpServers`, paste the shared block above (add commas as needed)  
4. Save and fully quit/reopen Claude Desktop  
5. Confirm `baidu-baike` tools appear in the MCP tools list  

---

### Claude Code

1. Open Claude Code MCP settings (or edit its MCP config JSON)  
2. Add the same `baidu-baike` server block under `mcpServers`  
3. Restart Claude Code / reload MCP servers  
4. Run a prompt that needs Baike lookup to verify `baike_search` / `get_baike_entry`  

---

### Cursor

1. Open **Cursor Settings → MCP** (or edit your MCP config JSON)  
2. Add the same `baidu-baike` stdio server block  
3. Save and reload MCP servers  
4. Optional: this repo also ships plugin metadata (`.cursor-plugin/`, `plugin.json`) for plugin loaders — still the same MCP underneath  

---

### Codex / ChatGPT (MCP-compatible hosts)

1. Open the host’s **custom MCP / tools / connectors** settings  
2. Choose **add stdio MCP server** (wording varies)  
3. Command: `uv`  
4. Args: `run` `--directory` `/absolute/path/to/baidu-baike/server` `python` `-m` `baidu_baike_mcp`  
5. Env: `PYTHONIOENCODING=utf-8`, `PYTHONUTF8=1`  
6. Save and refresh tools  

---

### Other MCP apps / custom agents

If the app accepts an MCP JSON config, merge:

```json
{
  "mcpServers": {
    "baidu-baike": { "...shared block..." }
  }
}
```

If it only has UI fields, map:

| Field | Value |
|-------|--------|
| Command | `uv` |
| Arguments | `run --directory /absolute/path/to/baidu-baike/server python -m baidu_baike_mcp` |
| Transport | stdio |

---

### Docker (any host that can run a container over stdio)

```bash
cd server
docker build -t baidu-baike-mcp .
docker run -i --rm baidu-baike-mcp
```

In the app config, set command/args to that `docker run -i --rm baidu-baike-mcp` invocation instead of `uv`.

Cloud/proxy notes: [`server/AGENT_SETUP.md`](./server/AGENT_SETUP.md).

## 3. Suggested agent workflow

1. Call `baike_search` to disambiguate multi-sense titles  
2. Call `get_baike_entry` with the chosen lemma (and `lemma_id` when available)  
3. Quote Chinese content verbatim; keep fallback source attribution if present  

## License

MIT © **Nishant Dilip Sharma**
