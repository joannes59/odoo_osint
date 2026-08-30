#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 30 12:47:20 2026

@author: joannes
"""

from odoo import models, fields, api
from urllib.parse import urlparse, urlunparse


class OsintUrl(models.Model):
    _name = 'osint.url'
    _description = 'Parsed URL components'
    _order = 'create_date desc'


    name = fields.Char(string='URL',
                       index=True,
                       help="Ex: https://fr.wikipedia.org/wiki/Uniform_Resource_Locator")
    
    website_id = fields.Many2one(
        'osint.website',
        string='Website',
        compute='_compute_url',
        ondelete='cascade',
        store=True,
        index=True)
    
    scheme = fields.Char(string='Scheme', compute='_compute_url', 
                         help="Ex: https")
    path = fields.Char(string='Path', compute='_compute_url',
                       help="Ex: /wiki/Uniform_Resource_Locator ...")
    params = fields.Char(string='Params', compute='_compute_url',
                         help="Parameters after the path (delimited by ;)")
    query = fields.Char(string='Query string', compute='_compute_url',
                        help="Parameters after the ? (tracking, filters)")
    fragment = fields.Char(string='Fragment / Anchor', compute='_compute_url',
                           help="Part after the #")

    @api.depends('name')
    def _compute_url(self):
        """Parse a raw URL and create the associated records."""
        for url in self:
            
            parsed = urlparse(url.name)
        
            # 1. Find or create the Website (Domain)
            website = self.env['osint.website'].search([('name', '=', parsed.netloc)], limit=1)
            if not website:
                website = self.env['osint.website'].create({'name': parsed.netloc})
                
            # 2. Create the URL with its components
            url.website_id =  website.id
            url.scheme = parsed.scheme
            url.path = parsed.path
            url.params = parsed.params
            url.query = parsed.query
            url.fragment = parsed.fragment
    
        
