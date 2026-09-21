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
    

    