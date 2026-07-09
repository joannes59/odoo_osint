# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    'name': 'OSINT Ollama',
    'version': '19.0.1.0.0',
    'category': 'Technical',
    'summary': 'Local AI for OSINT management',
    'description': """
        Base module to configure AI Providers.
        Requires `ollama ` Python package.
    """,
    'author': 'Joannes LANDY',

    'depends': ['base'],
    'external_dependencies': {
        'python': ['ollama'],
    },
    'data': [
        'security/res.group.xml',
        'security/ir.model.access.csv',
        'views/menu_views.xml',
        'views/ollama_provider_views.xml',
        'views/ollama_model_views.xml',
        'views/ollama_model_capability_views.xml',
        'views/ollama_prompt_views.xml',

    ],
    'installable': True,
    'images': ['static/description/icon.png'],
    'license': 'LGPL-3',
}
