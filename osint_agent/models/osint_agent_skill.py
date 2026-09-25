#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import markdown
import re
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo import Command

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
    description = fields.Text('Description (markdown)')
    description_pretty = fields.Html(
        string='Description',
        compute='_compute_description_pretty',
        sanitize=False,
    )
    parameter_ids = fields.Many2many(
        'osint.agent.skill.parameter',
        compute='_extract_parameters',
        string='Parameters',
        store = True
    )

    @api.depends('description')
    def _compute_description_pretty(self):
        for rec in self:
            rec.description_pretty = markdown.markdown(rec.description or '')

    def find_parameter(self, parameter_name):
        """ Find parameter or create one """
        domain = [('name', '=', parameter_name)]
        parameter_ids = self.env['osint.agent.skill.parameter'].search(domain)
        
        if not parameter_ids:
            parameter_vals = {
                'name': parameter_name,
                }
            parameter = self.env['osint.agent.skill.parameter'].create(parameter_vals)
            
        elif len(parameter_ids) == 1:
            parameter = parameter_ids
        else:
            raise UserError(f"Skill parameter is duplicated: {parameter_name}")
            
        return parameter

    @api.depends('description')
    def _extract_parameters(self):
        """ Create parameters used in this skills {{parameter}}."""
        
        for skill in self:
            if not  skill.description:
                continue
            # parameter is like {{parameter_name}} ^[a-z0-9]+(-[a-z0-9]+)*$
            list_parameters = re.findall(r"\{\{([^{}]+)\}\}", skill.description)
            
            for parameter_name in list_parameters:
                parameter = self.find_parameter(parameter_name)
                
                if not re.fullmatch(r'[a-z][a-z0-9_-]*', parameter.name):
                    raise ValidationError(_('The parameter should contain only lowercase alphanumeric characters, underscore, and dash, and it should start with a letter.'))
                
                skill.parameter_ids = [Command.link(parameter.id)]
                
                
            
    # self.env[model_name].check_access("write")
    
