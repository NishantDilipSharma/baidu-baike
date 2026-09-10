---
name: baidu-baike
description: >-
  Use when looking up Chinese encyclopedia knowledge from Baidu Baike (百度百科),
  disambiguating Chinese lemmas, or needing structured entries (summary, infobox,
  catalog, body). Prefer this over generic web search for Baike-style facts.
---

# Baidu Baike research

## Tools

1. `baike_search(query, limit=5)` — find lemmas, IDs, short blurbs, URLs.
2. `get_baike_entry(lemma, lemma_id=null, max_sections=25)` — full structured entry.
   Accepts a lemma name or a full `baike.baidu.com` URL.

## Workflow

1. Search first to disambiguate multi-sense titles.
2. Call `get_baike_entry` with the chosen title and `lemma_id` when available.
3. Quote Chinese text UTF-8 verbatim; do not "fix" wording or convert script.
4. If the response notes OpenAPI or Wikipedia fallback, keep that source attribution in the answer.

## Notes

- No API key or login required.
- Cloud datacenter IPs may hit Baidu WAF; the server auto-falls back to Baidu OpenAPI, then Chinese Wikipedia.
- Optional: set `HTTPS_PROXY` / `HTTP_PROXY` if you need forced desktop web access.
