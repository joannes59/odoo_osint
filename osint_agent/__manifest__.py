# -*- coding: utf-8 -*-
{
    'name': 'OSINT Agent',
    'version': '19.0.1.0.0',
    'category': 'Tools',
    'summary': 'AI agent integration for OSINT',
    'description': """
        Manage AI agents (res.users as agent) and their integration with the discuss channel.
    """,
    'author': 'Joannes LANDY',
    'depends': ['base', 'web', 'mail', 'im_livechat'],
    'data': [
        'views/res_users_views.xml',
        ],
    "assets": {
    "web.assets_backend": [
        "osint_agent/static/src/services/browser_context.js",
        ],
    },
    'installable': True,
    'license': 'LGPL-3',
}
