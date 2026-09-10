"""Comprehensive live test for Baidu Baike MCP including cloud-resilient fallback paths."""

import asyncio
from baidu_baike_mcp.server import do_baike_search, do_get_baike_entry
from baidu_baike_mcp.client import BaiduBaikeClient

async def main():
    print("--- 1. Testing baike_search('基层治理') ---")
    search_res = await do_baike_search(query="基层治理", limit=3)
    print(search_res[:250])

    print("\n--- 2. Testing get_baike_entry('全过程人民民主') ---")
    entry_1 = await do_get_baike_entry(lemma="全过程人民民主")
    print(entry_1[:350])

    print("\n--- 3. Testing get_baike_entry('中共中央组织部') ---")
    entry_2 = await do_get_baike_entry(lemma="中共中央组织部")
    print(entry_2[:350])

    print("\n--- 4. Testing simulated WAF block -> OpenAPI fallback ---")
    client = BaiduBaikeClient()
    # Direct OpenAPI test
    openapi_data = await client._fetch_openapi("全过程人民民主")
    assert openapi_data is not None, "OpenAPI failed"
    formatted_openapi = client._format_openapi_markdown(openapi_data, "全过程人民民主")
    print("OpenAPI Fallback Sample Output:")
    print(formatted_openapi[:350])

    print("\n--- 5. Testing simulated total Baidu outage -> Wikipedia fallback ---")
    wiki_entry = await client._fetch_wikipedia_entry("全过程人民民主")
    assert wiki_entry is not None, "Wikipedia fallback failed"
    print("Wikipedia Fallback Sample Output:")
    print(wiki_entry[:350])

    print("\n--- 6. Testing Wikipedia search fallback ---")
    wiki_search = await client._search_wikipedia("基层社会治理", limit=2)
    assert len(wiki_search) > 0, "Wikipedia search failed"
    print("Wikipedia Search Results:")
    for w in wiki_search:
        print(" -", w['title'], "->", w['url'])

    print("\nALL CLOUD-RESILIENT TESTS PASSED!")

if __name__ == "__main__":
    asyncio.run(main())
