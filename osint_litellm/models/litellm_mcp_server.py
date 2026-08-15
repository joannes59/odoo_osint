# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import asyncio
import json
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from litellm.experimental_mcp_client.client import MCPClient
    from litellm.experimental_mcp_client.tools import transform_mcp_tool_to_openai_tool
    from litellm.types.mcp import MCPAuth, MCPTransport
except ImportError:
    MCPClient = None
    transform_mcp_tool_to_openai_tool = None
    MCPAuth = None
    MCPTransport = None


def _to_jsonable(value):
    """ Convert pydantic models (MCP types) into JSON serializable data. """
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {k: _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    if hasattr(value, 'model_dump'):
        return _to_jsonable(value.model_dump())
    return value


class LitellmMCPServer(models.Model):
    _name = 'litellm.mcp.server'
    _description = 'MCP Server'

    name = fields.Char('Name', required=True)
    transport = fields.Selection([
        ('http', 'HTTP (Streamable)'),
        ('sse', 'SSE'),
        ('stdio', 'Standard IO'),
    ], string='Transport', default='http', required=True)
    url = fields.Char('Server URL', help="URL of the MCP server (http or sse transport).")
    command = fields.Char('Command', help="Command to run the MCP server (stdio transport).")
    args = fields.Char('Arguments', help="Command line arguments for the command.")
    env = fields.Json('Environment', help="Environment variables for the stdio process.")
    auth_type = fields.Selection([
        ('none', 'None'),
        ('api_key', 'API Key'),
        ('bearer_token', 'Bearer Token'),
        ('basic', 'Basic Auth'),
        ('authorization', 'Authorization Header'),
        ('oauth2', 'OAuth2'),
    ], string='Auth Type', default='none')
    auth_value = fields.Char('Auth Value', help="Value used for the selected auth type.")
    extra_headers = fields.Json('Extra Headers', help="Additional HTTP headers sent to the server.")
    ssl_verify = fields.Boolean('SSL Verify', default=True)
    active = fields.Boolean('Active', default=True)
    last_sync = fields.Datetime('Last Sync', readonly=True)

    tool_ids = fields.One2many('litellm.mcp.tool', 'mcp_server_id', string='Tools')
    resource_ids = fields.One2many('litellm.mcp.resource', 'mcp_server_id', string='Resources')
    prompt_ids = fields.One2many('litellm.mcp.prompt', 'mcp_server_id', string='Prompts')

    tool_count = fields.Integer('Tool Count', compute='_compute_capability_count')
    resource_count = fields.Integer('Resource Count', compute='_compute_capability_count')
    prompt_count = fields.Integer('Prompt Count', compute='_compute_capability_count')

    @api.depends('tool_ids', 'resource_ids', 'prompt_ids')
    def _compute_capability_count(self):
        for record in self:
            record.tool_count = len(record.tool_ids)
            record.resource_count = len(record.resource_ids)
            record.prompt_count = len(record.prompt_ids)

    @api.constrains('transport', 'url', 'command')
    def _check_config(self):
        for server in self:
            if server.transport in ('http', 'sse') and not server.url:
                raise UserError("Server URL is required for HTTP/SSE transport.")
            if server.transport == 'stdio' and not server.command:
                raise UserError("Command is required for Standard IO transport.")

    def _get_client(self):
        self.ensure_one()
        if not MCPClient:
            raise UserError("The 'litellm' python package is required to use MCP servers.")

        if self.transport == 'stdio':
            args = []
            if self.args:
                try:
                    args = json.loads(self.args) if self.args.strip().startswith('[') else self.args.split()
                except Exception:
                    args = self.args.split()
            stdio_config = {
                'command': self.command,
                'args': args,
                'env': self.env or None,
            }
        else:
            stdio_config = None

        auth_type = None
        if self.auth_type and self.auth_type != 'none' and self.auth_type in MCPAuth.__members__:
            auth_type = MCPAuth[self.auth_type]

        return MCPClient(
            server_url=self.url or '',
            transport_type=MCPTransport[self.transport],
            auth_type=auth_type,
            auth_value=self.auth_value or None,
            stdio_config=stdio_config,
            extra_headers=self.extra_headers or None,
            ssl_verify=self.ssl_verify,
        )

    def action_sync_capabilities(self):
        """ Fetch tools, resources and prompts from the MCP server."""
        for server in self:
            server._sync_capabilities()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'litellm.mcp.server',
            'res_id': self.id,
            'view_mode': 'form',
        }

    def _sync_capabilities(self):
        self.ensure_one()
        if not self.active:
            return self
        try:
            client = self._get_client()
            tools = asyncio.run(client.list_tools())
            resources = asyncio.run(client.list_resources())
            prompts = asyncio.run(client.list_prompts())

            self._update_tools(tools)
            self._update_resources(resources)
            self._update_prompts(prompts)

            self.last_sync = fields.Datetime.now()
        except Exception as e:
            raise UserError("Failed to sync capabilities from MCP server '%s': %s" % (self.name, str(e)))
        return self

    def _update_tools(self, tools_data):
        Tool = self.env['litellm.mcp.tool']
        existing = {tool.name: tool for tool in self.tool_ids}
        updated = []

        for tool_data in tools_data or []:
            if not getattr(tool_data, 'name', None):
                continue
            vals = {
                'mcp_server_id': self.id,
                'name': tool_data.name,
                'title': getattr(tool_data, 'title', None),
                'description': getattr(tool_data, 'description', None),
                'input_schema': getattr(tool_data, 'inputSchema', None),
                'output_schema': getattr(tool_data, 'outputSchema', None),
                'annotations': _to_jsonable(getattr(tool_data, 'annotations', None)),
            }
            tool = existing.get(tool_data.name)
            if tool:
                tool.write(vals)
                updated.append(tool.id)
            else:
                updated.append(Tool.create(vals).id)

        stale = [tool for name, tool in existing.items() if tool.id not in updated]
        if stale:
            stale.unlink()

    def _update_resources(self, resources_data):
        Resource = self.env['litellm.mcp.resource']
        existing = {resource.uri: resource for resource in self.resource_ids}
        updated = []

        for resource_data in resources_data or []:
            if not getattr(resource_data, 'uri', None):
                continue
            vals = {
                'mcp_server_id': self.id,
                'uri': str(resource_data.uri),
                'name': getattr(resource_data, 'name', None),
                'title': getattr(resource_data, 'title', None),
                'description': getattr(resource_data, 'description', None),
                'mime_type': getattr(resource_data, 'mimeType', None),
                'size': getattr(resource_data, 'size', None),
            }
            resource = existing.get(str(resource_data.uri))
            if resource:
                resource.write(vals)
                updated.append(resource.id)
            else:
                updated.append(Resource.create(vals).id)

        stale = [res for uri, res in existing.items() if res.id not in updated]
        if stale:
            stale.unlink()

    def _update_prompts(self, prompts_data):
        Prompt = self.env['litellm.mcp.prompt']
        existing = {prompt.name: prompt for prompt in self.prompt_ids}
        updated = []

        for prompt_data in prompts_data or []:
            if not getattr(prompt_data, 'name', None):
                continue
            vals = {
                'mcp_server_id': self.id,
                'name': prompt_data.name,
                'title': getattr(prompt_data, 'title', None),
                'description': getattr(prompt_data, 'description', None),
                'arguments': _to_jsonable(getattr(prompt_data, 'arguments', None)),
            }
            prompt = existing.get(prompt_data.name)
            if prompt:
                prompt.write(vals)
                updated.append(prompt.id)
            else:
                updated.append(Prompt.create(vals).id)

        stale = [prompt for name, prompt in existing.items() if prompt.id not in updated]
        if stale:
            stale.unlink()

    def get_openai_tools(self):
        """ Return the tools of this server in OpenAI chat completion format. """
        self.ensure_one()
        tools = []
        if transform_mcp_tool_to_openai_tool:
            for tool in self.tool_ids:
                mcp_tool = tool._to_mcp_tool()
                if mcp_tool is None:
                    continue
                try:
                    tools.append(transform_mcp_tool_to_openai_tool(mcp_tool))
                except Exception as e:
                    _logger.warning("Failed to transform MCP tool %s: %s", tool.name, e)
        return tools
