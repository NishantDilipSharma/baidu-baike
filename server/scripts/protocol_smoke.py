"""Simulated external MCP stdio client testing server startup and tool listing."""

import asyncio
import sys
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client import ClientSession

async def main():
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "baidu_baike_mcp"],
        env={"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
    )
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            tool_names = [t.name for t in tools.tools]
            print("Successfully initialized MCP session!")
            print("Registered tools:", tool_names)
            assert "baike_search" in tool_names
            assert "get_baike_entry" in tool_names

            # Call search tool
            res = await session.call_tool("baike_search", {"query": "数字治理", "limit": 2})
            assert not res.is_error
            print("baike_search tool output sample:")
            for content in res.content:
                if hasattr(content, "text"):
                    print(content.text[:200])

    print("\nSTDIO PROTOCOL SMOKE TEST PASSED!")

if __name__ == "__main__":
    asyncio.run(main())
