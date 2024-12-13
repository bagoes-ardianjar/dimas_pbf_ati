# Copyright 2013 Guewen Baconnier, Camptocamp SA
# Copyright 2017 Okia SPRL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models,_
from odoo.exceptions import AccessError, UserError, ValidationError



class po_confirm(models.TransientModel):
    _name = 'po.confirm'
    _description = 'PO Confirm'

    def confirm_afterValidate(self):
        ctx = dict(self.env.context or {})
        purchase_order = self.env['purchase.order'].browse(ctx['active_ids'])
        for po in purchase_order:
            po.sudo().write(
                {
                    'state': 'waiting_approve'
                }
            )
class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    cancel_reason_id = fields.Many2one(
        comodel_name="purchase.order.cancel.reason",
        string="Reason For Cancellation",
        readonly=True,
        ondelete="restrict",
    )


    state = fields.Selection([
        ('draft', 'RFQ'),
        ('waiting_approve', 'Waiting Approval'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('to_approve_apj', 'Waiting Cancel'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)

    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'waiting_approve', 'sent']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order._approval_allowed():
                order.sudo().button_approve()
            else:
                order.sudo().write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        return True


    def action_confirm(self):
        promotion = self.env['po.promotion'].search([('status', '=', True)])

        for promotion_product in promotion:
            for order_line in self.order_line:
                for product_ids_list in promotion_product.product_ids:
                    if order_line.product_id.id == product_ids_list.id and order_line.is_promotion != True and order_line.is_discount != True and order_line.is_promo != True:
                        raise UserError('Click the Promotion button to check your product got a promo')
        # for purchase in self:
        #     self._cr.execute("""
        #                 select
        #                     a.id
        #                     from po_promotion a
        #                     join purchase_order_line b on b.product_id = a.reward_product_id or b.product_id = a.discount_line_product_id
        #                     where b.order_id = {_id} and b.is_promotion = false
        #                 """.format(_id=self.id))
        #     check_promo = self._cr.dictfetchall()
        #     if len(check_promo) > 0:
        #         raise UserError('Click the Promotion button to check your product got a promo')
        product_not_active = []
        for order_line in self.order_line:
            # active_or_not = [product.activate_product for product in order_line.product_id]

            for product in order_line.product_id:
                if product.activate_product == False:
                    product_not_active.append(product.name)

            for prd in order_line.product_id:
                for seller in prd.seller_ids:
                    # order_line.order_id.id_of_supplierinfo = seller.id  # ...
                    order_line.order_id.sudo().write({'id_of_supplierinfo': seller.id})
        if not product_not_active:
            # //bimo
            for x in self:
                # CHECK TAXES IN PO LINE #
                # tax_ids = []
                # for line in x.order_line:
                #     if line.taxes_id:
                #         tax_ids.append(line.taxes_id.id)
                # tax_ids = set(list(tax_ids))
                # if len(tax_ids) > 1:
                #     raise UserError(_('Cannot confirm PO with different taxes.'))

                contacts = self.env['res.partner'].search([('name', '=', x.partner_id.name)])
                for listContacts in contacts:
                    if listContacts.expired_registration:
                        if x.date_order.date() > listContacts.expired_registration:
                            ir_model_data = self.env['ir.model.data']
                            view = ir_model_data._xmlid_lookup('purchase_cancel_reason.validation_expire_date')[2]
                            ctx = dict(self.env.context or {})
                            ctx.update({
                                'default_model': 'po.confirm',
                                'active_model': 'po.confirm',
                                'active_id': x.ids,
                                'partner_id': x.partner_id.id
                            })

                            return {
                                'name': _('Attention!'),
                                'type': 'ir.actions.act_window',
                                'view_mode': 'form',
                                'res_model': 'po.confirm',
                                'views': [(view, 'form')],
                                'view_id': view,
                                'target': 'new',
                                'context': ctx
                            }
                        else:
                            x.sudo().button_confirm()
                    # x.state = "waiting_approve"

        else:
            raise ValidationError(
                _("Product Non Active!\nMenunggu approval manager (manager mengaktifkan produk)\n\nNon-active product:\n%s" % (
                    ', \n'.join(product_not_active))))


    def action_reject(self):
        for x in self:
            x.state = "draft"



class PurchaseOrderCancelReason(models.Model):
    _name = "purchase.order.cancel.reason"
    _description = "Purchase Order Cancel Reason"

    name = fields.Char(string="Reason", required=True, translate=True)
