# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import litellm
import time

from odoo import api, fields, models
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class LitellmPrompt(models.Model):
    _name = 'litellm.prompt'
    _description = 'AI Prompt'

    name = fields.Char('Name', compute='_compute_name', store=True)
    model_id = fields.Many2one('litellm.model', string='Model', required=True)
    provider_id = fields.Many2one(related='model_id.provider_id', string='AI Server', store=True, readonly=True)
    message_ids = fields.One2many('litellm.prompt.message', 'prompt_id', string='Messages')
    question = fields.Text('Question')
    response = fields.Text('Response')
    keep_alive = fields.Text('keep alive', default="5m")


    @api.depends('model_id', 'message_ids', 'message_ids.role', 'message_ids.content')
    def _compute_name(self):
        for record in self:
            parts = []
            for msg in record.message_ids:
                content = msg.content or ''
                if len(content) > 40:
                    content = content[:40] + '...'
                parts.append("[%s] %s" % (msg.role, content))
            if parts:
                record.name = "%s - %s" % (record.model_id.name, ' | '.join(parts))
            else:
                record.name = record.model_id.name

    def action_send(self):
        self.ensure_one()
        try:
            if self.question:
                self.write({
                    'message_ids': [(0, 0, {
                        'role': 'user',
                        'content': self.question,
                    })],
                    'question': False,
                })

            api_base = self.provider_id.host or None
            model = self.model_id.provider_id.name + '/' + self.model_id.model
            keep_alive = (self.model_id.provider_id.name == 'ollama') and '5m' or None
            

            
            messages = [{'role': msg.role, 'content': msg.content} for msg in self.message_ids]
            
            start_time = time.time()
            
            response = litellm.completion(
                api_base=api_base,
                model=model, 
                messages=messages,
                keep_alive=keep_alive ,
                )
            
            reply = response.choices[0].message.content
            usage = response.usage


            self.write({
                'response': reply,
                'message_ids': [(0, 0, {
                    'role': 'assistant',
                    'content': reply,
                    'prompt_eval_count': usage.prompt_tokens,
                    'eval_count': usage.total_tokens,
                    'total_duration': time.time() - start_time,

                    
                })],
            })
        except Exception as e:
            raise UserError("Failed to send prompt: %s" % str(e))

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'litellm.prompt',
            'res_id': self.id,
            'view_mode': 'form',
        }


class LitellmPromptMessage(models.Model):
    _name = 'litellm.prompt.message'
    _description = 'Prompt Message'
    _order = 'sequence, id'

    prompt_id = fields.Many2one('litellm.prompt', string='Prompt',
                                required=True, ondelete='cascade')
    sequence = fields.Integer('Sequence', default=10)
    role = fields.Selection([
        ('system', 'System'),
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ], string='Role', required=True, default='user')
    content = fields.Text('Content', required=True)
    prompt_eval_count = fields.Float("Token in")
    eval_count = fields.Float("Total Token")
    cost = fields.Float("Cost")
    total_duration = fields.Float("Duration")
    
    


