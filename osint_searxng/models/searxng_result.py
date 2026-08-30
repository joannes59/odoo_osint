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
    _order = 'score desc, published_date desc' 

    query_id = fields.Many2one('searxng.query', string='Query', required=True)

    # Champs de base
    url = fields.Char(
        string='URL', 
        required=True, 
        index=True,
        help="Lien direct vers le résultat de recherche."
    )
    title = fields.Char(
        string='Titre', 
        required=True, 
        index=True
    )
    content = fields.Html(
        string='Contenu / Extrait', 
        required=True,
        help="Extrait du contenu. Utilise le type Html pour conserver le formatage (gras, etc.) des moteurs de recherche."
    )
    
    # Médias et Images
    thumbnail = fields.Char(
        string='Miniature (Thumbnail)',
        help="Image miniature (URL or Any)."
    )
    img_src = fields.Char(
        string='Source de l\'image',
        help="URL de l'image source."
    )

    # Métadonnées du moteur de recherche
    engine = fields.Char(
        string='Moteur principal', 
        required=True
    )
    engines = fields.Json(
        string='Liste des moteurs',
        help="Liste de tous les moteurs ayant trouvé ce résultat (mappé depuis list[str])."
    )
    template = fields.Char(
        string='Template', 
        required=True
    )
    category = fields.Char(
        string='Catégorie', 
        required=True
    )
    
    # Données techniques et scores
    parsed_url = fields.Json(
        string='URL analysée',
        help="Détails de l'URL découpée (mappé depuis list[str])."
    )
    priority = fields.Char(
        string='Priorité',
        help="Priorité du résultat (souvent une chaîne comme 'high', 'medium')."
    )
    positions = fields.Json(
        string='Positions',
        help="Positions du résultat dans les différents moteurs (mappé depuis list[int])."
    )
    score = fields.Float(
        string='Score', 
        required=True,
        index=True
    )

    # Dates
    published_date = fields.Datetime(
        string='Date de publication',
        index=True,
        help="Date de publication."
    )




