from odoo import models, fields, _, api
from odoo.http import request
import werkzeug
import werkzeug.wrappers

class ResUsers(models.Model):
    _inherit = 'res.users'
    _description = 'Users'

    manager_approval = fields.Many2one('res.partner', string='Manager Approval')