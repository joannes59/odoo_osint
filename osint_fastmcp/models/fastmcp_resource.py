# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class FastMCPResource(models.Model):
    _name = 'fastmcp.resource'
    _description = 'MCP Resource'
    _order = 'name'

    mcp_server_id = fields.Many2one('fastmcp.server', string='MCP Server',
                                    required=True, ondelete='cascade')
    uri = fields.Char('URI', required=True)
    name = fields.Char('Name')
    title = fields.Char('Title')
    description = fields.Text('Description')
    mime_type = fields.Char('Mime Type')
    size = fields.Integer('Size')

