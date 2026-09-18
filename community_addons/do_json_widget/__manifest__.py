# -*- encoding: utf-8 -*-

{
    'name': 'JSON Widget',
    'category': 'Technical',
    'version': '19.0.1.0.0',
    'author': 'Do Incredible',
    'license': 'OPL-1',
    'sequence': 10,
    'summary': 'Beautiful collapsible tree-view JSON field widget for Odoo — with expand/collapse, key filter, copy, raw view, and optional inline editing.',
    'website': 'https://doincredible.com',
    'description': """
DO JSON Widget
==============

A rich, interactive JSON field widget for Odoo 19 — replacing the default
plain-text JSON field with a structured, readable tree view.

Key Features
------------
- Collapsible tree structure: objects and arrays show child counts and can be
  expanded or collapsed individually or all at once.
- Color-coded value types: strings (green), numbers (red), booleans (purple),
  null (grey), and keys (blue) — matching developer-tool conventions.
- Live key/value filter: type to instantly hide non-matching rows;
  parent nodes auto-expand to reveal matching children.
- Toolbar: Expand All, Collapse All, Copy to clipboard, Raw JSON toggle,
  and optional inline Edit mode.
- Valid / Invalid JSON badge with live feedback.
- Inline textarea editor with real-time JSON validation and error messages.
- Edit mode can be disabled per-field via options="{'no_edit_json': True}".
- Registered as widget name "do_json" — use widget="do_json" in any view.
- Works with fields.Json, fields.Text, and fields.Char field types.

Developed and maintained by Do Incredible.
    """,
    'depends': ['web'],
    'assets': {
        'web.assets_backend': [
            'do_json_widget/static/src/**/*.css',
            'do_json_widget/static/src/**/*.js',
            'do_json_widget/static/src/**/*.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'images': [
        'static/description/banner.png',
    ],
}
