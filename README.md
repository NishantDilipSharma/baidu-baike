# Baidu Baike MCP (百度百科)

**Model Context Protocol (MCP) server** for searching and reading [Baidu Baike](https://baike.baidu.com) — China’s largest Chinese-language encyclopedia.

Works with **any MCP-compatible app** (Claude Desktop, Claude Code, ChatGPT MCP clients, custom agents, IDEs, and more) over stdio. **No login. No API key.**

## Capabilities

| Tool | What it does |
|------|----------------|
| `baike_search` | Search lemmas; returns titles, lemma IDs, short blurbs, and URLs |
| `get_baike_entry` | Fetch a structured entry (summary, infobox, catalog, body) by lemma name, lemma ID, or Baike URL |

**Resilience:** Baidu Baike desktop HTML → Baidu OpenAPI → Chinese Wikipedia (`zh.wikipedia.org`), with source noted when a fallback is used.

**Language:** Chinese text is returned as UTF-8 verbatim.

## Requirements

- [uv](https://github.com/astral-sh/uv) (recommended) or Python 3.12+
- Network access to Baidu (and optionally Wikipedia)

## Install & run

```bash
cd server
uv sync
uv run python -m baidu_baike_mcp
```

Or with pip:

```bash
cd server
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m baidu_baike_mcp
```

Docker:

```bash
cd server
docker build -t baidu-baike-mcp .
docker run -i --rm baidu-baike-mcp
```

## Add to any MCP client

Use a standard MCP server config (path adjusted to your checkout):

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

See `mcp.json` in this repo and `server/AGENT_SETUP.md` for cloud/proxy notes.

## Suggested agent workflow

1. `baike_search` to disambiguate multi-sense titles  
2. `get_baike_entry` with the chosen lemma (and `lemma_id` when available)  
3. Quote Chinese content verbatim; keep fallback source attribution if present  

## License

MIT © Nishant Sharma
