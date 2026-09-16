# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api
import json
from odoo.http import request
from urllib.parse import parse_qs, urlparse


class LitellmSession(models.Model):
    _name = 'litellm.session'
    _description = 'AI Session'

    name = fields.Char('Name', required=True)
    fields.Datetime('Date', default=fields.Datetime.now)
    prompt_ids = fields.One2many('litellm.prompt', 'session_id', string='Prompts')
    channel_id = fields.Many2one('discuss.channel', string='Channel')
    
    def get_answer(self, channel, body, values, command=False):
        """ Return answer to the user """
        
        # Get context information
        browser_context = self.env.context.copy()
        browser_context.pop('message_post_store', None)
        browser_context['agent_context'] = self.parse_website_url()

        browser_context_pretty = json.dumps(browser_context,
                indent=4,
                ensure_ascii=False
            )
        litellm_model = self.get_litellm_model()
        
        print('-------browser_context-----------\n', browser_context_pretty)
        print('---------------body--------------\n', body)
        print('---------------values------------\n', values)
        print('---------------litellm_model-----\n', litellm_model)
        
        prompt = self.get_litellm_prompt(litellm_model)
        prompt.question = body
        answer = prompt.send()
        
      
        
        return answer
    
    def get_litellm_model(self):
        """ return the litellm model to use """
        
        litellm_model = self.env['litellm.model'].search([], order='sequence', limit=1)
        return litellm_model
        
    def get_litellm_prompt(self, litellm_model):
        """ Complete or Create prompt to ask llm """
        
        prompt = self.prompt_ids.create({
            'model_id': litellm_model.id,
                })
        return prompt
               
        
    @api.model
    def parse_website_url(self):
        """ Get information about the web page being viewed by the user."""
        
        res = {}
        current_url = ''
        
        if request and hasattr(request, 'httprequest'):
            current_url = request.httprequest.headers.get('Referer')
            
        if current_url:
            parsed = urlparse(current_url)
            res = {
                "scheme": parsed.scheme,  # ex: 'https'
                "domain": parsed.netloc,  # ex: 'mon-site.com'
                "path": parsed.path,  # ex: '/shop/category/2'
                "query": parse_qs(parsed.query),  # ex: {'debug': ['1']}
                #"fragment": parsed.fragment,
            }
            
            if res['path'].startswith('/odoo/'):
                res['side'] = 'backend'
                res['view_type'] = 'list'
                res['res_id'] = 0
                
                backend_path = res['path'].replace('\n', '').split('/')
                
                if len(backend_path) >= 3 and backend_path[-1].isnumeric():
                    res['res_id'] = int(backend_path[-1])
                    res['view_type'] = 'form'

                action = backend_path[2]
                act_window = self.env['ir.actions.act_window']
                
                if action.startswith('action-'):
                    res['view_name'] = ''
                    action_id = action.replace('action-', '')
                    if action_id.isnumeric():
                        act_window = act_window.browse(int(action_id))
                else:
                    res['view_name'] = action
                    act_window = act_window.search([('path', '=', action)], limit=1)
                
                if act_window:
                    res['res_model'] = act_window.res_model
                    res['act_window_id'] = act_window.id
                    
            else:
                res['side'] = 'website'
                
        return res