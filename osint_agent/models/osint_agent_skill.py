#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import markdown
import re
from odoo import api, fields, models


class OsintAgentSkill(models.Model):
    _name = 'osint.agent.skill'
    _description = 'Agent Skill'
    _order = 'sequence, id'

    sequence = fields.Integer('Sequence', default=10)
    name = fields.Char('Name', required=True)
    role = fields.Selection([
        ('system', 'System'),
        ('developer', 'Developer'),
        ('tool', 'Tool'),
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ], string='Role', required=True, default='system')
    description = fields.Text('Description')
    description_pretty = fields.Html(
        string='Description',
        compute='_compute_description_pretty',
        sanitize=False,
    )
    parameter_ids = fields.Many2many(
        'osint.agent.skill.parameter',
        string='Parameters',
    )

    @api.depends('description')
    def _compute_description_pretty(self):
        for rec in self:
            rec.description_pretty = markdown.markdown(rec.description or '')



    #@api.depends('description')
    def extract_parameters(self):
        """ Create parameters used in this skills {{parameter}}."""
        
        for skill in self:
            parameters = re.findall(r"\{\{([^{}]+)\}\}", skill.description)
    
