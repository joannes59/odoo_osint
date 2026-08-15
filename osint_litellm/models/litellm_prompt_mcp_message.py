# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class LitellmPromptMCPMessage(models.Model):
    _name = 'litellm.prompt.mcp.message'
    _description = 'Prompt MCP Tool Call'
    _order = 'sequence, id'

    prompt_id = fields.Many2one('litellm.prompt', string='Prompt',
                                required=True, ondelete='cascade')
    sequence = fields.Integer('Sequence', default=10)
    tool_name = fields.Char('Tool Name', required=True)
    tool_call_id = fields.Char('Tool Call ID')
    arguments = fields.Text('Arguments')
    result = fields.Text('Result')
    error = fields.Boolean('Error')
    duration = fields.Float('Duration')
