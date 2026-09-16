#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 11 14:06:52 2026

@author: joannes
"""


from odoo import models


class MailBot(models.AbstractModel):
    _inherit = 'mail.bot'
    

    def get_litellm_session(self, channel):
        """ Return the litellm current session."""
        
        # get llm session
        if not self.env.user.litellm_session_id:
            
            session = self.env.user.litellm_session_id.create(
                {'name': self.env.user.name,
                 'channel_id': channel.id}
                )
        else:
            session = self.env.user.litellm_session_id
            
        return session
    
    def _get_answer(self, channel, body, values, command=False):
        """ Return the AI answer to the user """
        
        odoobot = self.env.ref("base.partner_root")

        if channel.channel_type == "chat" and odoobot in channel.channel_member_ids.partner_id:
            # main flow
            
            # get llm session
            sesion = self.get_litellm_session(channel)
            answer = sesion.get_answer(channel=channel, body=body,
                                       values=values, command=command)
        else:
            answer = super()._get_answer(channel=channel, body=body,
                                       values=values, command=command)

        return answer
