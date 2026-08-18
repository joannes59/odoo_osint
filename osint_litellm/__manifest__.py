# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    'name': 'OSINT LiteLLM',
    'version': '19.0.1.0.0',
    'category': 'Technical',
    'summary': 'Local AI for OSINT management',
    'description': """
        Base module to configure AI Providers.
        Requires `litellm ` Python package.
    """,
    'author': 'Joannes LANDY',

    'depends': ['base'],
    'external_dependencies': {
        'python': ['litellm'],
    },
    'data': [
        'security/res.group.xml',
        'security/ir.model.access.csv',
        
        'datas/litellm.provider.csv',
        
        'views/menu_views.xml',
        'views/litellm_provider_views.xml',
        'views/litellm_model_views.xml',
        'views/litellm_model_capability_views.xml',
        'views/litellm_provider_apikey_views.xml',
        'views/litellm_prompt_views.xml',

    ],
    'installable': True,
    'images': ['static/description/icon.png'],
    'license': 'LGPL-3',
}
