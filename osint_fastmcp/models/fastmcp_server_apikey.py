# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class FastMCPServerApikey(models.Model):
    _name = 'fastmcp.server.apikey'
    _description = 'MCP Server API Key'

    name = fields.Char('Name', required=True)
    key = fields.Char('API Key', required=True)
    server_id = fields.Many2one('fastmcp.server', string='MCP Server', required=True, ondelete='cascade')
    user_ids = fields.Many2many('res.users', string='Authorized Users')
    group_ids = fields.Many2many('res.groups', string='Authorized Groups')
