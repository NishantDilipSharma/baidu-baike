"""Model Context Protocol (MCP) Server for Baidu Baike (百度百科) with cloud-resilient fallbacks."""

from __future__ import annotations

import logging
import re
import urllib.parse
from typing import Optional

try:
    from mcp.server import MCPServer
    from mcp_types import ToolAnnotations

    READ_ONLY = ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    )
    USE_MCPSERVER = True
except ImportError:
    from mcp.server.fastmcp import FastMCP  # type: ignore[no-redef]
    USE_MCPSERVER = False

from baidu_baike_mcp.client import BaiduBaikeClient

logger = logging.getLogger("baidu_baike_mcp")

client = BaiduBaikeClient()


async def do_baike_search(query: str, limit: int = 5) -> str:
    """Search Baidu Baike for matching lemmas."""
    query = query.strip()
    if not query:
        return "Error: query cannot be empty."

    limit = max(1, min(limit, 10))
    results = await client.search(query=query, limit=limit)

    if not results:
        return (
            f"未找到与 '{query}' 匹配的百科词条建议。\n"
            f"建议：可以直接调用 `get_baike_entry(lemma='{query}')` 尝试直接检索同名词条。"
        )

    first_source = results[0].get("source", "Baidu Baike")
    lines: list[str] = [f"### 百科搜索建议: '{query}' (共 {len(results)} 条, 来源: {first_source})"]
    for idx, item in enumerate(results, 1):
        title = item["title"]
        desc = item["desc"] or "无描述"
        lemma_id = item.get("lemma_id")
        url = item["url"]
        id_str = f" (ID: `{lemma_id}`)" if lemma_id else ""
        lines.append(
            f"{idx}. **[{title}]({url})**{id_str}\n"
            f"   - 简介: {desc}"
        )

    lines.append(
        "\n> 提示: 获取词条完整正文与结构化信息，请调用 `get_baike_entry(lemma='<标题>')`。"
    )
    return "\n".join(lines)


async def do_get_baike_entry(
    lemma: str,
    lemma_id: Optional[int] = None,
    max_sections: int = 25,
) -> str:
    """Fetch and parse an encyclopedia entry, with automatic URL parsing, OpenAPI, and Wikipedia fallbacks."""
    lemma = lemma.strip()
    if not lemma:
        return "Error: lemma name cannot be empty."

    # Robust URL normalization: accept full URLs or item paths
    if "baike.baidu.com/item/" in lemma or lemma.startswith("/item/") or lemma.startswith("item/"):
        match = re.search(r"item/([^/?#]+)(?:/(\d+))?", lemma)
        if match:
            extracted_lemma = urllib.parse.unquote(match.group(1))
            extracted_id = int(match.group(2)) if match.group(2) else None
            lemma = extracted_lemma
            if lemma_id is None and extracted_id is not None:
                lemma_id = extracted_id
    elif lemma.startswith("http://") or lemma.startswith("https://"):
        parts = lemma.rstrip("/").split("/")
        if parts:
            lemma = urllib.parse.unquote(parts[-1])

    # Retrieve entry content using multi-tier fallback (Desktop -> OpenAPI/Mobile -> Wikipedia)
    content = await client.get_entry_content(
        lemma=lemma,
        lemma_id=lemma_id,
        max_sections=max_sections,
    )

    # Self-healing fallback: if specific ID is 404/obsolete, fallback to base lemma name
    if "未找到词条" in content and lemma_id is not None:
        logger.info("Lemma '%s' with id %s returned 404; retrying with base lemma.", lemma, lemma_id)
        content = await client.get_entry_content(
            lemma=lemma,
            lemma_id=None,
            max_sections=max_sections,
        )

    return content


def create_server():
    """Create and configure the MCP server instance."""
    if USE_MCPSERVER:
        server = MCPServer(
            name="baidu-baike",
            title="Baidu Baike MCP",
            description="Login-free search and structured entry retrieval from Baidu Baike (百度百科) with cloud-resilient fallbacks.",
            version="0.2.0",
        )

        @server.tool(
            name="baike_search",
            title="Search Baidu Baike",
            description=(
                "Search Baidu Baike (百度百科) for lemmas matching a query keyword or phrase. "
                "Returns matching lemma titles, lemma IDs, brief descriptions, and entry URLs. "
                "Includes automatic fallback to Chinese Wikipedia if Baidu is unreachable."
            ),
            annotations=READ_ONLY,
        )
        async def baike_search(query: str, limit: int = 5) -> str:
            return await do_baike_search(query, limit)

        @server.tool(
            name="get_baike_entry",
            title="Get Baidu Baike Entry",
            description=(
                "Fetch and parse a Baidu Baike (百度百科) entry by lemma name (or full Baike URL) "
                "and optional lemma ID. Extracts canonical title, summary/abstract, structured infobox "
                "key-values, table of contents, and main body sections in clean Markdown. "
                "Includes automatic OpenAPI and Wikipedia fallbacks if cloud datacenter IPs face anti-bot verification."
            ),
            annotations=READ_ONLY,
        )
        async def get_baike_entry(
            lemma: str,
            lemma_id: Optional[int] = None,
            max_sections: int = 25,
        ) -> str:
            return await do_get_baike_entry(lemma, lemma_id, max_sections)

        return server
    else:
        mcp = FastMCP("baidu-baike")

        @mcp.tool()
        async def baike_search(query: str, limit: int = 5) -> str:
            """Search Baidu Baike for lemmas matching a query keyword or phrase."""
            return await do_baike_search(query, limit)

        @mcp.tool()
        async def get_baike_entry(
            lemma: str,
            lemma_id: Optional[int] = None,
            max_sections: int = 25,
        ) -> str:
            """Fetch and parse a Baidu Baike entry."""
            return await do_get_baike_entry(lemma, lemma_id, max_sections)

        return mcp


def main() -> None:
    """Run the MCP server over stdio."""
    server = create_server()
    if USE_MCPSERVER:
        server.run("stdio")
    else:
        server.run(transport="stdio")


if __name__ == "__main__":
    main()
