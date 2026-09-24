# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models
import json
from jsonschema import Draft7Validator
from odoo.tools.safe_eval import test_python_expr
from odoo.exceptions import ValidationError

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
    code = fields.Text('Python code')
    
    enabled = fields.Boolean('Enabled', default=True)
    
    parameter_ids = fields.One2many('fastmcp.tool.parameter', 'tool_id',
                                    string='Input Parameters')
    
    input_schema_pretty = fields.Text(string="Input Schema", compute="_json_pretty")

    call_ids = fields.One2many('fastmcp.tool.call', 'tool_id', string='Calls')


    @api.constrains('code')
    def _check_python_code(self):
        for tool in self.sudo().filtered('code'):
            msg = test_python_expr(expr=tool.code.strip(), mode="exec")
            if msg:
                raise ValidationError(msg)

    def call_tool(self, arguments=None, timeout=60):
        """Programmatic entry point: create a call, run it, return the record.

            call = tool.call_tool({'query': 'odoo'})
            call.state, call.result_text, call.structured_content
        """
        self.ensure_one()
        call = self.env['fastmcp.tool.call'].create({
            'tool_id': self.id,
            'arguments': json.dumps(arguments or {}, ensure_ascii=False),
            'timeout': timeout,
        })
        call.action_call_tool()
        return call

    def action_new_call(self):
        """Open a new call form pre-filled with this tool."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.name,
            'res_model': 'fastmcp.tool.call',
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_tool_id': self.id},
        }


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

    def action_generate_input_schema(self):
        """ Build input_schema from the configured parameters. """
        self.ensure_one()

        properties = {}
        required = []

        for param in self.parameter_ids:
            if not param.name:
                continue

            prop = {"type": param.type}
            if param.description:
                prop["description"] = param.description
            properties[param.name] = prop

            if param.required:
                required.append(param.name)

        schema = {
            "type": "object",
            "properties": properties,
        }
        if required:
            schema["required"] = required

        self.input_schema = schema
                        
    
    def validate_tool_call(self, tool_call):
        """
        Validate a LiteLLM tool_call against its JSON inputSchema.
        "tool_call" : litellm response in json
    
        Returns:
            {
                "valid": bool,
                "errors": list[str],
                "name": str | None,
                "arguments": dict | None,
            }
        """
        
        if tool_call.get("type") != "function":
            return {
                "valid": False,
                "errors": ["tool_call.type must be 'function'"],
                "name": None,
                "arguments": None,
            }
    
        function = tool_call.get("function")
    
        if not isinstance(function, dict):
            return {
                "valid": False,
                "errors": ["tool_call.function must be an object"],
                "name": None,
                "arguments": None,
            }
    
        name = function.get("name")
        arguments = function.get("arguments")
    
        if not name:
            return {
                "valid": False,
                "errors": ["Missing function name"],
                "name": None,
                "arguments": None,
            }
    
        # Les arguments LiteLLM sont généralement une chaîne JSON
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError as e:
                return {
                    "valid": False,
                    "errors": [f"Invalid JSON arguments: {e}"],
                    "name": name,
                    "arguments": None,
                }
    
        if not isinstance(arguments, dict):
            return {
                "valid": False,
                "errors": ["Function arguments must be a JSON object"],
                "name": name,
                "arguments": arguments,
            }
    
        # Validation JSON Schema
        validator = Draft7Validator(self.input_schema)
        errors = sorted(
            validator.iter_errors(arguments),
            key=lambda error: list(error.path)
        )
    
        error_messages = []
    
        for error in errors:
            path = ".".join(str(x) for x in error.path)
    
            if path:
                error_messages.append(f"{path}: {error.message}")
            else:
                error_messages.append(error.message)
    
        return {
            "valid": not error_messages,
            "errors": error_messages,
            "name": name,
            "arguments": arguments,
        }
        
