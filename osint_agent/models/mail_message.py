#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep  4 23:36:28 2026

@author: joannes
"""

from odoo import api, models


class MailMessage(models.Model):
    _inherit = "mail.message"

    @api.model_create_multi
    def create(self, vals_list):

        messages = super().create(vals_list)

        for message in messages:
            pass

        return messages
    