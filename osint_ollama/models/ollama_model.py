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


class OllamaModel(models.Model):
    _name = 'ollama.model'
    _description = 'AI model'


    name = fields.Char('Name', required=True)
    model = fields.Char('Model')
    provider_id = fields.Many2one('ollama.provider', string='AI server', required=True)
    description = fields.Char('Description')
    size = fields.Float('Size')
    digest = fields.Char('Digest')
    format = fields.Char('Format')
    family = fields.Char('Family')
    parameter_size = fields.Char('Parameter Size')
    quantization_level = fields.Char('Quantization Level')
    context_length = fields.Integer('Context Length')
    embedding_length = fields.Integer('Embedding Length')
    capability_ids = fields.Many2many('ollama.model.capability', string='Capabilities')
    
    