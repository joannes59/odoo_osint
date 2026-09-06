#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep  4 20:42:19 2026

@author: joannes
"""

from odoo import models, api
from odoo.http import request
from urllib.parse import parse_qs, urlparse


class DiscussChannel(models.Model):
    _inherit = 'discuss.channel'

    def _message_post_after_hook(self, message, msg_vals):
        """ get the message and Ask IA """
        
        # Get context information
        browser_context = self.env.context.copy()
        browser_context.pop('message_post_store', None)
        browser_context['agent_context'] = self.parse_website_url()

        author_id = msg_vals.get("author_id")
        browser_context['agent_context']['author_id'] =  author_id
        
        # Post the message
        res = super()._message_post_after_hook(message, msg_vals)
        
        
        # Check if agent in the loop        
        odoobot_id = self.env['ir.model.data']._xmlid_to_res_id("base.partner_root")        
        partner_origin = author_id and self.env['res.partner'].browse(author_id) or False
                
        if not author_id or author_id == odoobot_id or partner_origin.main_user_id.is_ai_agent:
            # No interaction with odoobot or previeus ai_agent response
            return res

        for channel in self:
            
            browser_context['agent_context']['channel_id'] = channel.id
            browser_context['agent_context']['message_id'] = message.id
            browser_context['agent_context'].pop('ai_partner_id', None)
                            
            ai_user = channel.channel_member_ids.mapped(
                    "partner_id"
                ).main_user_id.filtered(
                    lambda user: user.is_ai_agent
                )[:1]

            if ai_user:                
                browser_context['agent_context']['ai_partner_id'] = ai_user.partner_id.id

                answer = self.get_answer(browser_context)
            
                channel.sudo().message_post(
                            author_id=browser_context['agent_context']['ai_partner_id'],
                            body=answer,
                            message_type="comment",
                            silent=True,
                            subtype_xmlid="mail.mt_comment",
                        )
        return res
    
    def get_answer(self, browser_context):
        """ return answer to the message """
        answer = "ok, it is good!\n" + str(browser_context)
        return answer
    
    @api.model
    def parse_website_url(self):
        """ Get informations on the web page viewing by the user """
        
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
                "params": parse_qs(parsed.query),  # ex: {'debug': ['1']}
            }
            
            if res['path'].startswith('/odoo/'):
                res['side'] = 'backend'
                res['view_type'] = 'list'
                res['res_id'] = 0
                
                backend_path = res['path'].split('/')
                
                if len(backend_path) == 4 and backend_path[3].isnumeric():
                    res['res_id'] = int(backend_path[3])
                    res['view_type'] = 'form'

                if len(backend_path) >= 3:
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
                    
            else:
                res['side'] = 'website'
                
        return res
                
                
        

            
            
            
    
    