# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class OllamaModelCapability(models.Model):
    _name = 'ollama.model.capability'
    _description = 'AI Model Capability'

    name = fields.Char('Name', required=True)
