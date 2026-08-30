#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 25 17:21:52 2026

@author: joannes
"""

from odoo import models, fields, api
import requests



class SearxngQuery(models.Model):
    """Persistent log of all searches performed via SearxNG."""
    _name = 'searxng.query'
    _description = 'SearxNG query History'
    _order = 'create_date desc'
    
    name = fields.Char(string='Query', required=True, index=True)
    server_id = fields.Many2one(
        'searxng.server', 
        string='Server', 
        required=True, 
        default=lambda self: self.env['searxng.server'].search([], limit=1)
    )
    
    categories = fields.Selection([
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
    
    language = fields.Char(string='Language', default='all')
    time_range = fields.Selection([
        ('day', 'Day'),
        ('week', 'Week'),
        ('month', 'Month'),
        ('year', 'Year'),
    ], string='Time Range')
    
    result_ids = fields.One2many('searxng.result', 'query_id', string="Results")
    result_count = fields.Integer(string='Number of Results')
    
    # Optional: Store a summary of the top result for quick preview
    top_result_title = fields.Char(string='Top Result Title')
    top_result_url = fields.Char(string='Top Result URL')
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.user.lang:
            pass
            #res['language'] = self.env.user.lang[:2]
        return res
    
    def action_send(self):
        """ send query to server SearXNG """
        
        params = {
             'q': self.name,
             'format': 'json',
        }
        if self.categories:
            params['categories'] = self.categories
        if self.language:
            params['language'] = self.language
        if self.time_range:
            params['time_range'] = self.time_range

        try:
            url = self.server_id.base_url + "/search"
            response = requests.get(url, params=params, timeout=self.server_id.timeout)
            response.raise_for_status()
            print(response.json())

            # response: [{'query', 'results', 'answers', 'corrections', 'infoboxes', 'suggestions', 'unresponsive_engines'}, ...]
            
            for result in response.json().get('results'):
                
                list_result_field = ['template', 'title', 'content', 'img_src', 'iframe_src', 'audio_src', 'thumbnail', 'publishedDate',
                                  'pubdate', 'length', 'views', 'author', 'metadata', 'priority', 'engines', 'open_group', 'close_group', 
                                  'positions', 'score', 'category', 'url', 'engine', 'parsed_url']
                
                data = {}
                for result_field in list_result_field:
                    data[result_field] = result.get(result_field)
                    
                print(data)
                
                
                

                
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Erreur de communication avec SearxNG : {e}") from e
             
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'searxng.query',
            'res_id': self.id,
            'view_mode': 'form',
        }      
             