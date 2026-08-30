#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 30 12:46:49 2026

@author: joannes
"""

from odoo import models, fields, api


class OsintWebsite(models.Model):
    _name = 'osint.website'
    _description = 'Website / Domain'
    _order = 'name'

    name = fields.Char(
        string='website', 
        required=True, 
        index=True,
        help="Ex: flipboard.com"
    )
    url_ids = fields.One2many(
        'osint.url', 
        'website_id', 
        string='Website URLs'
    )
    url_count = fields.Integer(
        string='Number of URLs', 
        compute='_compute_url_count'
    )

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'This domain name already exists!')
    ]

    @api.depends('url_ids')
    def _compute_url_count(self):
        for website in self:
            website.url_count = len(website.url_ids)

