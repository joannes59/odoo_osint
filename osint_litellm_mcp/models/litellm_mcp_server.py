# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).


import json
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

import fastmcp
import asyncio



class LitellmMCPServer(models.Model):
    _name = 'litellm.mcp.server'
    _description = 'MCP Server'

    name = fields.Char('Name', required=True)
    server_url = fields.Char('Server URL', help="URL of the MCP server (http or sse transport).")


    tool_ids = fields.One2many('litellm.mcp.tool', 'mcp_server_id', string='Tools')
    resource_ids = fields.One2many('litellm.mcp.resource', 'mcp_server_id', string='Resources')
    prompt_ids = fields.One2many('litellm.mcp.prompt', 'mcp_server_id', string='Prompts')

    tool_count = fields.Integer('Tool Count', compute='_compute_capability_count')
    resource_count = fields.Integer('Resource Count', compute='_compute_capability_count')
    prompt_count = fields.Integer('Prompt Count', compute='_compute_capability_count')
    
    active = fields.Boolean('Active', default=True)

    @api.depends('tool_ids', 'resource_ids', 'prompt_ids')
    def _compute_capability_count(self):
        for record in self:
            record.tool_count = len(record.tool_ids)
            record.resource_count = len(record.resource_ids)
            record.prompt_count = len(record.prompt_ids)


    @api.model
    def _run_async_mcp_fetch(self, server_url):
        """Méthode interne pour exécuter le code asynchrone."""
        async def main():
            client = fastmcp.Client(server_url)
            try:
                async with client:
                    tools = await client.list_tools()
                    resources = await client.list_resources()
                    prompts = await client.list_prompts()
                    
                    result =  {
                        'status': 'success',
                        'tools': str(tools),
                        'resources': str(resources),
                        'prompts': str(prompts)
                    }
       
                    return result
                
            except Exception as e:
                _logger.error(f"Erreur de connexion au serveur MCP : {e}")
                return {'status': 'error', 'message': str(e)}

        # Exécution de la boucle asynchrone dans le contexte synchrone d'Odoo
        return asyncio.run(main())

    def action_fetch_metadata(self):
        """Action déclenchée par le bouton pour récupérer les métadonnées."""
        self.ensure_one()
        
        if not self.server_url:
            raise UserError("Veuillez configurer une URL de serveur MCP valide.")

        _logger.info(f"Connexion au serveur MCP : {self.server_url}")
        result = self._run_async_mcp_fetch(self.server_url)

        if result['status'] == 'success':
            print(result)
        else:
            raise UserError(f"Échec de la récupération des données MCP : {result['message']}")

    def action_sync_capabilities(self):
        """ Fetch tools, resources and prompts from the MCP server."""


        return {
            'type': 'ir.actions.act_window',
            'res_model': 'litellm.mcp.server',
            'res_id': self.ids and self.ids[0] or False,
            'view_mode': 'form',
        }
