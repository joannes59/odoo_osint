# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    'name': 'OSINT Website',
    'version': '19.0.1.0.0',
    'category': 'Tools',
    'summary': 'OSINT management of websites and URLs',
    'description': """
        This module allows collecting and organising OSINT information
        related to websites and URLs. Each domain is recorded
        (`osint.website`) and the parsed URLs (`osint.url`) are attached
        to it, with their components (scheme, path, query, fragment...).
    """,
    'author': 'Joannes LANDY',
    'depends': ['base'],
    'data': [
        'security/res.group.xml',
        'security/ir.model.access.csv',

        'views/menu_views.xml',
        'views/osint_website_views.xml',
        'views/osint_url_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
