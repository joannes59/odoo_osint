{
    'name': 'Website Contact Capture',
    'version': '19.0.1.0.0',
    'category': 'Website',
    'summary': 'Store website contact form submissions',
    'depends': [
        'website',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/osint_website_contact_views.xml',
    ],
    'installable': True,
    'application': True,
}
