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
    _description = 'Éléments d\'URL parsée'
    _order = 'create_date desc'

    website_id = fields.Many2one(
        'osint.website', 
        string='Site Web', 
        required=True, 
        ondelete='cascade',
        index=True
    )
    scheme = fields.Char(string='Protocole', help="Ex: https")
    path = fields.Char(string='Chemin', help="Ex: /programme2025/...")
    params = fields.Char(string='Paramètres', help="Paramètres après le chemin (délimité par ;)")
    query = fields.Char(string='Chaîne de requête', help="Paramètres après le ? (tracking, filtres)")
    fragment = fields.Char(string='Fragment / Ancre', help="Partie après le #")
    
    # Champ calculé très utile pour voir l'URL reconstituée
    full_url = fields.Char(
        string='URL Complète', 
        compute='_compute_full_url', 
        store=True
    )

    @api.depends('scheme', 'website_id.name', 'path', 'params', 'query', 'fragment')
    def _compute_full_url(self):
        for url in self:
            # Reconstitution de l'URL selon la norme RFC 3986
            netloc = url.website_id.name or ''
            path = url.path or ''
            params = url.params or ''
            query = url.query or ''
            fragment = url.fragment or ''
            
            # urlunparse attend un tuple de 6 éléments
            parsed_tuple = (url.scheme, netloc, path, params, query, fragment)
            url.full_url = urlunparse(parsed_tuple)

    # Méthode utilitaire pour créer un enregistrement à partir d'une URL brute
    @api.model
    def create_from_raw_url(self, raw_url):
        """Parse une URL brute et crée les enregistrements associés."""
        parsed = urlparse(raw_url)
        
        # 1. Trouver ou créer le Site (Domaine)
        website = self.env['osint.website'].search([('name', '=', parsed.netloc)], limit=1)
        if not website:
            website = self.env['osint.website'].create({'name': parsed.netloc})
            
        # 2. Créer l'URL avec ses composants
        url_vals = {
            'website_id': website.id,
            'scheme': parsed.scheme,
            'path': parsed.path,
            'params': parsed.params,
            'query': parsed.query,
            'fragment': parsed.fragment,
        }
        
        return self.create(url_vals)