#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 30 12:46:49 2026

@author: joannes
"""

from odoo import models, fields, api

from html.parser import HTMLParser
from urllib.parse import urljoin

import requests


class FaviconLinkParser(HTMLParser):
    """Extract icons URLs from the <link rel="icon"> tags of a page."""

    def __init__(self):
        super().__init__()
        self.icon_urls = []

    def handle_starttag(self, tag, attrs):
        if tag != 'link':
            return
        attrs = dict(attrs)
        rel = (attrs.get('rel') or '').lower()
        href = attrs.get('href')
        if href and 'icon' in rel:
            self.icon_urls.append(href)


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
    favicon = fields.Binary(
        string='Favicon',
        attachment=True,
        help="Favicon of the website (fetched from https://<domain>/favicon.ico)."
    )

    @api.depends('url_ids')
    def _compute_url_count(self):
        for website in self:
            website.url_count = len(website.url_ids)

    def action_fetch_favicon(self):
        """Fetch the favicon of each website. Try HTTPS, skip on error."""
        for website in self:
            if not website.name:
                continue

            base_url = "https://%s" % website.name.strip()
            headers = {"User-Agent": "Mozilla/5.0"}

            # 1. Look for <link rel="icon" ...> in the homepage
            icon_urls = []
            try:
                response = requests.get(
                    base_url,
                    timeout=10,
                    headers=headers,
                )
                response.raise_for_status()
                parser = FaviconLinkParser()
                parser.feed(response.text)
                icon_urls = [urljoin(base_url, href) for href in parser.icon_urls]
            except requests.exceptions.RequestException:
                pass

            # 2. Fall back to the default location
            icon_urls.append(urljoin(base_url, "/favicon.ico"))

            # 3. Download the first reachable icon
            for icon_url in dict.fromkeys(icon_urls):
                try:
                    icon_response = requests.get(
                        icon_url,
                        timeout=10,
                        headers=headers,
                    )
                    icon_response.raise_for_status()
                    website.favicon = icon_response.content
                    break
                except requests.exceptions.RequestException:
                    continue

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