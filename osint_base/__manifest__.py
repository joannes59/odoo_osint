# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    'name': 'OSINT Base',
    'version': '19.0.1.0.0',
    'category': 'Tools',
    'summary': 'Base module for the OSINT suite',
    'description': """
        Foundation module for the OSINT suite.

        Provides the root **OSINT** menu and the shared security group
        used by all other OSINT modules.
    """,
    'author': 'Joannes LANDY',
    'depends': ['base'],
    'data': [
        'security/res.group.xml',
        'security/ir.model.access.csv',

        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
