# Cloud AI Agent Setup Guide: Baidu Baike MCP Server (Cloud-Resilient Edition)

This guide provides instructions for an autonomous AI agent or engineer deploying this Model Context Protocol (MCP) server in a cloud environment (e.g., Docker container, cloud VM, or agent workstation).

---

## 1. Cloud Network & WAF Resilience

Cloud datacenter IPs (AWS, GCP, Azure, DigitalOcean, Hetzner, etc.) frequently trigger Baidu's Edge CDN anti-bot verification (`百度安全验证`) on desktop web pages.

This server has built-in **3-Tier Automatic Fallbacks** so you will never get blocked:
1. **Tier 1 (Desktop)**: Direct `baike.baidu.com` queries with Chrome 124 TLS impersonation.
2. **Tier 2 (Baidu OpenAPI)**: If Tier 1 hits a security verification challenge on your cloud IP, the server automatically queries Baidu's backend OpenAPI (`BaikeLemmaCardApi`), which returns canonical abstracts, structured infoboxes, and catalogs as pure JSON **without web CAPTCHAs or WAF blocks**.
3. **Tier 3 (Chinese Wikipedia)**: If your cloud host is entirely firewalled from Baidu, it automatically queries `zh.wikipedia.org` to provide accurate encyclopedic context.
4. **Proxy Support (Optional)**: If you have an outbound proxy, you can optionally pass `HTTPS_PROXY` or `HTTP_PROXY`.

---

## 2. Quick Setup in Cloud Workspaces

### Method A: Using `uv` (Recommended)

```bash
# 1. Sync dependencies into an isolated virtual environment
uv sync

# 2. Verify with test suite
uv run pytest tests/

# 3. Test live retrieval
uv run python scripts/smoke_test.py
```

### Method B: Using Standard Python `venv` + `pip`

```bash
# 1. Create and activate venv
python3 -m venv .venv
source .venv/bin/activate

# 2. Install editable package
pip install -e .

# 3. Run test suite
pip install pytest
pytest tests/
```

### Method C: Docker Container

```bash
# Build image
docker build -t baidu-baike-mcp .

# Run over stdio
docker run -i --rm baidu-baike-mcp
```

---

## 3. Client Configuration Snippets

### Claude Desktop / Claude Code / Cursor

```json
{
  "mcpServers": {
    "baidu-baike": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["-m", "baidu_baike_mcp"],
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1"
      }
    }
  }
}
```

*If using an outbound proxy:*
```json
{
  "mcpServers": {
    "baidu-baike": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["-m", "baidu_baike_mcp"],
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "HTTPS_PROXY": "http://your-proxy:port"
      }
    }
  }
}
```

---

## 4. Tools Reference

| Tool Name | Arguments | Description | Output |
|---|---|---|---|
| `baike_search` | `query: str`, `limit: int = 5` | Searches lemma suggestions with automatic fallback to Wikipedia search. | Markdown list of candidate titles, IDs, descriptions, and URLs. |
| `get_baike_entry` | `lemma: str`, `lemma_id: Optional[int] = None`, `max_sections: int = 25` | Retrieves encyclopedia entry (accepts lemma name or URL) with automatic 3-tier fallback. | Structured Markdown with Title, URL, Summary, Infobox, Catalog, and Body highlights. |
