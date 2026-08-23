#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug 22 20:39:18 2026

@author: joannes
"""

from odoo import api, fields, models
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class LitellmPrompt(models.Model):
    _inherit = 'litellm.prompt'
    
    mcp_ids = fields.Many2many('fastmcp.server', string='MCP server')

    def get_tools(self):
        """ Get the tools available """
        result = super().get_tools()
        result += self.mcp_ids.get_tools()
        
        return result
    