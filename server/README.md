# Baidu Baike MCP Server (百度百科) - Cloud-Resilient Edition

A fast, reliable, login-free Model Context Protocol (MCP) server for searching and retrieving structured knowledge from Baidu Baike (百度百科), specifically engineered to handle cloud datacenter IP blocks.

## Key Features & Cloud Resilience

- **Anti-Bot & Datacenter WAF Bypass**: Major cloud providers (AWS, GCP, Azure, DigitalOcean) frequently face Baidu web WAF verification (`百度安全验证`). This server incorporates a **3-Tier Automatic Fallback**:
  1. **Tier 1 (Desktop Web)**: Queries `baike.baidu.com` with Chrome TLS impersonation and visitor cookies.
  2. **Tier 2 (Baidu OpenAPI + Mobile)**: If desktop triggers WAF challenges, automatically switches to Baidu's official backend OpenAPI (`BaikeLemmaCardApi`), fetching complete abstracts, infobox key-values, and catalogs without WAF interference, augmented with mobile (`wapbaike`) body text.
  3. **Tier 3 (Chinese Wikipedia Fallback)**: If a cloud datacenter IP is completely firewalled from all Baidu endpoints, automatically falls back to `zh.wikipedia.org` to guarantee the agent always receives encyclopedic background.
- **Optional Proxy Support**: Automatically respects standard `HTTPS_PROXY` / `HTTP_PROXY` / `ALL_PROXY` environment variables if configured.
- **Zero Credentials**: Completely free, requiring no API keys, accounts, or cookies.
- **Search & Suggestion**: `baike_search` retrieves lemma suggestions with IDs and one-line summaries.
- **Rich Structured Extraction**: `get_baike_entry` extracts canonical titles, lead summaries, infobox key-values, catalogs, and section headings/paragraphs in clean Markdown.

## Tools

1. `baike_search(query: str, limit: int = 5)`:
   Search for lemmas matching a term.
2. `get_baike_entry(lemma: str, lemma_id: Optional[int] = None, max_sections: int = 25)`:
   Fetch and parse full entry text, infobox, and table of contents. Accepts lemma names or full Baike URLs.

## Installation & Running

```bash
# With uv (recommended)
uv sync
uv run python -m baidu_baike_mcp

# Or with pip
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m baidu_baike_mcp
```
