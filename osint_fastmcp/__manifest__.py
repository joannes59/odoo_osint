# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    'name': 'OSINT MCP utility',
    'version': '19.0.1.0.0',
    'category': 'Technical',
    'summary': 'MCP server proxy',
    'description': """
        Add description of MCP server, store the MCP capability in database
    """,
    'author': 'Joannes LANDY',
    'depends': ['osint_litellm'],
    'data': [
        'security/ir.model.access.csv',
        'views/fastmcp_server_views.xml',

    ],
    'installable': True,
    'images': ['static/description/icon.png'],
    'license': 'LGPL-3',
}
