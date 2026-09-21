#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from odoo import fields, models


class OsintAgentSkillParameter(models.Model):
    _name = 'osint.agent.skill.parameter'
    _description = 'Agent Skill Parameter'
    _order = 'sequence, id'

    sequence = fields.Integer('Sequence', default=10)
    name = fields.Char('Name', required=True)
    parameter_type = fields.Selection([
        ('char', 'Char'),
        ('text', 'Text'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('boolean', 'Boolean'),
        ('selection', 'Selection'),
        ('json', 'JSON'),
    ], string='Parameter Type', required=True, default='char')
    skill_ids = fields.Many2many(
        'osint.agent.skill',
        string='Skills',
    )
    description = fields.Char('Description')
    
    