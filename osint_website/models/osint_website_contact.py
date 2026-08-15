from odoo import fields, models


class WebsiteContactRequest(models.Model):
    _name = 'osint.website.contact'
    _description = 'Website Contact Request'
    _order = 'create_date desc'

    name = fields.Char(string='Name', required=True)
    email = fields.Char(string='Email', required=True)
    phone = fields.Char(string='Phone')
    company = fields.Char(string='Company')
    subject = fields.Char(string='Subject')
    description = fields.Text(string='Message')

    create_date = fields.Datetime(
        string='Received At',
        readonly=True,
    )
