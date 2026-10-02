# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models
import json
from jsonschema import Draft7Validator
import base64
from xml.sax.saxutils import escape
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
        

    # ------------------------------------------------------------------
    # Export XML
    # ------------------------------------------------------------------
    def _xml_field(self, name, value, indent='        ', as_json=False):
        """Retourne une ligne <field> ou '' si la valeur est vide."""
        if value in (False, None, '', {}, []):
            return ''
        if as_json:
            value = json.dumps(value, ensure_ascii=False, indent=2)
        return f'{indent}<field name="{name}"><![CDATA[{value}]]></field>\n'

    def _get_xml_id_name(self, record, prefix):
        """Génère un identifiant XML stable (sans espaces ni caractères spéciaux)."""
        safe = ''.join(c if c.isalnum() else '_' for c in (record.name or ''))
        return f'{prefix}_{safe}_{record.id}'.lower()

    def _generate_xml(self):
        self.ensure_one()
        tool_xid = self._get_xml_id_name(self, 'tool')
        server = self.mcp_server_id

        lines = ['<?xml version="1.0" encoding="utf-8"?>', '<odoo>']

        # --- Outil ---
        lines.append(f'    <record id="{tool_xid}" model="fastmcp.tool">')
        lines.append(f'        <field name="name">{escape(self.name or "")}</field>')
        lines.append(f'        <field name="mcp_server_id" ref="{escape(self._server_ref(server))}"/>')
        for fname in ('title', 'description', 'code'):
            line = self._xml_field(fname, self[fname])
            if line:
                lines.append(line.rstrip('\n'))
        for fname in ('input_schema', 'output_schema', 'annotations'):
            line = self._xml_field(fname, self[fname], as_json=True)
            if line:
                lines.append(line.rstrip('\n'))
        lines.append(f'        <field name="enabled" eval="{bool(self.enabled)}"/>')
        lines.append('    </record>')

        # --- Paramètres ---
        for param in self.parameter_ids.sorted(lambda p: (p.sequence, p.id)):
            p_xid = self._get_xml_id_name(param, 'param')
            lines.append('')
            lines.append(f'    <record id="{p_xid}" model="fastmcp.tool.parameter">')
            lines.append(f'        <field name="tool_id" ref="{tool_xid}"/>')
            lines.append(f'        <field name="name">{escape(param.name or "")}</field>')
            lines.append(f'        <field name="type">{param.type}</field>')
            line = self._xml_field('description', param.description)
            if line:
                lines.append(line.rstrip('\n'))
            lines.append(f'        <field name="required" eval="{bool(param.required)}"/>')
            lines.append(f'        <field name="sequence">{param.sequence or 0}</field>')
            lines.append('    </record>')

        lines.append('</odoo>')
        return '\n'.join(lines) + '\n'

    def _server_ref(self, server):
        """Référence XML ID du serveur (existant, sinon généré à la volée)."""
        xmlid = server.get_external_id().get(server.id)
        return xmlid or f'__export__.fastmcp_server_{server.id}'

    def action_export_xml(self):
        """Génère le fichier XML et déclenche son téléchargement."""
        self.ensure_one()
        xml_content = self._generate_xml()

        filename = ''.join(
            c if c.isalnum() or c in '-_' else '_' for c in (self.name or 'tool')
        )
        attachment = self.env['ir.attachment'].create({
            'name': f'fastmcp_tool_{filename}.xml',
            'type': 'binary',
            'datas': base64.b64encode(xml_content.encode('utf-8')),
            'mimetype': 'application/xml',
            'res_model': self._name,
            'res_id': self.id,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }