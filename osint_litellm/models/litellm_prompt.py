# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import asyncio
import json
import time

import litellm

from odoo import api, fields, models
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)

try:
    from litellm.experimental_mcp_client.client import MCPClient
    from litellm.experimental_mcp_client.tools import transform_mcp_tool_to_openai_tool
    from mcp.types import CallToolRequestParams as MCPCallToolRequestParams
except ImportError:
    MCPClient = None
    transform_mcp_tool_to_openai_tool = None
    MCPCallToolRequestParams = None


class LitellmPrompt(models.Model):
    _name = 'litellm.prompt'
    _description = 'AI Prompt'

    name = fields.Char('Name', compute='_compute_name', store=True)
    model_id = fields.Many2one('litellm.model', string='Model', required=True)
    provider_id = fields.Many2one(related='model_id.provider_id', string='AI Server', store=True, readonly=True)
    message_ids = fields.One2many('litellm.prompt.message', 'prompt_id', string='Messages')
    question = fields.Text('Question')
    response = fields.Text('Response')
    keep_alive = fields.Text('keep alive')
    
    mcp_server_ids = fields.Many2many('litellm.mcp.server', string='MCP Servers')
    mcp_tool_ids = fields.Many2many('litellm.mcp.tool', string='MCP Tools')
    mcp_resource_ids = fields.Many2many('litellm.mcp.resource', string='MCP Resources')
    mcp_prompt_ids = fields.Many2many('litellm.mcp.prompt', string='MCP Prompts')
    mcp_message_ids = fields.One2many('litellm.prompt.mcp.message', 'prompt_id', string='MCP Tool Calls')


    @api.depends('model_id', 'message_ids', 'message_ids.role', 'message_ids.content')
    def _compute_name(self):
        for record in self:
            parts = []
            for msg in record.message_ids:
                content = msg.content or ''
                if len(content) > 40:
                    content = content[:40] + '...'
                parts.append("[%s] %s" % (msg.role, content))
            if parts:
                record.name = "%s - %s" % (record.model_id.name, ' | '.join(parts))
            else:
                record.name = record.model_id.name

    def _sync_mcp_capabilities(self):
        """ Sync MCP servers capabilities and link them to the prompt. """
        if not self.mcp_server_ids:
            return
        for server in self.mcp_server_ids:
            server._sync_capabilities()
            self.mcp_tool_ids |= server.tool_ids
            self.mcp_resource_ids |= server.resource_ids
            self.mcp_prompt_ids |= server.prompt_ids

    def _get_mcp_tools(self):
        """ Return tools of the linked MCP servers in OpenAI chat format. """
        tools = []
        if transform_mcp_tool_to_openai_tool:
            for tool in self.mcp_tool_ids:
                mcp_tool = tool._to_mcp_tool()
                if mcp_tool is None:
                    continue
                try:
                    tools.append(transform_mcp_tool_to_openai_tool(mcp_tool))
                except Exception as e:
                    _logger.warning("Failed to transform MCP tool %s: %s", tool.name, e)
        return tools

    @staticmethod
    def _parse_mcp_result(result):
        """ Extract readable text from an MCP tool call result. """
        if not result or not getattr(result, 'content', None):
            return "Tool executed successfully"
        try:
            from mcp.types import EmbeddedResource, ImageContent, TextContent
        except ImportError:
            return "Tool executed successfully"
        text_parts = []
        for content_item in result.content:
            if isinstance(content_item, TextContent):
                text_parts.append(str(content_item.text))
            elif isinstance(content_item, ImageContent):
                text_parts.append("[Generated Image]")
            elif isinstance(content_item, EmbeddedResource):
                text_parts.append("[Embedded Resource]")
        return " ".join(text_parts) or "Tool executed successfully"

    @staticmethod
    def _serialize_arguments(arguments):
        if isinstance(arguments, str):
            return arguments
        try:
            return json.dumps(arguments, ensure_ascii=False, indent=2)
        except Exception:
            return str(arguments)

    def _call_mcp_tool(self, server, tool_name, tool_call_id, arguments):
        """ Execute a tool on the MCP server and record the exchange. """
        server.ensure_one()
        if not MCPClient or not MCPCallToolRequestParams:
            raise UserError("The 'litellm' python package is required to call MCP tools.")
        try:
            client = server._get_client()
            params = MCPCallToolRequestParams(
                name=tool_name,
                arguments=arguments,
            )
            result = asyncio.run(client.call_tool(params))
            error = bool(getattr(result, 'isError', False))
            text = self._parse_mcp_result(result)
        except Exception as e:
            text = "Error executing tool: %s" % str(e)
            error = True
            _logger.warning("MCP tool call failed %s/%s: %s", server.name, tool_name, e)

        self.mcp_message_ids = [(0, 0, {
            'tool_name': tool_name,
            'tool_call_id': tool_call_id,
            'arguments': self._serialize_arguments(arguments),
            'result': text,
            'error': error,
        })]
        return text, error
    
    def action_send(self):
       self.ensure_one()
       try:
           if self.question:
               self.write({
                   'message_ids': [(0, 0, {
                       'role': 'user',
                       'content': self.question,
                   })],
                   'question': False,
               })

           api_base = self.provider_id.host or None
           api_key = self.model_id.get_apikey() or None
           model = (self.model_id.provider_id.litellm_provider + '/' + self.model_id.model).lower()
           keep_alive = (self.model_id.provider_id.name == 'ollama') and '5m' or None
           
           
           messages = [{'role': msg.role, 'content': msg.content} for msg in self.message_ids]
           
           start_time = time.time()
           
           response = litellm.completion(
               api_base=api_base,
               api_key=api_key,
               model=model, 
               messages=messages,
               keep_alive=keep_alive,
               )
           
           reply = response.choices[0].message.content
           usage = response.usage


           self.write({
               'response': reply,
               'message_ids': [(0, 0, {
                   'role': 'assistant',
                   'content': reply,
                   'prompt_eval_count': usage.prompt_tokens,
                   'eval_count': usage.total_tokens,
                   'total_duration': time.time() - start_time,

                   
               })],
           })
       except Exception as e:
           raise UserError("Failed to send prompt: %s" % str(e))

       return {
           'type': 'ir.actions.act_window',
           'res_model': 'litellm.prompt',
           'res_id': self.id,
           'view_mode': 'form',
       }

    def action_send2(self):
        self.ensure_one()
        try:
            if self.question:
                self.write({
                    'message_ids': [(0, 0, {
                        'role': 'user',
                        'content': self.question,
                    })],
                    'question': False,
                })

            api_base = self.provider_id.host or None
            api_key = self.model_id.get_apikey() or None
            model = (self.model_id.provider_id.litellm_provider + '/' + self.model_id.model).lower()
            keep_alive = (self.model_id.provider_id.name == 'ollama') and '5m' or None

            self._sync_mcp_capabilities()
            tools = self._get_mcp_tools()
            server_by_tool = {}
            for tool in self.mcp_tool_ids:
                server_by_tool[tool.name] = tool.mcp_server_id

            messages = [{'role': msg.role, 'content': msg.content} for msg in self.message_ids]

            start_time = time.time()
            reply = None
            max_iterations = 10

            for _iteration in range(max_iterations):
                response = litellm.completion(
                    api_base=api_base,
                    api_key=api_key,
                    model=model,
                    messages=messages,
                    tools=tools or None,
                    keep_alive=keep_alive,
                )

                message = response.choices[0].message
                tool_calls = getattr(message, 'tool_calls', None) or []

                if not tool_calls:
                    reply = message.content
                    usage = response.usage
                    break

                assistant_msg = {
                    'role': 'assistant',
                    'content': message.content,
                    'tool_calls': [
                        {
                            'id': tc.id,
                            'type': 'function',
                            'function': {
                                'name': tc.function.name,
                                'arguments': tc.function.arguments,
                            },
                        }
                        for tc in tool_calls
                    ],
                }
                messages.append(assistant_msg)

                for tc in tool_calls:
                    tool_name = tc.function.name
                    try:
                        arguments = json.loads(tc.function.arguments) if tc.function.arguments else {}
                    except Exception:
                        arguments = {}
                    server = server_by_tool.get(tool_name)
                    if not server:
                        text = "Unknown tool: %s (no MCP server configured for it)" % tool_name
                        error = True
                        self.mcp_message_ids = [(0, 0, {
                            'tool_name': tool_name,
                            'tool_call_id': tc.id,
                            'arguments': tc.function.arguments or '{}',
                            'result': text,
                            'error': error,
                        })]
                    else:
                        text, error = self._call_mcp_tool(server, tool_name, tc.id, arguments)
                    messages.append({
                        'role': 'tool',
                        'tool_call_id': tc.id,
                        'name': tool_name,
                        'content': text,
                    })

            if reply is None:
                raise UserError("Failed to get a response from the model.")

            self.write({
                'response': reply,
                'message_ids': [(0, 0, {
                    'role': 'assistant',
                    'content': reply,
                    'prompt_eval_count': usage.prompt_tokens,
                    'eval_count': usage.total_tokens,
                    'total_duration': time.time() - start_time,
                })],
            })
        except Exception as e:
            raise UserError("Failed to send prompt: %s" % str(e))

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'litellm.prompt',
            'res_id': self.id,
            'view_mode': 'form',
        }


class LitellmPromptMessage(models.Model):
    _name = 'litellm.prompt.message'
    _description = 'Prompt Message'
    _order = 'sequence, id'

    prompt_id = fields.Many2one('litellm.prompt', string='Prompt',
                                required=True, ondelete='cascade')
    sequence = fields.Integer('Sequence', default=10)
    role = fields.Selection([
        ('system', 'System'),
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ], string='Role', required=True, default='user')
    content = fields.Text('Content', required=True)
    prompt_eval_count = fields.Float("Token in")
    eval_count = fields.Float("Total Token")
    cost = fields.Float("Cost")
    total_duration = fields.Float("Duration")
    
    


