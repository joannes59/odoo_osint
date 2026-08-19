#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 18 15:15:55 2026

@author: joannes
"""

import asyncio
from fastmcp import Client

# In-memory server (ideal for testing)
#server = FastMCP("TestServer")
#client = Client(server)

# HTTP server
client = Client("http://127.0.0.1:8000/mcp")

# Local Python script
#client = Client("my_mcp_server.py")

async def main():
    async with client:
        # List available operations
        tools = await client.list_tools()
        resources = await client.list_resources()
        prompts = await client.list_prompts()
        
        print(tools)
        print(resources)
        print(prompts)

        # Execute operations
        #result = await client.call_tool("example_tool", {"param": "value"})
        #print(result)

asyncio.run(main())