#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 11 14:06:52 2026

@author: joannes
"""


from odoo import models, api
import json
from odoo.http import request
from urllib.parse import parse_qs, urlparse

class MailBot(models.AbstractModel):
    _inherit = 'mail.bot'

    def get_litellm_session(self, browser_context):
        """ Return the litellm current session."""
        
        # Call llm
        if not self.litellm_session_id:
            self.litellm_session_id = self.litellm_session_id.create({'name': 'test'})
            
        return self.litellm_session_id
    
    def _get_answer(self, channel, body, values, command=False):
        odoobot = self.env.ref("base.partner_root")
        # onboarding
        odoobot_state = self.env.user.odoobot_state

        if channel.channel_type == "chat" and odoobot in channel.channel_member_ids.partner_id:
            # main flow
            

            # Get context information
            browser_context = self.env.context.copy()
            browser_context.pop('message_post_store', None)
            browser_context['agent_context'] = self.parse_website_url()

            browser_context_pretty = json.dumps(browser_context,
                    indent=4,
                    ensure_ascii=False
                )
            print('-------browser_context-----------\n', browser_context_pretty)
            
            answer = "ok, next step is ready with odoo bot !\n" 

            return answer
        
        
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
                print('-----backend_path---------', current_url)
                
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