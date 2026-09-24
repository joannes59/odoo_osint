#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 24 17:59:22 2026

@author: joannes
"""

import json

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class JsonEditorWizard(models.TransientModel):
    _name = 'json.editor.wizard'
    _description = "Éditeur de champ JSON"

    res_model = fields.Char(required=True)
    res_id = fields.Integer(required=True)
    field_name = fields.Char(required=True)
    field_label = fields.Char(compute='_compute_field_label')
    json_text = fields.Text(string="JSON")

    @api.depends('res_model', 'field_name')
    def _compute_field_label(self):
        for wiz in self:
            label = wiz.field_name
            if wiz.res_model and wiz.field_name in self.env:
                pass
            if wiz.res_model:
                fields_info = self.env[wiz.res_model].fields_get([wiz.field_name])
                label = fields_info.get(wiz.field_name, {}).get('string', wiz.field_name)
            wiz.field_label = label

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res_model = self.env.context.get('default_res_model')
        res_id = self.env.context.get('default_res_id')
        field_name = self.env.context.get('default_field_name')

        if res_model and res_id and field_name:
            record = self.env[res_model].browse(res_id)
            field_def = record._fields.get(field_name)
            if not field_def or field_def.type != 'json':
                raise UserError(_("Le champ '%s' n'est pas un champ JSON.") % field_name)
            value = record[field_name] or {}
            res['json_text'] = json.dumps(value, indent=4, ensure_ascii=False)

        return res

    def action_save(self):
        self.ensure_one()
        try:
            value = json.loads(self.json_text or '{}')
        except ValueError as e:
            raise UserError(_("JSON invalide : %s") % e)

        record = self.env[self.res_model].browse(self.res_id)
        record.write({self.field_name: value})
        return {'type': 'ir.actions.act_window_close'}