# OSINT MCP Utility

Odoo module acting as a proxy between Odoo and MCP (Model Context Protocol) servers.

## Features

- Registers MCP servers (`fastmcp.server`) with their URL and API keys.
- Fetches and stores the server capabilities in the database:
  - Tools (`fastmcp.tool`)
  - Resources (`fastmcp.resource`)
  - Prompts (`fastmcp.prompt`)
- Exposes MCP tools as LLM tool schemas, usable by the `osint_litellm` prompts.
- API keys can be restricted to given users and groups.

## Models

| Model                 | Purpose                                          |
| --------------------- | ------------------------------------------------ |
| `fastmcp.server`      | MCP server configuration and capability sync     |
| `fastmcp.server.apikey` | API keys with user/group restrictions        |
| `fastmcp.tool`        | Tool metadata and LLM schema conversion          |
| `fastmcp.resource`    | Resource metadata                                |
| `fastmcp.prompt`      | Prompt metadata and arguments                    |
| `litellm.prompt`      | Extension: links prompts to MCP servers (`mcp_ids`) |

## How it works

1. Configure an MCP server (`Server URL`).
2. Click **Sync Capabilities** to connect and list tools/resources/prompts.
3. In an OSINT LiteLLM prompt, add the MCP server to `mcp_ids` to expose its tools to the AI model.

## Test client / server

The `test_mcp/` folder contains standalone examples:

- `mcp_server.py` — a small FastMCP filesystem server (via HTTP on port `8000`).
- `mcp_client.py` — a client that lists the tools, resources and prompts of a server (default `http://127.0.0.1:3000/mcp`).

Dependencies: `fastmcp`.