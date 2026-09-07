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
        string='Website', 
        required=True, 
        index=True,
        help="E.g. flipboard.com"
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

    @api.depends('url_ids')
    def _compute_url_count(self):
        for website in self:
            website.url_count = len(website.url_ids)

    @api.constrains("website_id")
    def _check_unique_website(self):
        for record in self:
            if record.name:
                duplicate = self.search([
                    ("name", "=", name),
                    ("id", "!=", record.id),
                ], limit=1)
    
                if duplicate:
                    raise ValidationError(
                        f"This website is already in created: {record.name}")