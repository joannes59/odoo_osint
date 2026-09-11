#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 11 15:25:52 2026

@author: joannes
"""

from odoo import  models

class DiscussChannelMember(models.Model):
    _inherit = 'discuss.channel.member'
    
    
    def _mark_as_read(self, last_message_id):
        """
        Mark channel as read by updating the seen message id of the current
        member as well as its new message separator.

        :param last_message_id: the id of the message to be marked as read.
        """

        message = self.env['mail.message'].browse(last_message_id)
        odoobot = self.env.ref("base.partner_root")
        if message.author_id == odoobot:
            # No need of mark as read for odoobot
            return
        
        self.ensure_one()
        domain = [
            ("model", "=", "discuss.channel"),
            ("res_id", "=", self.channel_id.id),
            ("id", "<=", last_message_id),
        ]
        last_message = self.env['mail.message'].search(domain, order="id DESC", limit=1)
        if not last_message:
            return
        self._set_last_seen_message(last_message)
        self._set_new_message_separator(last_message.id + 1)