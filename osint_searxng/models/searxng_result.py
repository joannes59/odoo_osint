#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 25 17:23:12 2026

@author: joannes
"""

from odoo import models, fields, api

class SearxngResult(models.Model):
    """ SearxNG search result."""
    _name = 'searxng.result'
    _description = 'SearxNG search result'
    _order = 'score desc, date desc' 

    query_id = fields.Many2one('searxng.query', string='Query', required=True)    
    url_id = fields.Many2one('osint.url', string='URL')
    website_id = fields.Many2one('osint.website', string="Website",
                                 related="url_id.website_id")
  

    # Search engine metadata
    engine = fields.Char(
        string='Main Engine', 
    )
    
    score = fields.Float(
        string='Score', 
        required=True,
        index=True
    )
    
    # Dates
    date = fields.Datetime(string="Date", default=fields.Datetime.now)



