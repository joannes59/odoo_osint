#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 30 12:47:20 2026

@author: joannes
"""

from odoo import models, fields, api
from urllib.parse import urlparse #, urlunparse
from odoo.exceptions import ValidationError


class OsintUrl(models.Model):
    _name = 'osint.url'
    _description = 'Parsed URL components'
    _order = 'create_date desc'


    name = fields.Char(string='URL',
                       index=True,
                       help="E.g. https://en.wikipedia.org/wiki/Uniform_Resource_Locator")
    
    website_id = fields.Many2one(
        'osint.website',
        string='Website',
        compute='_compute_website',
        ondelete='cascade',
        store=True,
        index=True)
    
    # Metadata
    scheme = fields.Char(string='Scheme', compute='_compute_url', 
                         help="E.g. https")
    path = fields.Char(string='Path', compute='_compute_url',
                       help="E.g. /wiki/Uniform_Resource_Locator ...")
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
        ('undefined', 'Undefined'),
        ('day', 'Day'),
        ('week', 'Week'),
        ('month', 'Month'),
        ('semester', 'semester'),
        ('year', 'Year'),
        ('always', 'Always'),
    ], string='Validity time', default='undefined')
    
    # Data
    title = fields.Char(
        string='Title', 
        index=True
    )
    
    content = fields.Html(
        string='Content', 
        help="Excerpt of the content."
    )
    
    # Media
    thumbnail = fields.Char(
        string='Thumbnail',
        help="Thumbnail image."
    )
    
    img_src = fields.Char(
        string="Image Source",
        help="URL of the image."
    )
    
    audio_src = fields.Char(
        string= "Audio Source",
        help="URL of the audio."
    )
    
    video_src = fields.Char(
        string= "Video Source",
        help="URL of the video."
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
    
        
