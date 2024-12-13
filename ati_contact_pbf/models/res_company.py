from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ResCompany(models.Model):
    _inherit = 'res.company'

    remainder_email_user_ids = fields.One2many('res.users', 'remainder_email_company_id', string='Email User for Reminder Partner')
    remainder_email_mail_server_id = fields.Many2one('ir.mail_server', string='Mail Server for Reminder Partner')

class ResUsers(models.Model):
    _inherit = 'res.users'

    remainder_email_company_id = fields.Many2one('res.company', string='Company for Reminder Partner', ondelete='cascade')