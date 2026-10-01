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
    
    note = fields.Text('Note')

    def get_tools(self):
        """ Get the tools available """
        result = []
        result += self.mcp_ids.get_tools()
        
        return result
    
    def _get_message_sequence(self):
        """ sequence message by 10 step """
        last = self.message_ids.search([], order='sequence desc', limit=1)
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
                msg_start = record.message_ids[0]
                msg_end = record.message_ids[-1]
                if  msg_end.content:
                    msg = msg_end
                else:
                    msg = msg_start
                    
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
            if msg.message_json:
                messages.append(msg.message_json)
            
        return messages
    
    def save_question(self):
        """ Save the question of the user in messages """
        if self.question:
            message_json = {
                'role': 'user',
                'content': self.question,
            }
            
            self.write({
                'message_ids': [(0, 0, {
                    'role': 'user',
                    'content': self.question,
                    'message_json': message_json,
                })],
                'question': False,
            })
        
    def send(self, role='user', loop=0, loop_max=5):
        """ Complete a prompt to ask llm response """
        self.ensure_one()
        try:
            if role == 'user':
                self.save_question()
                
            if loop >= loop_max:
                return "Number of iteration execed"
                
                
            start_time = time.time()
            
            # Provider and model
            api_base = self.provider_id.host or None
            api_key = self.provider_id.get_apikey() or None
            model = (self.model_id.provider_id.litellm_provider + '/' + self.model_id.model).lower()
            keep_alive = (self.model_id.provider_id.litellm_provider == 'OLLAMA') and '5m' or None
            
            # message system and tools
            if not self.message_system:
                self.message_system = self.generate_message_sytem()  
            tools = self.get_tools() or None       
            tool_choice = tools and "auto" or None
            
            # Ask LLM response
            messages = self.generate_messages()
            print('--litellm----completion--messages-----------', messages)
            response = litellm.completion(
                api_base=api_base,
                api_key=api_key,
                model=model, 
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
                keep_alive=keep_alive,
                )
            print('--litellm----completion--response-----------', response)
            # get llm response
            message_json  = self.to_json(response.choices[0].message)
            print('------message_json----------', message_json)

            tool_calls = message_json.get('tool_calls')
            content = message_json.get('content')
            usage = response.usage

                    
            # Save llm response in message_ids
            reply_message = {
                'prompt_id': self.id,
                'role': 'assistant',
                'content': content,
                'message_json': message_json,

                'prompt_eval_count': usage.prompt_tokens,
                'eval_count': usage.total_tokens,
                'total_duration': time.time() - start_time,
            }
            self.write({
                    'response': content,
                    'message_ids': [(0, 0, reply_message)],
                })
            
            # Tools call response message
            if tool_calls:
                tool_message_ids = self.env['litellm.prompt.message']
                tool_message_vals = {'prompt_id': self.id}
                tool_message_vals['role'] = 'tool'  

                for tool in tool_calls:
                    tool_message_vals['tool_call_id'] = tool.get('id')      

                       
                    tool_call = self.env['fastmcp.tool.call'].create_tool_call(tool)
                    tool_message_vals['response_tool_call_id'] = tool_call.id
                    
                    tool_message_ids += self.env['litellm.prompt.message'].create(tool_message_vals)    
                    
                print('------tool_message_ids----------', tool_message_ids)

                # Call tools
                for tool_message in tool_message_ids:
                    if tool_message.response_tool_call_id:
                        tool_message.response_tool_call_id.action_call_tool()
                    
                        if tool_message.response_tool_call_id.state == 'success':
                            tool_message.content = tool_message.response_tool_call_id.result_text
                            tool_message_json = {
                                'role': 'tool',
                                'tool_call_id': tool_message.response_tool_call_id.tool_call_id,
                                'content': tool_message.response_tool_call_id.result_text,
                                
                                }
                            tool_message.message_json = tool_message_json
                        else:
                            tool_message.content = ''
    
                # recall llm with tool response in messages
                if tool_message_ids:
                    loop += 1
                    print('--------recall llm with tool---------')
                    self.send(role='tool', loop=loop)
                    print('--------response llm with tool---------')

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
    


