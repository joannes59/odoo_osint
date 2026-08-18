# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class LitellmMCPPrompt(models.Model):
    _name = 'litellm.mcp.prompt'
    _description = 'MCP Prompt'
    _order = 'name'

    mcp_server_id = fields.Many2one('litellm.mcp.server', string='MCP Server',
                                    required=True, ondelete='cascade')
    name = fields.Char('Name', required=True)
    title = fields.Char('Title')
    description = fields.Text('Description')
    arguments = fields.Json('Arguments')
    prompt_ids = fields.Many2many('litellm.prompt', string='Prompts')
