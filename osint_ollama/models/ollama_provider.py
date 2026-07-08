#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul  8 19:10:31 2026

@author: joannes
"""

import requests

from odoo import api, fields, models
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class OllamaProvider(models.Model):
    _name = 'ollama.provider'
    _description = 'Provider server configuration'


    name = fields.Char('Name', required=True, default="Local")
    host = fields.Char('Host', required=True, default="http://localhost:11434")
    model_ids = fields.One2many('ollama.model', 'provider_id', string='AI model')

    def action_sync_models(self):
        self.ensure_one()
        url = self.host.rstrip('/') + '/api/tags'
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            raise UserError("Failed to fetch models from %s: %s" % (url, str(e)))

        Capability = self.env['ollama.model.capability']

        for model_data in data.get('models', []):
            details = model_data.get('details', {})

            capability_ids = []
            for cap_name in model_data.get('capabilities', []):
                cap = Capability.search([('name', '=', cap_name)], limit=1)
                if not cap:
                    cap = Capability.create({'name': cap_name})
                capability_ids.append(cap.id)

            model = self.env['ollama.model'].search([
                ('model', '=', model_data.get('model')),
                ('provider_id', '=', self.id),
            ], limit=1)

            vals = {
                'name': model_data.get('name'),
                'model': model_data.get('model'),
                'size': model_data.get('size'),
                'digest': model_data.get('digest'),
                'format': details.get('format'),
                'family': details.get('family'),
                'parameter_size': details.get('parameter_size'),
                'quantization_level': details.get('quantization_level'),
                'context_length': details.get('context_length'),
                'embedding_length': details.get('embedding_length'),
                'capability_ids': [(6, 0, capability_ids)],
            }
            print(vals)
            if model:
                model.write(vals)
            else:
                vals['provider_id'] = self.id
                self.env['ollama.model'].create(vals)

        action = {
            'type': 'ir.actions.act_window',
            'res_model': 'ollama.provider',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('osint_ollama.view_ollama_provider_form').id,
        }
        return action
    
    