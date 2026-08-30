#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug 22 16:13:57 2026

@author: joannes
"""
from odoo import api, fields, models
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class LitellmPromptMessage(models.Model):
    _name = 'litellm.prompt.message'
    _description = 'Prompt Message'
    _order = 'sequence, id'

    
    prompt_id = fields.Many2one('litellm.prompt', string='Prompt',
                                required=True, ondelete='cascade')
    sequence = fields.Integer('Sequence', default=10)
    role = fields.Selection([
        ('system', 'System'),
        ('developer', 'Developer'),
        ('tool', 'Tool'),
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ], string='Role', required=True, default='user')
    
    content = fields.Text('Content')
    
    prompt_eval_count = fields.Float("Token in")
    eval_count = fields.Float("Total Token")
    cost = fields.Float("Cost")
    total_duration = fields.Float("Duration")
    
    tool_call_id = fields.Char('Tool call ID')
    tool_calls = fields.Json('Tool calls')
    

        
        
    