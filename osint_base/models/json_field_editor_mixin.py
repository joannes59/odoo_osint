#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 24 18:03:07 2026

@author: joannes
"""
from odoo import models, _
from odoo.exceptions import UserError


class JsonFieldEditorMixin(models.AbstractModel):
    _name = 'json.field.editor.mixin'
    _description = "Mixin - open JSON editor"

    def action_edit_json_field(self):
        self.ensure_one()
        field_name = self.env.context.get('field_name')
        if not field_name:
            raise UserError(_("No JSON field specified."))

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'json.editor.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_model': self._name,
                'default_res_id': self.id,
                'default_field_name': field_name,
            },
        }