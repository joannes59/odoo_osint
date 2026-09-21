# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class FastMCPToolParameter(models.Model):
    _name = 'fastmcp.tool.parameter'
    _description = 'MCP Tool Input Parameter'
    _order = 'sequence, id'

    tool_id = fields.Many2one('fastmcp.tool', string='Tool',
                              required=True, ondelete='cascade')
    name = fields.Char('Name', required=True)
    type = fields.Selection([
        ('string', 'String'),
        ('number', 'Number'),
        ('integer', 'Integer'),
        ('boolean', 'Boolean'),
        ('array', 'Array'),
        ('object', 'Object'),
    ], string='Type', required=True, default='string')
    description = fields.Text('Description')
    required = fields.Boolean('Required')
    sequence = fields.Integer('Sequence')
