# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import ollama

from odoo import api, fields, models
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class OllamaPrompt(models.Model):
    _name = 'ollama.prompt'
    _description = 'AI Prompt'

    name = fields.Char('Name', compute='_compute_name', store=True)
    model_id = fields.Many2one('ollama.model', string='Model', required=True)
    provider_id = fields.Many2one(related='model_id.provider_id', string='AI Server', store=True, readonly=True)
    message_ids = fields.One2many('ollama.prompt.message', 'prompt_id', string='Messages')
    question = fields.Text('Question')
    response = fields.Text('Response')

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

            client = ollama.Client(host=self.provider_id.host)
            messages = [{'role': msg.role, 'content': msg.content} for msg in self.message_ids]
            response = client.chat(model=self.model_id.model, messages=messages)
            reply = response['message']['content']

            self.write({
                'response': reply,
                'message_ids': [(0, 0, {
                    'role': 'assistant',
                    'content': reply,
                })],
            })
        except Exception as e:
            raise UserError("Failed to send prompt: %s" % str(e))

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ollama.prompt',
            'res_id': self.id,
            'view_mode': 'form',
        }


class OllamaPromptMessage(models.Model):
    _name = 'ollama.prompt.message'
    _description = 'Prompt Message'
    _order = 'sequence, id'

    prompt_id = fields.Many2one('ollama.prompt', string='Prompt', required=True, ondelete='cascade')
    sequence = fields.Integer('Sequence', default=10)
    role = fields.Selection([
        ('system', 'System'),
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ], string='Role', required=True, default='user')
    content = fields.Text('Content', required=True)
