#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul  8 19:10:31 2026

@author: joannes
"""

from odoo import api, fields, models
from odoo.exceptions import UserError
from litellm import get_supported_openai_params, get_model_info
import json
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
    response_format = fields.Boolean('Response Format')
    json_schema = fields.Boolean('JSON Schema')
    
    description_pretty = fields.Text(
            string="Description",
            compute="_compute_description_pretty"
        )

    @api.depends("description")
    def _compute_description_pretty(self):
        for rec in self:
            description_pretty = ""
            
            if rec.description:
                description_pretty = json.dumps(
                        rec.description,
                        indent=4,
                        ensure_ascii=False
                    )
            rec.description_pretty = description_pretty
                    
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

    def action_update_model_support(self):
        """ Update response_format and json_schema fields from litellm."""

        for model in self:
            custom_llm_provider = model.provider_id.litellm_provider.lower()
    
            try:
                params = get_supported_openai_params(
                    model=model.model,
                    custom_llm_provider=custom_llm_provider,
                )
                model.response_format = 'response_format' in params
                print(model.model,type(params), params)
                
                info = get_model_info(
                    model=model.model,
                    custom_llm_provider=custom_llm_provider,
                    )
                print('-------------------------')
                print(info)
                
                
            except Exception as e:
                raise UserError("Failed to get supported params: %s" % str(e))
    



        