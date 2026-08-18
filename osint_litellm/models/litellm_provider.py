#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul  8 19:10:31 2026

@author: joannes.landy
"""

import litellm
import requests

from odoo import api, fields, models
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)

litellm_provider_list = [(provider.name, provider.name) for provider in litellm.provider_list]


class LitellmProvider(models.Model):
    _name = 'litellm.provider'
    _description = 'Provider server configuration'

    name = fields.Char('Name', required=True)
    litellm_provider = fields.Selection(litellm_provider_list, string="configuration", required=True, default="OLLAMA")

    host = fields.Char('Host', required=False, 
                       help="For example, local ollama use this address: http://localhost:11434")
    api_type = fields.Selection(
        [("ollama", "ollama"), ("openai", "openai"), ("gemini", "gemini")],
        string="API Type", default="openai",
        help="Type of API, use to authentification, function...")
    need_api_key = fields.Boolean("Need API Key")
    model_ids = fields.One2many('litellm.model', 'provider_id', string='AI model')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('done', 'Done'),
    ], string='State', default='draft', required=True)


    def action_update_providers(self):
        """ Update provider configuration."""
        pass
    
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'litellm.provider',
            'view_mode': 'list',
        }        
                
    def get_apikey(self):
        """ Return api key to use with this model, depend on user """
        self.ensure_one()
        user = self.env.user
        api_key = None
        
        domain_0 = [('provider_id', '=', self.id)]
        domain_1 = domain_0 + [('user_ids', 'in', user.ids)]
        domain_2 = domain_0 + [('group_ids', 'in', user.group_ids.ids)]
            
        for domain in [domain_1, domain_2]:
            api_key_ids = self.env['litellm.provider.apikey'].search(domain)
        
            if api_key_ids:
                api_key = api_key_ids[0].key
                break

        return api_key
              
    def get_models(self, timeout=30):
        """ Get modeles availables on provider. """
        self.ensure_one()
        url = self.host.rstrip('/')
        headers={}
         
        if self.api_type == "ollama":
            url += '/api/tags'
        elif self.api_type == "openai":
            url += '/models'
            
            api_key = self.get_apikey()
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
        else:
            # TODO: add gemini and more
            pass
        
            
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response    
        
    def action_sync_models(self):
        """ Action to complete models informations of a provider """
        
        for provider in self:
            
            try:
                response = provider.get_models()
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                raise UserError(f"Failed to fetch models from {provider.name}\n{e}")
                data = {}

            model_data_list = data.get('models') or  data.get('data') or []
            
            def model_data_get(model_data, field_list=[]):
                """ return first value defined in the dic """
                for field_name in field_list:                        
                    if model_data.get(field_name):
                        return model_data.get(field_name)
                return False
            
            for model_data in model_data_list:
                     
                model_key = model_data_get(model_data, ['model', 'id']) or '?'
                name =  model_data_get(model_data, ['name']) or model_key
    
                model_ids = self.env['litellm.model'].search([
                    ('model', '=', model_key),
                    ('provider_id', '=', self.id),
                ], limit=1)
    
                vals = {
                    'name':name,
                    'model': model_key,
                    'description': model_data,
                }

                if model_ids:
                    model_ids.write(vals)
                else:
                    vals['provider_id'] = self.id
                    self.env['litellm.model'].create(vals)

        action = {
            'type': 'ir.actions.act_window',
            'res_model': 'litellm.provider',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('osint_litellm.view_litellm_provider_form').id,
        }
        return action
    
    