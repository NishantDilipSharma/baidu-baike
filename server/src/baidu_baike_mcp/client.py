"""Asynchronous HTTP client for Baidu Baike with Chrome TLS impersonation, OpenAPI fallback, and Wikipedia fallback."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import urllib.parse
from typing import Any, Optional

from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession

logger = logging.getLogger("baidu_baike_mcp.client")

BASE_URL = "https://baike.baidu.com"
WAP_BASE_URL = "https://wapbaike.baidu.com"
SUGGEST_API = "https://baike.baidu.com/api/searchui/suggest"
OPENAPI_CARD_URL = "https://baike.baidu.com/api/openapi/BaikeLemmaCardApi"
WIKI_SUMMARY_API = "https://zh.wikipedia.org/api/rest_v1/page/summary"
WIKI_SEARCH_API = "https://zh.wikipedia.org/w/api.php"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://baike.baidu.com/",
}

MOBILE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/17.4 Mobile/15E148 Safari/604.1"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

WIKI_HEADERS = {
    "User-Agent": "BaiduBaikeMCP/0.2.0 (MCP Tool; contact@example.com)",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


class BaiduBaikeClient:
    """Async client managing multi-tiered retrieval for Baidu Baike and fallback knowledge."""

    def __init__(
        self,
        impersonate: str = "chrome124",
        timeout: float = 12.0,
        max_retries: int = 1,
    ) -> None:
        self.impersonate = impersonate
        self.timeout = timeout
        self.max_retries = max_retries
        self._session: Optional[AsyncSession] = None
        self._init_lock = asyncio.Lock()
        self._initialized = False

    def _get_proxy(self) -> Optional[str]:
        return (
            os.environ.get("HTTPS_PROXY")
            or os.environ.get("HTTP_PROXY")
            or os.environ.get("ALL_PROXY")
            or os.environ.get("https_proxy")
            or os.environ.get("http_proxy")
            or os.environ.get("all_proxy")
        )

    async def _get_session(self) -> AsyncSession:
        if self._session is None:
            proxy = self._get_proxy()
            self._session = AsyncSession(
                impersonate=self.impersonate,
                headers=DEFAULT_HEADERS,
                timeout=self.timeout,
                proxy=proxy,
            )
        if not self._initialized:
            async with self._init_lock:
                if not self._initialized:
                    try:
                        # Warm up visitor cookies (e.g. BAIDUID) to bypass desktop challenges
                        await self._session.get(BASE_URL, headers=DEFAULT_HEADERS)
                        self._initialized = True
                    except Exception as exc:
                        logger.debug("Visitor cookie warmup: %s", exc)
                        self._initialized = True
        return self._session

    async def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Search Baidu Baike suggestions with automatic Wikipedia fallback on block."""
        session = await self._get_session()
        encoded = urllib.parse.quote(query.strip())
        url = f"{SUGGEST_API}?wd={encoded}"
        headers = {**DEFAULT_HEADERS, "Referer": BASE_URL}

        for attempt in range(self.max_retries + 1):
            try:
                resp = await session.get(url, headers=headers)
                if resp.status_code == 200 and "百度安全验证" not in resp.text:
                    data = json.loads(resp.text)
                    raw_list = data.get("list", [])
                    results: list[dict[str, Any]] = []
                    for item in raw_list[:limit]:
                        lemma_id = item.get("lemmaId")
                        lemma_title = item.get("lemmaTitle", "").strip()
                        lemma_desc = item.get("lemmaDesc", "").strip()
                        if not lemma_title:
                            continue

                        item_url = (
                            f"{BASE_URL}/item/{urllib.parse.quote(lemma_title)}/{lemma_id}"
                            if lemma_id
                            else f"{BASE_URL}/item/{urllib.parse.quote(lemma_title)}"
                        )
                        results.append(
                            {
                                "lemma_id": lemma_id,
                                "title": lemma_title,
                                "desc": lemma_desc,
                                "url": item_url,
                                "source": "Baidu Baike",
                            }
                        )
                    if results:
                        return results
            except Exception as exc:
                if attempt < self.max_retries:
                    await asyncio.sleep(1.0)
                else:
                    logger.warning("Baidu suggest failed (%s); falling back to Wikipedia search.", exc)

        # Fallback: Chinese Wikipedia full-text search
        return await self._search_wikipedia(query=query, limit=limit)

    async def _search_wikipedia(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        session = await self._get_session()
        encoded = urllib.parse.quote(query.strip())
        url = (
            f"{WIKI_SEARCH_API}?action=query&list=search&srsearch={encoded}"
            f"&srlimit={limit}&utf8=&format=json"
        )
        try:
            resp = await session.get(url, headers=WIKI_HEADERS)
            if resp.status_code == 200:
                data = json.loads(resp.text)
                items = data.get("query", {}).get("search", [])
                results: list[dict[str, Any]] = []
                for item in items:
                    title = item.get("title", "").strip()
                    snippet = re.sub(r"<[^>]+>", "", item.get("snippet", "")).strip()
                    if title:
                        results.append(
                            {
                                "lemma_id": None,
                                "title": title,
                                "desc": snippet,
                                "url": f"https://zh.wikipedia.org/wiki/{urllib.parse.quote(title)}",
                                "source": "中文维基百科 (Baidu受限兜底)",
                            }
                        )
                return results
        except Exception as exc:
            logger.error("Wikipedia search failed: %s", exc)
        return []

    async def get_entry_content(
        self,
        lemma: str,
        lemma_id: Optional[int] = None,
        max_sections: int = 25,
    ) -> str:
        """
        Multi-tiered entry retrieval:
        1. Desktop Baike
        2. Baidu OpenAPI (BaikeLemmaCardApi) + Mobile Baike
        3. Chinese Wikipedia Fallback
        """
        session = await self._get_session()
        encoded_lemma = urllib.parse.quote(lemma.strip())

        # --- Tier 1: Desktop Webpage ---
        desktop_url = (
            f"{BASE_URL}/item/{encoded_lemma}/{lemma_id}"
            if lemma_id
            else f"{BASE_URL}/item/{encoded_lemma}"
        )
        try:
            resp = await session.get(desktop_url, headers={**DEFAULT_HEADERS, "Referer": BASE_URL})
            if resp.status_code == 200 and "百度安全验证" not in resp.text:
                from baidu_baike_mcp.parser import parse_baike_page
                return parse_baike_page(
                    html=resp.text,
                    url=str(resp.url),
                    fallback_lemma=lemma,
                    max_sections=max_sections,
                )
            elif "百度安全验证" in resp.text or resp.status_code == 403:
                logger.warning(
                    "Baidu desktop WAF triggered for '%s' on IP; switching to OpenAPI & Mobile channels.",
                    lemma,
                )
        except Exception as exc:
            logger.warning("Desktop request error for '%s': %s", lemma, exc)

        # --- Tier 2: Baidu Baike Official OpenAPI (BaikeLemmaCardApi) ---
        openapi_data = await self._fetch_openapi(lemma)
        wap_html = await self._fetch_wapbaike(lemma, lemma_id)

        if openapi_data:
            return self._format_openapi_markdown(
                data=openapi_data,
                lemma=lemma,
                wap_html=wap_html,
                max_sections=max_sections,
            )

        # If OpenAPI didn't return data but mobile Baike succeeded
        if wap_html and "百度安全验证" not in wap_html:
            from baidu_baike_mcp.parser import parse_baike_page
            wap_url = f"{WAP_BASE_URL}/item/{encoded_lemma}"
            return parse_baike_page(
                html=wap_html,
                url=wap_url,
                fallback_lemma=lemma,
                max_sections=max_sections,
            )

        # --- Tier 3: Chinese Wikipedia Fallback ---
        wiki_md = await self._fetch_wikipedia_entry(lemma)
        if wiki_md:
            return wiki_md

        # --- Tier 4: Error Report ---
        proxy_hint = (
            "\n提示：若需强制访问百度百科网页端，可在环境变量中配置 `HTTPS_PROXY` 代理。"
            if not self._get_proxy()
            else ""
        )
        return (
            f"未能在百度百科及中文维基百科中找到词条 '{lemma}'，或当前云端 IP 访问完全受限。\n"
            f"建议：调用 `baike_search(query='{lemma}')` 检索相近词条。{proxy_hint}"
        )

    async def _fetch_openapi(self, lemma: str) -> Optional[dict[str, Any]]:
        """Fetch structured encyclopedia card from Baidu's OpenAPI."""
        session = await self._get_session()
        encoded = urllib.parse.quote(lemma.strip())
        url = f"{OPENAPI_CARD_URL}?scope=103&format=json&appid=379020&bk_key={encoded}"
        try:
            resp = await session.get(url, headers=DEFAULT_HEADERS)
            if resp.status_code == 200:
                data = json.loads(resp.text)
                if data.get("title") or data.get("abstract"):
                    return data
        except Exception as exc:
            logger.debug("OpenAPI fetch failed for '%s': %s", lemma, exc)
        return None

    async def _fetch_wapbaike(self, lemma: str, lemma_id: Optional[int] = None) -> Optional[str]:
        """Fetch mobile Baike HTML (often has relaxed WAF rules)."""
        session = await self._get_session()
        encoded = urllib.parse.quote(lemma.strip())
        url = (
            f"{WAP_BASE_URL}/item/{encoded}/{lemma_id}"
            if lemma_id
            else f"{WAP_BASE_URL}/item/{encoded}"
        )
        try:
            resp = await session.get(url, headers=MOBILE_HEADERS)
            if resp.status_code == 200 and "百度安全验证" not in resp.text:
                return resp.text
        except Exception as exc:
            logger.debug("WAP fetch failed for '%s': %s", lemma, exc)
        return None

    async def _fetch_wikipedia_entry(self, lemma: str) -> Optional[str]:
        """Fetch encyclopedia summary from Chinese Wikipedia."""
        session = await self._get_session()
        encoded = urllib.parse.quote(lemma.strip())
        url = f"{WIKI_SUMMARY_API}/{encoded}"
        try:
            resp = await session.get(url, headers=WIKI_HEADERS)
            if resp.status_code == 200:
                data = json.loads(resp.text)
                title = data.get("title") or lemma
                extract = data.get("extract") or "暂无概述。"
                page_url = (
                    data.get("content_urls", {}).get("desktop", {}).get("page")
                    or f"https://zh.wikipedia.org/wiki/{encoded}"
                )
                description = data.get("description")

                lines = [
                    f"# 百科词条: {title}",
                    f"**来源链接**: {page_url} *(来源: 中文维基百科 - 云端抗拦截通道)*",
                    "",
                    "> 💡 **网络说明**: 当前云端工作区 IP 触发了百度安全检查拦截，已自动切换至中文维基百科提供权威条目背景与概述。",
                ]
                if description:
                    lines.append(f"\n> **词条定义**: {description}")

                lines.extend([
                    "\n## 概述 (Summary)",
                    extract,
                ])
                return "\n\n".join(lines)
        except Exception as exc:
            logger.debug("Wikipedia fetch error for '%s': %s", lemma, exc)
        return None

    def _format_openapi_markdown(
        self,
        data: dict[str, Any],
        lemma: str,
        wap_html: Optional[str] = None,
        max_sections: int = 25,
    ) -> str:
        """Format Baidu OpenAPI JSON card (+ optional mobile body) into clean Markdown."""
        title = data.get("title") or data.get("key") or lemma
        desc = data.get("desc", "").strip()
        abstract = data.get("abstract", "").strip() or "暂无概述。"
        url = data.get("url") or f"https://baike.baidu.com/item/{urllib.parse.quote(lemma)}"

        lines = [
            f"# 百度百科: {title}",
            f"**来源链接**: {url} *(来源: 百度百科 OpenAPI 结构化通道)*",
            "",
            "> 🛡️ **云端通道**: 检测到当前网络触发了百度网页验证，已自动切换至百度官方结构化 OpenAPI 通道直接提取摘要与信息框。",
        ]

        if desc:
            lines.append(f"\n> **词条定义**: {desc}")

        lines.extend([
            "\n## 概述 (Summary)",
            abstract,
            "\n## 基本信息 (Infobox)",
        ])

        cards = data.get("card", [])
        if cards:
            for item in cards:
                name = item.get("name")
                val = item.get("value", [])
                val_str = ", ".join(val) if isinstance(val, list) else str(val)
                if name and val_str:
                    lines.append(f"- **{name}**: {val_str}")
        else:
            lines.append("无基本信息。")

        catalogs = data.get("catalog", [])
        if catalogs:
            lines.append("\n## 目录 (Catalog)")
            for i, c in enumerate(catalogs, 1):
                clean_c = c.split(">")[1].split("<")[0] if ">" in c else c
                lines.append(f"{i}. {clean_c}")

        # If we got mobile HTML, parse extra body paragraphs
        if wap_html and "百度安全验证" not in wap_html:
            soup = BeautifulSoup(wap_html, "html.parser")
            paras = soup.select(".para, [class*='para'], p")
            body_paras: list[str] = []
            for p in paras:
                text = p.get_text(strip=True)
                if len(text) >= 25 and not any(text in b for b in body_paras[-2:]):
                    body_paras.append(text)
            if body_paras:
                lines.append("\n## 正文精选 (Body Highlights)")
                lines.append("\n\n".join(body_paras[: max_sections * 2]))

        return "\n\n".join(lines)

    async def close(self) -> None:
        """Close HTTP session."""
        if self._session is not None:
            await self._session.close()
            self._session = None
            self._initialized = False
