# -*- coding: utf-8 -*-
{
    'name': 'SearxNG Search Integration',
    'version': '19.0.1.0.0',
    'category': 'Tools',
    'summary': 'Interact with SearxNG search servers directly from Odoo',
    'description': """
        This module allows users to configure SearxNG server instances, 
        perform web searches, and keep a persistent history of all queries 
        and their results directly within the Odoo interface.
    """,
    'depends': ['base'],
    'data': [
        'security/res.group.xml',
        'security/ir.model.access.csv',
        'views/menu_views.xml',
        'views/searxng_server_views.xml',
        'views/searxng_query_views.xml',
        'views/searxng_result_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}

