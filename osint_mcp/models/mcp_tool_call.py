import asyncio
import json
import logging
import time

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from .mcp_client import flatten_exception, open_mcp_session
from odoo.tools.safe_eval import safe_eval
import traceback

_logger = logging.getLogger(__name__)


class FastMCPToolCall(models.Model):
    _name = 'fastmcp.tool.call'
    _description = 'MCP Tool Call'
    _inherit = ['json.field.editor.mixin']
    _order = 'id desc'

    tool_id = fields.Many2one(
        'fastmcp.tool', string='Tool', required=True, index=True,
        ondelete='cascade',
    )
    mcp_server_id = fields.Many2one(
        related='tool_id.mcp_server_id', string='MCP Server',
        store=True, index=True, readonly=True,
    )
    tool_description = fields.Text(related='tool_id.description', readonly=True)
    input_schema = fields.Json(related='tool_id.input_schema', readonly=True)

    # --- Call parameters -------------------------------------------------
    arguments = fields.Json(
        'Arguments (JSON)', 
        help="JSON object passed as `arguments` to call_tool.",
    )
    timeout = fields.Integer(
        'Timeout (s)', default=60,
        help="Maximum duration of the whole call (connection included). 0 = no limit.",
    )

    # --- Execution & response -------------------------------------------
    state = fields.Selection(
        [('draft', 'Draft'), ('success', 'Success'), ('error', 'Error')],
        default='draft', required=True, readonly=True, copy=False, index=True,
    )
    call_date = fields.Datetime('Called on', readonly=True, copy=False)
    duration = fields.Float('Duration (s)', readonly=True, copy=False, digits=(16, 3))
    result_text = fields.Text('Text Result', readonly=True, copy=False)
    structured_content = fields.Text('Structured Content', readonly=True, copy=False)
    raw_response = fields.Text('Raw Response', readonly=True, copy=False)
    error_message = fields.Text('Error', readonly=True, copy=False)

    # ---------------------------------------------------------------------
    # Compute / constraints
    # ---------------------------------------------------------------------
    @api.depends('tool_id.name', 'create_date')
    def _compute_display_name(self):
        for call in self:
            date = call.create_date.strftime('%Y-%m-%d %H:%M') if call.create_date else _("New")
            call.display_name = f"{call.tool_id.name or ''} - {date}"


    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------

    @api.model
    def _run_async_call(self, server_url, apikey, tool_name, arguments, timeout=None):
        """Run call_tool in a fresh event loop (Odoo workers are synchronous)."""
        async def _call():
            async with open_mcp_session(server_url, apikey) as session:
                return await session.call_tool(tool_name, arguments)

        async def main():
            return await asyncio.wait_for(_call(), timeout=timeout or None)

        return asyncio.run(main())

    def _prepare_result_vals(self, result):
        """Convert a CallToolResult into field values."""
        data = result.model_dump(mode='json', by_alias=True, exclude_none=True)

        texts = []
        for block in result.content or []:
            if getattr(block, 'type', None) == 'text':
                texts.append(block.text)
            else:
                # image / audio / resource: kept in raw_response only
                texts.append(f"[{getattr(block, 'type', 'unknown')}]")
        text = "\n".join(texts)

        structured = getattr(result, 'structuredContent', None)
        is_error = bool(getattr(result, 'isError', False))

        return {
            'state': 'error' if is_error else 'success',
            'result_text': text or False,
            'structured_content': (
                json.dumps(structured, indent=2, ensure_ascii=False)
                if structured is not None else False
            ),
            'raw_response': json.dumps(data, indent=2, ensure_ascii=False),
            'error_message': (text or _("The tool reported an error.")) if is_error else False,
        }

    # ---------------------------------------------------------------------
    # Actions
    # ---------------------------------------------------------------------
    def action_call_tool(self):
        """ MCP server call tool """ 
        for call in self:
            start = time.monotonic()
            call.call_date = fields.Datetime.now()
            if call._check_required_arguments():
            
                if call.mcp_server_id.built_in:
                    call._execute_built_in({})
                else:
                    call._execute_external()
                    
            call.duration = time.monotonic() - start


    def _check_required_arguments(self):
        """Light validation against the `required` list of the tool input schema."""
        self.ensure_one()
        schema = self.tool_id.input_schema or {}
        required = schema.get('required') or []
        missing = [key for key in required if key not in self.arguments]
        if missing:
            self.state = 'error'
            e = ", ".join(missing)
            self.error_message = f"Missing required argument(s): {e}"
            return False
        else:
            return True

    def _execute_external(self):
        """ Call external MCP server """
        self.ensure_one()
        server = self.tool_id.mcp_server_id
        print('--------self.arguments--------', self.arguments)
        print('--------self.arguments--------', type(self.arguments))

        try:
            result = self._run_async_call(
                server.server_url,
                server.get_server_apikey(),
                self.tool_id.name,
                self.arguments,
                self.timeout,
            )
        except Exception as e:
            error_message = ''
            for exc in e.exceptions:
                error_message += flatten_exception(exc)

            self.state = 'error'
            self.error_message = error_message

        else:
            vals = self._prepare_result_vals(result)
            self.write(vals)
            
            
    def _get_eval_context(self):
        """Context to push on execute python."""
        self.ensure_one()

        eval_context = {
            'env': self.env,
            'tool_call': self,
            'args': self.arguments or {},
            'result': {},   # the python code return response in this dic
            'log': lambda msg: self._logger_info(msg), 
        }
        return eval_context

    def _execute_built_in(self):
        """ Buit in function to execute """
        self.ensure_one()
        eval_context = self._get_eval_context()
        code = (self.tool_id.code or '').strip()
        if not code:
            self.state = 'error'
            self.error_message = "No code on this call tool"
        else:
            try:
                safe_eval(
                    code,
                    globals_dict=eval_context,
                    mode='exec',
                    nocopy=True,
                )
            except Exception as e:
                self.state = 'error'
                self.error_message = str(e)
            else:            
                self.result = eval_context.get('result', {})
                self.state = 'done'
    