#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep  4 20:42:19 2026

@author: joannes
"""

from odoo import models
from odoo.addons.web.controllers.utils import get_action



class DiscussChannel(models.Model):
    _inherit = 'discuss.channel'


    def _message_post_after_hook(self, message, msg_vals):
        
        browser_context = self.env.context.get("browser_context") or {}
        pathname = browser_context.get("pathname")
        #ir.actions.act_window if action
        
        
        

        if pathname:
        
            print("BROWSER CONTEXT:", get_action(self.env, pathname))
      
    
        res = super()._message_post_after_hook(message, msg_vals)
        
        odoobot_id = self.env['ir.model.data']._xmlid_to_res_id("base.partner_root")
        author_id = msg_vals.get("author_id")
        partner_origin = author_id and self.env['res.partner'].browse(author_id) or False
                
        if not author_id or author_id == odoobot_id or partner_origin.main_user_id.is_ai_agent:
            # No interaction with odoobot or previeus ai_agent response
            return res

        for channel in self:
                            
            ai_user = channel.channel_member_ids.mapped(
                    "partner_id"
                ).main_user_id.filtered(
                    lambda user: user.is_ai_agent
                )[:1]
   
            
            if ai_user:
                message_model = message.model
                res_id = message.res_id
                answer = "ok, ca marche!\n" + message_model + ': ' + str(res_id)
                answer += '\n' + str(browser_context)
                answer += '\n' + str(self.env.context)
                
            
                channel.sudo().message_post(
                            author_id=ai_user.partner_id.id,
                            body=answer,
                            message_type="comment",
                            silent=True,
                            subtype_xmlid="mail.mt_comment",
                        )

        return res
    
    