#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 18 15:15:55 2026

@author: joannes
"""
import asyncio
from fastmcp import Client

# docker run --rm -p 3000:3000   --add-host=host.docker.internal:host-gateway   -e MCP_HTTP_PORT=3000   -e MCP_HTTP_HOST=0.0.0.0   -e SEARXNG_URL=http://host.docker.internal:8080   isokoliuk/mcp-searxng:latest
# docker run -d   --name web-search-mcp   -p 3000:3000   -e ENABLE_CORS=true   -e CORS_ORIGIN=*   ghcr.io/aas-ee/open-web-search:latest
host = "http://127.0.0.1:3000/mcp"


async def main():

    client = Client(host)

    async with client:

        # Tools
        try:
            tools = await client.list_tools()
            print("\nTOOLS:")
            for tool in tools:
                print(f"  {tool.name}: {tool.description}")
                print(type(tool.inputSchema))

        except Exception as e:
            print(f"\nTOOLS indisponibles: {e}")

        # Resources
        try:
            resources = await client.list_resources()
            print("\nRESOURCES:")
            for resource in resources:
                print(f"  {resource.uri}: {resource.name}")

        except Exception as e:
            print(f"\nRESOURCES indisponibles: {e}")

        # Prompts
        try:
            prompts = await client.list_prompts()
            print("\nPROMPTS:")
            for prompt in prompts:
                print(f"  {prompt.name}: {prompt.description}")

        except Exception as e:
            print(f"\nPROMPTS indisponibles: {e}")


asyncio.run(main())