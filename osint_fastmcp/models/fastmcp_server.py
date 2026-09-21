# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).


import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

import asyncio
from contextlib import AsyncExitStack
import httpx
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamable_http_client


class FastMCPServer(models.Model):
    _name = 'fastmcp.server'
    _description = 'MCP Server'

    name = fields.Char('Name', required=True)
    server_url = fields.Char('Server URL', help="URL of the MCP server (http or sse transport).")
    apikey_ids = fields.One2many('fastmcp.server.apikey', 'server_id', string='API Keys')
    built_in = fields.Boolean('built_in', help='Built in server is inside Odoo, no host needed')
    
    tool_ids = fields.One2many('fastmcp.tool', 'mcp_server_id', string='Tools')
    resource_ids = fields.One2many('fastmcp.resource', 'mcp_server_id', string='Resources')
    prompt_ids = fields.One2many('fastmcp.prompt', 'mcp_server_id', string='Prompts')

    tool_count = fields.Integer('Tool Count', compute='_compute_capability_count')
    resource_count = fields.Integer('Resource Count', compute='_compute_capability_count')
    prompt_count = fields.Integer('Prompt Count', compute='_compute_capability_count')
    
    active = fields.Boolean('Active', default=True)

    def get_tools(self):
        """ return all tools in llm client schema """
        # https://modelcontextprotocol.io/specification/2026-07-28/server/tools
        
        result = []
        for tool in self.tool_ids:
            result += tool.get_llm_schema()
        return result

    @api.depends('tool_ids', 'resource_ids', 'prompt_ids')
    def _compute_capability_count(self):
        for record in self:
            record.tool_count = len(record.tool_ids)
            record.resource_count = len(record.resource_ids)
            record.prompt_count = len(record.prompt_ids)

    @api.model
    def _run_async_mcp_fetch(self, server_url, apikey=None):
        """Internal method to execute asynchronous code."""
        headers = {"Authorization": f"Bearer {apikey}"} if apikey else None
    
        async def _safe_list(call, attr):
            try:
                return getattr(await call(), attr)
            except Exception as e:
                _logger.debug("MCP %s not available: %s", attr, e)
                return []
    
        async def main():
            try:
                async with AsyncExitStack() as stack:
                    if server_url.rstrip("/").endswith("/sse"):
                        streams = await stack.enter_async_context(
                            sse_client(server_url, headers=headers)
                        )
                    else:
                        # Les en-têtes se règlent sur le client httpx
                        http_client = await stack.enter_async_context(
                            httpx.AsyncClient(
                                headers=headers,
                                follow_redirects=True,
                                timeout=httpx.Timeout(30.0, read=300.0),
                            )
                        )
                        streams = await stack.enter_async_context(
                            streamable_http_client(server_url, http_client=http_client)
                        )
    
                    read, write = streams[0], streams[1]
                    session = await stack.enter_async_context(ClientSession(read, write))
                    await session.initialize()
    
                    return {
                        'status': 'success',
                        'tools': await _safe_list(session.list_tools, 'tools'),
                        'resources': await _safe_list(session.list_resources, 'resources'),
                        'prompts': await _safe_list(session.list_prompts, 'prompts'),
                    }
            except Exception as e:
                _logger.error("MCP server connection error: %s", e)
                return {'status': 'error', 'message': str(e)}
    
        return asyncio.run(main())

    def action_fetch_metadata(self):
        """Action triggered by the button to retrieve metadata."""
        self.ensure_one()
        
        if self.built_in:
            return
        
        if not self.server_url:
            raise UserError("Please configure a valid MCP server URL.")

        _logger.info(f"Connecting to MCP server: {self.server_url}")
        if self.apikey_ids:
            # Todo complete the search with user right
            apikey = self.apikey_ids[0].apikey
        else:
            apikey = None
            
        result = self._run_async_mcp_fetch(self.server_url)

        if result['status'] == 'success':
            for tool in result['tools']:
                name = getattr(tool, 'name', None)
                if name:
                    tool_id = self.tool_ids.get_tool_id(self.id, name)
                    tool_id.update_info(tool)
                
            for resource in result['resources']:
                uri = getattr(resource, 'uri', None)
                if uri:
                    resource_id = self.resource_ids.get_resource_id(self.id, str(uri))
                    resource_id.update_info(resource)
                
            for prompt in result['prompts']:
                name = getattr(prompt, 'name', None)
                if name:
                    prompt_id = self.prompt_ids.get_prompt_id(self.id, name)
                    prompt_id.update_info(prompt)
        else:
            raise UserError(f"Failed to retrieve MCP data: {result['message']}")


