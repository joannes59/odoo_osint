# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class LitellmSession(models.Model):
    _name = 'litellm.session'
    _description = 'AI Session'

    name = fields.Char('Name', required=True)
    prompt_ids = fields.One2many('litellm.prompt', 'session_id', string='Prompts')
    channel_id = fields.Many2one('discuss.channel', string='Channel')
    
    def get_answer(self, browser_context):
        """ Return answer to the user """
        
        answer = "ok, next step is ready!\n" 
        
        return answer
        
        
