# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class LitellmProviderApikey(models.Model):
    _name = 'litellm.provider.apikey'
    _description = 'Provider API Key'

    name = fields.Char('Name', required=True)
    key = fields.Char('API Key', required=True)
    provider_id = fields.Many2one('litellm.provider', string='Provider', required=True)
    model_id = fields.Many2one('litellm.model', string='Model')
    user_ids = fields.Many2many('res.users', string='Authorized Users')
    group_ids = fields.Many2many('res.groups', string='Authorized Groups')
