#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 30 12:46:49 2026

@author: joannes
"""

from odoo import models, fields, api


class OsintWebsite(models.Model):
    _name = 'osint.website'
    _description = 'Site Web / Domaine'
    _order = 'name'

    name = fields.Char(
        string='Nom de domaine', 
        required=True, 
        index=True,
        help="Ex: www.wikipedia.org"
    )
    url_ids = fields.One2many(
        'osint.url', 
        'website_id', 
        string='URLs du site'
    )
    url_count = fields.Integer(
        string='Nombre d\'URLs', 
        compute='_compute_url_count'
    )

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Ce nom de domaine existe déjà !')
    ]

    @api.depends('url_ids')
    def _compute_url_count(self):
        for website in self:
            website.url_count = len(website.url_ids)

