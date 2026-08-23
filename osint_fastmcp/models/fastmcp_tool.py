# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models
import json


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
    
    enabled = fields.Boolean('Enabled', default=True)
    
    input_schema_pretty = fields.Text(string="Input Schema", compute="_json_pretty")

    @api.depends("input_schema")
    def _json_pretty(self):
        """ Return json in human readable text """
        
        for rec in self:
            input_schema_pretty = ""
            
            if rec.input_schema:
                input_schema_pretty = json.dumps(
                        rec.input_schema,
                        indent=4,
                        ensure_ascii=False
                    )
            rec.input_schema_pretty = input_schema_pretty
    
    
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
        
        annotations = None
        ann = getattr(tool, 'annotations', None)
        if ann is not None:
            if hasattr(ann, 'model_dump'):          # Pydantic v2
                annotations = ann.model_dump(exclude_none=True)
            elif hasattr(ann, 'dict'):              # Pydantic v1
                annotations = ann.dict(exclude_none=True)
            elif isinstance(ann, dict):
                annotations = ann
        update['annotations'] = annotations
        
        self.write(update)
        
    def get_llm_schema(self):
        """ return tools schema in llm client format. """
        result = []

        for tool in self:
            result.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.input_schema or {
                        "type": "object", "properties": {}},
                }
            })
        return result
                        
            
        
    
    
