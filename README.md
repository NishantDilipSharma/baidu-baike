# Baidu Baike MCP (百度百科)

**Model Context Protocol (MCP) server** that lets any AI agent search and read [Baidu Baike](https://baike.baidu.com) — China’s largest Chinese-language encyclopedia — **without login or API keys**.

Works with Cursor, Claude Desktop, Claude Code, ChatGPT (MCP-compatible clients), and other agents that speak MCP over stdio.

## Why this exists

Generic web search is weak for Chinese encyclopedia facts, lemma disambiguation, and structured Baike pages. This MCP gives agents first-class tools for:

- **Chinese encyclopedia lookup** (百度百科 / Baidu Baike)
- **Lemma search & disambiguation** (同名条目)
- **Structured entries**: summary, infobox, catalog, article body
- **Cloud-resilient fetching** when datacenter IPs hit Baidu WAF

## Capabilities (MCP tools)

| Tool | Capability |
|------|------------|
| `baike_search` | Search Baike lemmas; returns titles, lemma IDs, short blurbs, and URLs |
| `get_baike_entry` | Fetch a full structured entry by lemma name, lemma ID, or Baike URL |

**Resilience chain:** Baidu Baike desktop HTML → Baidu OpenAPI → Chinese Wikipedia (`zh.wikipedia.org`), with source noted in responses.

**Language:** Returns Chinese text as UTF-8 verbatim (no script “fixes”).

## Quick start

### Requirements

- [uv](https://github.com/astral-sh/uv)
- Python 3.12+

### Run the MCP server

```bash
cd server
uv sync
uv run python -m baidu_baike_mcp
```

Point your MCP client at that stdio command (see `mcp.json` / `.mcp.json` in this repo for example configs).

### Cursor plugin (optional)

This repo also ships as a Cursor / agent plugin layout:

```bash
mkdir -p ~/.cursor/plugins/local
ln -s "$(pwd)" ~/.cursor/plugins/local/baidu-baike
# Reload the editor, then enable the plugin
```

Marketplace: publish this folder via [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish).

## Example agent workflow

1. Call `baike_search` to disambiguate multi-sense Chinese titles  
2. Call `get_baike_entry` with the chosen lemma (and `lemma_id` when available)  
3. Quote Chinese content verbatim; keep fallback source attribution if present  

## Keywords / topics

`mcp` · `model-context-protocol` · `baidu-baike` · `百度百科` · `chinese-encyclopedia` · `ai-agent` · `llm-tools` · `claude` · `cursor` · `research`

## License

MIT © Nishant Sharma
