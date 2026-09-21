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
    provider_id = fields.Many2one(related='model_id.provider_id', string='AI Server',
                                  store=True, readonly=True)
    message_ids = fields.One2many('litellm.prompt.message', 'prompt_id', string='Messages')
    question = fields.Text('Question')
    response = fields.Text('Response')
    keep_alive = fields.Text('keep alive')
    session_id = fields.Many2one('litellm.session', string='Session')
    
    message_system = fields.Text('System Message')

    mcp_ids = fields.Many2many('fastmcp.server', string='MCP server')

    def get_tools(self):
        """ Get the tools available """
        result = []
        result += self.mcp_ids.get_tools()
        
        return result
    
    def _get_message_sequence(self):
        """ sequence message by 10 step """
        last = self.message_ids.search([], order='sequence desc', limit=1)
        print('-------_get_message_sequence-----------', last)
        return (last.sequence if last else 0) + 10
    
    @api.model
    def to_json(self, response_tool_calls):
        """ convert and save tools """
        result = {}
        
        if response_tool_calls is not None:
            if hasattr(response_tool_calls, 'model_dump'):          # Pydantic v2
                result = response_tool_calls.model_dump(exclude_none=True)
            elif hasattr(response_tool_calls, 'dict'):              # Pydantic v1
                result = response_tool_calls.dict(exclude_none=True)
            elif isinstance(response_tool_calls, dict):
                result = response_tool_calls
     
        return result

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
    
    def generate_message_sytem(self):
        """ Get the prompt system, futur function """
        res = ''
        return res
        
    def generate_messages(self):
        """ List previews message to send to llm """
        messages = []
        if self.message_system:
            messages.append({
                'role': 'system',
                'content': self.message_system})
            
        for msg in self.message_ids:
            messages.append({'role': msg.role, 'content': msg.content})
            
        return messages
    
    def save_question(self):
        """ Save the question of the user in messages """
        if self.question:
            self.write({
                'message_ids': [(0, 0, {
                    'role': 'user',
                    'content': self.question,
                })],
                'question': False,
            })
        
    def send(self, role='user'):
        """ Complete a prompt to ask llm response """
        self.ensure_one()
        try:
            self.save_question()
            start_time = time.time()
            
            api_base = self.provider_id.host or None
            api_key = self.provider_id.get_apikey() or None
            model = (self.model_id.provider_id.litellm_provider + '/' + self.model_id.model).lower()
            keep_alive = (self.model_id.provider_id.litellm_provider == 'OLLAMA') and '5m' or None
            
            self.message_system = self.message_system or self.generate_message_sytem()
            
            tools = self.get_tools() or None       
            tool_choice = tools and "auto" or None
            
            messages = self.generate_messages()
                                    
            # Ask LLM response
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
            usage = response.usage
            tool_calls = response.choices[0].message.tool_calls
                    
            reply_message = {
                'content': reply,
                'prompt_eval_count': usage.prompt_tokens,
                'eval_count': usage.total_tokens,
                'total_duration': time.time() - start_time,
            }
            
            if tool_calls:
                reply_message['role'] = 'tool'

                for tool in tool_calls:
                    reply_message['tool_call_id'] = tool.id
                    reply_message['tool_calls'] = self.to_json(tool)
                
                    self.write({
                        'response': reply,
                        'message_ids': [(0, 0, reply_message)],
                    })
                    
                    # In case if there are multiple tool_calls, init message
                    reply_message['content'] = None
                    reply_message['prompt_eval_count'] = 0
                    reply_message['eval_count'] = 0
                    reply_message['total_duration'] = 0
                    
            else:
                reply_message['role'] = 'assistant'
                self.write({
                    'response': reply,
                    'message_ids': [(0, 0, reply_message)],
                })
            
            
        except Exception as e:
            raise UserError("Failed to send prompt: %s" % str(e))

        return self.response
    

    def action_send(self, role='user'):
        """ return llm response to prompt view """
        self.send(role=role)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'litellm.prompt',
            'res_id': self.id,
            'view_mode': 'form',
        }
    


