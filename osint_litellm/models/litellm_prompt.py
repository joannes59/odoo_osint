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
    keep_alive = fields.Text('keep alive')


    @api.depends('message_ids', 'message_ids.role', 'message_ids.content')
    def _compute_name(self):
        for record in self:
            len_content = 120
            if record.message_ids:
                msg = record.message_ids[-1]
                content = msg.content or ''
                if len(content) > len_content:
                    content = content[:len_content] + '...'
                    
                record.name = "[%s] %s" % (msg.role, content)

            else:
                record.name = ""

    def get_tools(self):
        """ Get the tools available """
        return []

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
            api_key = self.provider_id.get_apikey() or None
            model = (self.model_id.provider_id.litellm_provider + '/' + self.model_id.model).lower()
            keep_alive = (self.model_id.provider_id.litellm_provider == 'OLLAMA') and '5m' or None
            tools = self.get_tools() or None       
            tool_choice = tools and "auto" or None
            messages = [{'role': msg.role, 'content': msg.content} for msg in self.message_ids]
            
            start_time = time.time()
            
            print(tool_choice, tools)
            
            response = litellm.completion(
                api_base=api_base,
                api_key=api_key,
                model=model, 
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
                keep_alive=keep_alive,
                )
            
            reply = response.choices[0].message.content
            tool_calls = response.choices[0].message.tool_calls
            usage = response.usage
            
            print('------------------------\n', tool_calls)

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



    


