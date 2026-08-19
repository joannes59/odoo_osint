# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class FastMCPTool(models.Model):
    _name = 'fastmcp.tool'
    _description = 'MCP Tool'
    _order = 'name'

    mcp_server_id = fields.Many2one('fastmcp.server', string='MCP Server',
                                    required=True, ondelete='cascade')
    name = fields.Char('Name', required=True)
    title = fields.Char('Title')
    description = fields.Text('Description')
    input_schema = fields.Json('Input Schema')
    output_schema = fields.Json('Output Schema')
    annotations = fields.Json('Annotations')
    
    @api.model
    def get_tool_id(self, mcp_server_id, name):
        """ 
        search or create the tool by name.
        
        :param mcp_server_id: int | recordset id of fastmcp.server
        :param name: text | name of the tool
        :return: recordset of fastmcp.tool
        """
        tool_ids = self.search([
            ('mcp_server_id', '=', mcp_server_id),
            ('name', '=', name)])
        
        if not tool_ids:
            tool_ids = tool_ids.create({
                "mcp_server_id": mcp_server_id,
                "name": name,
                })
        return tool_ids[0]
    
    def update_info(self, tool):
        """
        Update informations about this tool

        :param tool: mcp.types.Tool 
        :return: None
        """
        update = {}           
        update['title'] = getattr(tool, 'title', None)
        update['description'] = getattr(tool, 'description', None)
        update['input_schema'] = getattr(tool, 'inputSchema', None)
        update['output_schema'] = getattr(tool, 'outputSchema', None)
        
        self.write(update)
        
        
        
        
        
    
    
