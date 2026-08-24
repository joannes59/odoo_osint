# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class FastMCPPrompt(models.Model):
    _name = 'fastmcp.prompt'
    _description = 'MCP Prompt'
    _order = 'name'

    mcp_server_id = fields.Many2one('fastmcp.server', string='MCP Server',
                                    required=True, ondelete='cascade')
    name = fields.Char('Name', required=True)
    title = fields.Char('Title')
    description = fields.Text('Description')
    arguments = fields.Json('Arguments')

    @api.model
    def get_prompt_id(self, mcp_server_id, name):
        """ 
        search or create the prompt by name.
        
        :param mcp_server_id: int | recordset id of fastmcp.server
        :param name: text | name of the prompt
        :return: recordset of fastmcp.prompt
        """
        prompt_ids = self.search([
            ('mcp_server_id', '=', mcp_server_id),
            ('name', '=', name)])
        
        if not prompt_ids:
            prompt_ids = prompt_ids.create({
                "mcp_server_id": mcp_server_id,
                "name": name,
                })
        return prompt_ids[0]
    
    def update_info(self, prompt):
        """
        Update informations about this prompt

        :param prompt: mcp.types.Prompt 
        :return: None
        """
        update = {}           
        update['title'] = getattr(prompt, 'title', None)
        update['description'] = getattr(prompt, 'description', None)
        
        arguments = []
        for arg in getattr(prompt, 'arguments', None) or []:
            if hasattr(arg, 'model_dump'):          # Pydantic v2
                arguments.append(arg.model_dump(exclude_none=True))
            elif hasattr(arg, 'dict'):              # Pydantic v1
                arguments.append(arg.dict(exclude_none=True))
            elif isinstance(arg, dict):
                arguments.append(arg)
        update['arguments'] = arguments
        
        self.write(update)

