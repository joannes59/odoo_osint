# -*- coding: utf-8 -*-

import logging
import requests
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class ServerSearxNG(models.Model):
    """Model representing a SearxNG server instance and its search capabilities."""
    _name = 'searxng.server'
    _description = 'SearxNG Server Configuration'

    name = fields.Char(string='Name', required=True, help='Internal name for this server instance')
    base_url = fields.Char(string='Base URL', required=True, help='e.g., https://searx.example.com')
    timeout = fields.Integer(string='Timeout (seconds)', default=10, help='HTTP request timeout')
    active = fields.Boolean(string='Active', default=True)
