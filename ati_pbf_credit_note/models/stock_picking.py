from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Picking(models.Model):
    _inherit = 'stock.picking'

    # open wizard credit note in form return
    def action_credit_note(self):
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_view_account_move_reversal")
        # picking = self.env['stock.picking'].search([('name', '=', self.origin[10:])])

        self._cr.execute("""
                   select a.picking_id
                        from stock_move a
                        where a.id in (select origin_returned_move_id from stock_move where picking_id = {_id})
                   """.format(_id=self.id))
        picking_id = self._cr.dictfetchall()
        picking = self.env['stock.picking'].search([('id', '=', picking_id[0]['picking_id'])])

        if picking:
            model = False

            # delivery order
            if picking.picking_type_id.code == 'outgoing':
                model = self.env['sale.order'].search([('name', '=', picking.origin)])

            # receipt
            elif picking.picking_type_id.code == 'incoming':
                model = self.env['purchase.order'].search([('name', '=', picking.origin)])

            # set context account.move
            if model:
                if model.invoice_ids:
                    if picking.picking_type_id.code == 'outgoing':
                        move_ids = model.invoice_ids.filtered(lambda x: x.state == 'posted' and x.move_type == 'out_invoice')
                    elif picking.picking_type_id.code == 'incoming':
                        move_ids = model.invoice_ids.filtered(lambda x: x.state == 'posted' and x.move_type == 'in_invoice')
                    stock_move_line = [{'product_id': sm.product_id.id, 'quantity': sm.quantity_done }for sm in self.move_ids_without_package]
                    action.update({'context': {
                        'return': True,
                        'move_ids': move_ids.ids,
                        'return_id': self.id,
                        'reason_return_id': self.return_reason.id,
                        'stock_move_line': stock_move_line
                    }})
                else:
                    raise UserError("Invoice not found")
        return action


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    @api.model
    def default_get(self, fields):
        result = super(AccountMoveReversal, self).default_get(fields)

        # get context account.move
        if self.env.context.get('return') == True:
            move_ids = self.env.context.get('move_ids')
            return_id = self.env.context.get('move_ids')

            result.update({
                'move_ids': [(6,0,move_ids)],
            })
        return result


    def _prepare_default_reversal(self, move):
        res = super(AccountMoveReversal, self)._prepare_default_reversal(move)
        ctx = self.env.context
        stock_move_line = []
        picking_id = self.env[ctx.get('active_model')].sudo().browse(ctx.get('active_id'))
        product_qty = {picking.product_id.id: picking.qty_done for picking in picking_id.move_line_ids_without_package}
        if ctx.get('active_model') == 'stock.picking':
            ref = res.get('ref')
            if ref and picking_id.customer_invoice:
                ref += " ("+picking_id.customer_invoice+")"
            if not ref and picking_id.customer_invoice:
                ref = ref

            res.update({
                'source_document_id': ctx.get('active_id'),
                'reason_return_id': ctx.get('reason_return_id'),
                'ref': ref
                # 'line_ids':[(0, 0, {
                #     'product_id': line.product_id.id,
                #     'price_unit': line.price_unit,
                #     'quantity': product_qty[line.product_id.id],
                #     'name': line.name,
                #     'account_id': line.account_id.id,
                #     'tax_ids': line.tax_ids.ids,
                # })for line in move.invoiice],

                # 'line_ids':[(0, 0, {
                #     'product_id': line.product_id.id,
                #     'price_unit': line.price_unit,
                #     'quantity': product_qty[line.product_id.id],
                #     'name': line.name,
                #     'account_id': line.account_id.id,
                #     'tax_ids': line.tax_ids.ids,
                # })for line in move.invoice_line_ids],

                # 'line_ids':[(0, 0, {
                #     'product_id': line.product_id.id,
                #     'price_unit': line.price_unit,
                #     'quantity': product_qty[line.product_id.id],
                #     'name': line.name,
                #     'tax_ids': line.tax_ids.ids,
                # })for line in move.line_ids],
            })
        return res