import asyncio
import json
import logging
import time

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from .mcp_client import flatten_exception, open_mcp_session

_logger = logging.getLogger(__name__)


class FastMCPToolCall(models.Model):
    _name = 'fastmcp.tool.call'
    _description = 'MCP Tool Call'
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
    input_schema_text = fields.Text(
        'Input Schema', compute='_compute_input_schema_text',
    )

    # --- Call parameters -------------------------------------------------
    arguments = fields.Text(
        'Arguments (JSON)', default='{}',
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

    @api.depends('tool_id.input_schema')
    def _compute_input_schema_text(self):
        for call in self:
            schema = call.tool_id.input_schema
            call.input_schema_text = (
                json.dumps(schema, indent=2, ensure_ascii=False) if schema else False
            )

    @api.constrains('arguments')
    def _check_arguments(self):
        for call in self:
            call._get_arguments_dict()

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------
    def _get_arguments_dict(self):
        self.ensure_one()
        raw = (self.arguments or '').strip()
        if not raw:
            return {}
        try:
            args = json.loads(raw)
        except ValueError as e:
            raise ValidationError(_("Arguments must be valid JSON: %s", e))
        if not isinstance(args, dict):
            raise ValidationError(_("Arguments must be a JSON object."))
        return args

    def _check_required_arguments(self, arguments):
        """Light validation against the `required` list of the tool input schema."""
        self.ensure_one()
        schema = self.tool_id.input_schema or {}
        required = schema.get('required') or []
        missing = [key for key in required if key not in arguments]
        if missing:
            raise UserError(_(
                "Missing required argument(s) for tool %(tool)s: %(missing)s",
                tool=self.tool_id.name, missing=", ".join(missing),
            ))

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
        for call in self:
            if call.state != 'draft':
                raise UserError(_(
                    "This call has already been executed. Duplicate it to run it again."
                ))
            call._execute()
        return True

    def _execute(self):
        self.ensure_one()
        tool = self.tool_id
        server = tool.mcp_server_id

        # Validation errors are raised to the user, nothing is logged
        arguments = self._get_arguments_dict()
        self._check_required_arguments(arguments)

        vals = {'call_date': fields.Datetime.now()}
        start = time.monotonic()
        try:
            result = self._run_async_call(
                server.server_url,
                server.get_server_apikey(),
                tool.name,
                arguments,
                self.timeout,
            )
        except (Exception, BaseExceptionGroup) as e:
            _logger.warning("MCP call_tool %s failed: %s", tool.name, e)
            message = flatten_exception(e)
            if isinstance(e, asyncio.TimeoutError):
                message = _("Timeout after %s s", self.timeout)
            vals.update(state='error', error_message=message)
        else:
            vals.update(self._prepare_result_vals(result))
        vals['duration'] = time.monotonic() - start
        self.write(vals)

