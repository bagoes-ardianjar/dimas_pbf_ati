from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from itertools import groupby

class PurchaseOrderIb_for_supplier(models.Model):
    _inherit = 'purchase.order'
    _description = 'Purchase Order for Supplier'

    def getAllowCreateBill(self):
        for rec in self:
            rec.allow_create_bill = True
            amount_due = 0
            if rec.state not in ('purchase', 'done'):
                rec.allow_create_bill = False
            # if rec.invoice_status not in ('no', 'invoiced'):
            #     print("2")
            #     rec.allow_create_bill = False
            if not rec.order_line:
                rec.allow_create_bill = False

            ## lines
            for inv in rec.invoice_ids.filtered(lambda r: r.move_type == 'in_invoice'):
                amount_due += inv.amount_residual

            if rec.invoice_ids and amount_due == 0:
                rec.allow_create_bill = False

    purchase_person = fields.Many2one('hr.employee', string='Purchase Person (*)', index=True, tracking=1)
    allow_create_bill = fields.Boolean(compute=getAllowCreateBill, string='Allow Create Bill',)

    def action_create_invoice(self):
        """Create the invoice associated to the PO.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        # 1) Prepare invoice vals and clean-up the section lines
        invoice_vals_list = []
        for order in self:
            if order.invoice_status != 'to invoice':
                continue

            order = order.with_company(order.company_id)
            pending_section = None
            # Invoice values.
            invoice_vals = order._prepare_invoice()
            # Invoice line values (keep only necessary sections).
            for line in order.order_line:
                if line.display_type == 'line_section':
                    pending_section = line
                    continue
                if not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    if pending_section:
                        invoice_vals['invoice_line_ids'].append((0, 0, pending_section._prepare_account_move_line()))
                        pending_section = None
                    invoice_vals['invoice_line_ids'].append((0, 0, line._prepare_account_move_line()))
            invoice_vals_list.append(invoice_vals)
            # print('ivl', invoice_vals_list)

        if not invoice_vals_list:
            raise UserError(
                _('There is no invoiceable line. If a product has a control policy based on received quantity, please make sure that a quantity has been received.'))

        # 2) group by (company_id, partner_id, currency_id) for batch creation
        new_invoice_vals_list = []
        for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: (
        x.get('company_id'), x.get('partner_id'), x.get('currency_id'))):
            origins = set()
            payment_refs = set()
            refs = set()
            ref_invoice_vals = None
            for invoice_vals in invoices:
                if not ref_invoice_vals:
                    ref_invoice_vals = invoice_vals
                else:
                    ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                origins.add(invoice_vals['invoice_origin'])
                payment_refs.add(invoice_vals['payment_reference'])
                refs.add(invoice_vals['ref'] if invoice_vals['ref'] != False else '')

            ref_invoice_vals.update({
                'ref': ', '.join(refs)[:2000],
                'invoice_origin': ', '.join(origins),
                'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
            })
            new_invoice_vals_list.append(ref_invoice_vals)
        invoice_vals_list = new_invoice_vals_list
        # print('ivl', invoice_vals_list)

        # 3) Create invoices.
        moves = self.env['account.move']
        # print('move1',moves.id)

        # new_total_discount_po = 0
        # for line in self.order_line:
        #     new_discount_1 = line.ati_price_unit * line.discount_1 / 100.0 if line.discount_1 else 0.0
        #     new_discount_2 = line.ati_price_unit * line.discount_2 / 100.0 if line.discount_2 else 0.0
        #     new_discount_3 = line.discount_3 if line.discount_3 else 0.0
        #     new_discount_4 = line.discount_4 if line.discount_4 else 0.0
        #     new_discount_line = (new_discount_1 + new_discount_2 + new_discount_3 + new_discount_4) * line.qty_received
        #     new_total_discount_po += new_discount_line
        #     print(new_total_discount_po)
        # new_aml_vals = {
        #     'name': 'Discount Item',
        #     'display_type': False,
        #     'quantity': 1,
        #     'account_id': self.env['account.account'].sudo().search([('code', '=', '1100-00-040')]).id,
        #     # 'product_uom_id': line.product_id.uom_id.id,
        #     'debit': 0,
        #     'credit': new_total_discount_po,
        #     'parent_state': 'draft',
        #     'company_id': self.company_id.id,
        #     'journal_id': self.env['account.journal'].sudo().search(
        #         [('code', '=', 'INV'), ('type', '=', 'purchase'), ('active', '=', True)],
        #         limit=1).id,
        #     # 'analytic_account_id': self.analytic_account_id.id,
        #     'exclude_from_invoice_tab': False,
        #     # 'tax_tag_invert': invert,
        #     'partner_id': self.partner_id.id,
        #     'move_id': moves.id,
        # }
        # new_aml_id = self.env['account.move.line'].sudo().create(new_aml_vals)


        AccountMove = self.env['account.move'].with_context(default_move_type='in_invoice')
        for vals in invoice_vals_list:
            moves |= AccountMove.with_company(vals['company_id']).create(vals)

        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        moves.filtered(
            lambda m: m.currency_id.round(m.amount_total) < 0).action_switch_invoice_into_refund_credit_note()
        for move_obj in moves:
            move_obj.purchase_person = self.purchase_person.id
        # print('move2', moves.id)
        new_total_discount_po = 0
        for line in self.order_line:
            ati_harga_unit = line.ati_price_unit
            line_discount_1 = ati_harga_unit * line.discount_1 / 100.0 if line.discount_1 else 0.0
            ati_harga_unit = ati_harga_unit - line_discount_1
            line_discount_2 = ati_harga_unit * line.discount_2 / 100.0 if line.discount_2 else 0.0
            ati_harga_unit = ati_harga_unit - line_discount_2
            line_discount_3 = line.discount_3 if line.discount_3 else 0.0
            ati_harga_unit = ati_harga_unit - line_discount_3
            line_discount_4 = line.discount_4 if line.discount_4 else 0.0
            ati_harga_unit = ati_harga_unit - line_discount_4
            total_discount_line = (line_discount_1 + line_discount_2 + line_discount_3 + line_discount_4) * line.qty_received
            # new_discount_1 = line.ati_price_unit * line.discount_1 / 100.0 if line.discount_1 else 0.0
            # new_discount_2 = line.ati_price_unit * line.discount_2 / 100.0 if line.discount_2 else 0.0
            # new_discount_3 = line.discount_3 if line.discount_3 else 0.0
            # new_discount_4 = line.discount_4 if line.discount_4 else 0.0
            # new_discount_line = (new_discount_1 + new_discount_2 + new_discount_3 + new_discount_4) * line.qty_received
            new_total_discount_po += total_discount_line
        if new_total_discount_po > 0:
            new_aml_vals = {
                'name': 'Purchase Discount Item',
                'display_type': False,
                'quantity': 1,
                # 'account_id': self.env['ir.config_parameter'].sudo().search([('key', '=', 'discount_account_invoive.discount_item_account')]).id or None,
                'account_id': int(self.env['ir.config_parameter'].sudo().search([('key', '=', 'discount_account_invoive.bill_discount_item_account')]).value) or None,
                # 'product_uom_id': line.product_id.uom_id.id,
                'debit': 0,
                'credit': new_total_discount_po,
                'parent_state': 'draft',
                'company_id': self.company_id.id,
                'journal_id': self.env['account.journal'].sudo().search(
                    [('code', '=', 'BILL'), ('type', '=', 'purchase'), ('active', '=', True)],
                    limit=1).id,
                # 'analytic_account_id': self.analytic_account_id.id,
                'exclude_from_invoice_tab': True,
                # 'tax_tag_invert': invert,
                'partner_id': self.partner_id.id,
                'move_id': moves.id,
            }
            new_aml_id = self.env['account.move.line'].sudo().create(new_aml_vals)
        picking = self.env['stock.picking'].sudo().search([('origin', '=', self.name), ('date_done', '!=', False)],order='id desc',
                                                          limit=1)

        if picking.date_done:
            update_data = "update account_move set invoice_date = '{_effective_date}', date = '{_effective_date}' " \
                          "where move_type = 'in_invoice' and id = {_id}".format(_effective_date=picking.date_done,
                                                                                  _id=moves.id)
            self._cr.execute(update_data)
            self._cr.commit()
        # xxx

        return self.action_view_invoice(moves)

    def _prepare_supplier_info(self, partner, line, price, currency):
        # Prepare supplierinfo data when adding a product
        return {
            'name': partner.id,
            'sequence': max(line.product_id.seller_ids.mapped('sequence')) + 1 if line.product_id.seller_ids else 1,
            'min_qty': 0.0,
            'price': price,
            'currency_id': currency.id,
            'price_include_ppn': price * 1.11, # line.order_id.amount_total,
            'min_qty': line.product_qty,
            'discount_1': line.discount_1,
            'discount_2': line.discount_2,
            'discount_3': line.discount_3,
            'discount_4': line.discount_4,
            'delay': 0,
        }

    def _add_supplier_to_product(self):
        # Add the partner in the supplier list of the product if the supplier is not registered for
        # this product. We limit to 10 the number of suppliers for a product to avoid the mess that
        # could be caused for some generic products ("Miscellaneous").
        for line in self.order_line:
            # Do not add a contact as a supplier
            partner = self.partner_id if not self.partner_id.parent_id else self.partner_id.parent_id
            if line.product_id and len(
                    line.product_id.seller_ids) <= 10:
                # Convert the price in the right currency.
                currency = partner.property_purchase_currency_id or self.env.company.currency_id
                price = self.currency_id._convert(line.price_unit, currency, line.company_id,
                                                  line.date_order or fields.Date.today(), round=False)
                # Compute the price for the template's UoM, because the supplier's UoM is related to that UoM.
                if line.product_id.product_tmpl_id.uom_po_id != line.product_uom:
                    default_uom = line.product_id.product_tmpl_id.uom_po_id
                    price = line.product_uom._compute_price(price, default_uom)

                supplierinfo = self._prepare_supplier_info(partner, line, price, currency)
                # In case the order partner is a contact address, a new supplierinfo is created on
                # the parent company. In this case, we keep the product name and code.
                seller = line.product_id._select_seller(
                    partner_id=line.partner_id,
                    quantity=line.product_qty,
                    date=line.order_id.date_order and line.order_id.date_order.date(),
                    uom_id=line.product_uom)

                if seller:
                    supplierinfo['product_name'] = seller.product_name
                    supplierinfo['product_code'] = seller.product_code
                vals = {
                    'seller_ids': [(0, 0, supplierinfo)],
                }
                try:
                    line.product_id.write(vals)
                except AccessError:  # no write access rights -> just ignore
                    break

    def _prepare_invoice(self):
        res = super(PurchaseOrderIb_for_supplier, self)._prepare_invoice()
        no_faktur = ''
        for picking_id in self.picking_ids:
            no_faktur = picking_id.customer_invoice

        res['ref'] = no_faktur
        return res


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"


    # Set default value quantity is '0' on purchase order line
    def _suggest_quantity(self):
        '''
        Suggest a minimal quantity based on the seller
        '''
        if not self.product_id:
            return
        seller_min_qty = self.product_id.seller_ids\
            .filtered(lambda r: r.name == self.order_id.partner_id and (not r.product_id or r.product_id == self.product_id))\
            .sorted(key=lambda r: r.min_qty)
        if seller_min_qty:
            self.product_qty = 0.0
            # self.product_qty = seller_min_qty[0].min_qty or 1.0
            self.product_uom = seller_min_qty[0].product_uom
        else:
            self.product_qty = 0.0