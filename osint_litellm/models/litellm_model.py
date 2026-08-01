#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul  8 19:10:31 2026

@author: joannes
"""

from odoo import api, fields, models
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class LitellmModel(models.Model):
    _name = 'litellm.model'
    _description = 'AI model'


    name = fields.Char('Name')
    model = fields.Char('Model')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('done', 'Done'),
    ], string='State', default='draft', required=True)
    provider_id = fields.Many2one('litellm.provider', string='AI server', required=True)
    description = fields.Json('Description')
    size = fields.Float('Size')
    digest = fields.Char('Digest')
    format = fields.Char('Format')
    family = fields.Char('Family')
    parameter_size = fields.Char('Parameter Size')
    quantization_level = fields.Char('Quantization Level')
    context_length = fields.Integer('Context Length')
    embedding_length = fields.Integer('Embedding Length')
    capability_ids = fields.Many2many('litellm.model.capability', string='Capabilities')
    
    def get_apikey(self):
        """ Return api key to use with this model, depend on user """
        self.ensure_one()
        user = self.env.user
        api_key = None
        
        domain = [
            ('provider_id', '=', self.provider_id.id),
            '|',
            ('model_id', '=', False),
            ('model_id', '=', self.id),
            '|',
            ('user_ids', 'in', user.ids),
            ('group_ids', 'in', user.group_ids.ids),
        ]
        
        api_key_ids = self.env['litellm.provider.apikey'].search(domain)
        
        if api_key_ids:
            api_key = api_key_ids[0].key

        return api_key
        