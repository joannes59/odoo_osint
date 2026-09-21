# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class FastMCPResource(models.Model):
    _name = 'fastmcp.resource'
    _description = 'MCP Resource'
    _order = 'name'

    mcp_server_id = fields.Many2one('fastmcp.server', string='MCP Server',
                                    required=True, ondelete='cascade')
    uri = fields.Char('URI', required=True)
    name = fields.Char('Name')
    title = fields.Char('Title')
    description = fields.Text('Description')
    mime_type = fields.Char('Mime Type')
    size = fields.Integer('Size')

    @api.model
    def get_resource_id(self, mcp_server_id, uri):
        """ 
        search or create the resource by uri.
        
        :param mcp_server_id: int | recordset id of fastmcp.server
        :param uri: text | uri of the resource
        :return: recordset of fastmcp.resource
        """
        resource_ids = self.search([
            ('mcp_server_id', '=', mcp_server_id),
            ('uri', '=', uri)])
        
        if not resource_ids:
            resource_ids = resource_ids.create({
                "mcp_server_id": mcp_server_id,
                "uri": uri,
                })
        return resource_ids[0]
    
    def update_info(self, resource):
        """
        Update informations about this resource

        :param resource: mcp.types.Resource 
        :return: None
        """
        update = {}           
        update['name'] = getattr(resource, 'name', None)
        update['title'] = getattr(resource, 'title', None)
        update['description'] = getattr(resource, 'description', None)
        update['mime_type'] = getattr(resource, 'mimeType', None)
        update['size'] = getattr(resource, 'size', None) or 0
        
        self.write(update)

