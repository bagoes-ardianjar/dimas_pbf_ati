from email.policy import default
from odoo.exceptions import UserError
from odoo import models, fields, _, api

class X_inherit_stk_pckg(models.Model):
    _inherit = 'stock.picking'
    _description = ''

    recipient_id = fields.Many2one('res.partner', string='Recipient Contact')
    is_return = fields.Boolean(string='is return')
    is_internal_transfer = fields.Boolean(string='is internal transfer', compute='_is_internal_transfer')

    @api.depends('picking_type_id')
    def _is_internal_transfer(self):

        if self.picking_type_id.code == "internal":
            self.is_internal_transfer = True
        else:
            self.is_internal_transfer = False


    def action_submit_2(self):
        if self.state == 'assigned' and self.is_return == False:
            if not self.apj:
                raise UserError('Anda belum menginput "APJ"')
            else:
                self.state = 'waiting_approval'
