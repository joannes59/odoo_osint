#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 30 12:47:20 2026

@author: joannes
"""

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    is_ai_agent = fields.Boolean(
        string="Agent IA",
        default=False,
    )
    