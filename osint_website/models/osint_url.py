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
        compute='_compute_website',
        ondelete='cascade',
        store=True,
        index=True)
    
    # Metadata
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
    
    category = fields.Selection([
        ('general', 'general'),
        ('images', 'images'),
        ('videos', 'videos'),
        ('news', 'news'),
        ('map', 'map'),
        ('music', 'music'),
        ('it', 'it'),
        ('science', 'science'),
        ('files', 'files'),
        ('social media', 'Social media'),
    ], string='Categories', default='general')
    
    date = fields.Datetime(string="Date", default=fields.Datetime.now)
    
    time_update = fields.Selection([
        ('never', 'Never'),
        ('day', 'Day'),
        ('week', 'Week'),
        ('month', 'Month'),
        ('semester', 'semester'),
        ('year', 'Year'),
    ], string='Time Range', default='never')
    
    # Data
    content = fields.Html(
        string='Extrait', 
        help="Extrait du contenu."
    )
    
    # Médias
    thumbnail = fields.Char(
        string='Thumbnail',
        help="Image miniature."
    )
    img_src = fields.Char(
        string="Source de l'image",
        help="URL de l'image."
    )
    
    audio_src = fields.Char(
        string= "Source de l'audio",
        help="URL de l'audio."
    )
    
    video_src = fields.Char(
        string= "Source de la vidéo",
        help="URL de la vidéo."
    )
    
    @api.constrains("website_id")
    def _check_unique_website(self):
        for record in self:
            if record.website_id:
                duplicate = self.search([
                    ("website_id", "=", record.website_id.name),
                    ("id", "!=", record.id),
                ], limit=1)
    
                if duplicate:
                    raise ValidationError(
                        "Cet élément est déjà utilisé."
                    )
    
    @api.depends('name')
    def _compute_website(self):
        """Parse a raw URL and create the associated website."""
        for url in self:
            
            parsed = urlparse(url.name)
        
            # 1. Find or create the Website (Domain)
            website = self.env['osint.website'].search([('name', '=', parsed.netloc)], limit=1)
            if not website:
                website = self.env['osint.website'].create({'name': parsed.netloc})
                
            url.website_id =  website.id   

    @api.depends('name')
    def _compute_url(self):
        """Parse a raw URL and create the associated records."""
        for url in self:
            
            parsed = urlparse(url.name)

            # 2. Create the URL with its components
            url.scheme = parsed.scheme
            url.path = parsed.path
            url.params = parsed.params
            url.query = parsed.query
            url.fragment = parsed.fragment
    
        
