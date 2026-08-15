# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class LitellmMCPTool(models.Model):
    _name = 'litellm.mcp.tool'
    _description = 'MCP Tool'
    _order = 'name'

    mcp_server_id = fields.Many2one('litellm.mcp.server', string='MCP Server',
                                    required=True, ondelete='cascade')
    name = fields.Char('Name', required=True)
    title = fields.Char('Title')
    description = fields.Text('Description')
    input_schema = fields.Json('Input Schema')
    output_schema = fields.Json('Output Schema')
    annotations = fields.Json('Annotations')
    prompt_ids = fields.Many2many('litellm.prompt', string='Prompts')

    def _to_mcp_tool(self):
        """ Rebuild an mcp.types.Tool object from the stored fields. """
        try:
            from mcp.types import Tool as MCPTool
        except ImportError:
            return None
        return MCPTool(
            name=self.name,
            title=self.title or None,
            description=self.description or None,
            inputSchema=self.input_schema or {'type': 'object', 'properties': {}},
            outputSchema=self.output_schema or None,
            annotations=self.annotations or None,
        )
