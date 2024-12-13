# -*- coding: utf-8 -*-


from odoo import models, fields, api, _


class AccountPayments(models.Model):
    _inherit = 'account.payment'

    is_giro = fields.Boolean(string='Giro')
    tgl_giro = fields.Date(string='Tanggal Giro')
    no_check = fields.Char(string='No Cek')
    payment_method = fields.Char("Related Payment Method", related="payment_method_line_id.name")
    temp_bill = fields.Many2many('account.move', string="Temporary Bill")
    no_credit_note = fields.Char(string='No Credit Note')

    def action_post(self):
        res = super(AccountPayments, self).action_post()
        if self.temp_bill:
            domain = [('account_internal_type', 'in', ('receivable', 'payable')), ('reconciled', '=', False)]
            payment_lines = self.line_ids.filtered_domain(domain)
            lines = self.temp_bill.mapped('line_ids').filtered_domain([('reconciled', '=', False)])
            for account in payment_lines.account_id:
                (payment_lines + lines)\
                    .filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)])\
                    .reconcile()
        return res

    @api.onchange("tgl_giro")
    def onchange_tgl_giro(self):
        for c in self:
            if c.tgl_giro:
                c.date = c.tgl_giro

    def button_print_tanda_terima_barang(self):
        return self.env.ref('ati_invoice_payments.action_report_payment_ttb_custom').report_action(self)
    
    def get_document_retur(self):
        bill_ids = [bill.id for bill in self.reconciled_bill_ids]
        result = []
        bills_ids = []
        for rec in self.temp_bill.filtered(lambda r: r.payment_state == 'paid'):
            ## BILL DATA ##
            if rec.id not in bills_ids:
                bills_ids.append(rec.id)
                # datas_bill = {
                #     'name': rec.name,
                #     'product_name': rec.ref,
                #     'qty': 0,
                #     'total': '{0:,.2f}'.format(rec.amount_total).replace(',', ',') or 0.0,
                #     'invoice_date': rec.invoice_date
                # }
                # result.append(datas_bill)


            ## RETUR DATA ##
            po2_name = [po.name for po in self.env['purchase.order'].sudo().search([('invoice_ids', '=', rec.id), ('state', 'in', ['purchase', 'done'])])]
            retur2_ids = self.env['stock.picking'].sudo().search([
                ('is_return', '=', True),
                ('group_id.name', 'in', po2_name),
                ('state', '=', 'done')
            ])

            for retur2 in retur2_ids:
                for retur2_line in retur2.move_line_ids_without_package:
                    bill_id = self.env['account.move'].search([('source_document_id', '=', retur2.id),('state', '=', 'posted'), ('payment_state', '=', 'paid')])
                    cn_sum = sum(am_line.tax_ids.compute_all(am_line.price_subtotal, am_line.currency_id).get('total_included', am_line.price_subtotal) for am_line in self.env['account.move.line'].sudo().search([
                        ('product_id', '=', retur2_line.product_id.id), ('exclude_from_invoice_tab', '!=', True),
                        ('move_id.state', '=', 'posted'), ('move_id.payment_state', 'in', ['partial', 'paid', 'in_payment']), ('move_id.source_document_id', '=', retur2.id)
                    ]))

                    if bill_id:
                        if bill_id.id not in bills_ids:
                            bills_ids.append(bill_id.id)

                        ref = retur2_line.product_id.name
                        total = '{0:,.2f}'.format(cn_sum).replace(',', ',') or 0.0
                        total_cn = '('+str(total)+')'
                        if retur2_line.qty_done:
                            ref = retur2_line.product_id.name+' (qty: '+str(retur2_line.qty_done)+')'
                        data = {
                            'name': retur2.name,
                            'product_name': ref,
                            'qty': retur2_line.qty_done,
                            'total': total_cn,
                            'invoice_date': bill_id.invoice_date if bill_id else ''
                        }
                        result.append(data)

            ## CREDIT NOTE MANUAL ##
            reconciled_info = rec._get_reconciled_info_JSON_values()
            for line in reconciled_info:
                if line['account_payment_id'] == False and line['move_id']:
                    move_id = self.env['account.move'].search([('id', '=', line['move_id'])], limit=1)
                    if move_id and move_id.id not in bills_ids:
                        bills_ids.append(move_id.id)
                        total = '{0:,.2f}'.format(move_id.amount_total_signed).replace(',', ',') or 0.0
                        total_cn = '('+str(total)+')'
                        data = {
                            'name': move_id.name,
                            'product_name': move_id.ref,
                            'qty': 0,
                            'total': total_cn,
                            'invoice_date': move_id.invoice_date
                        }
                        result.append(data)
        return result

    def get_document_retur_all(self):
        bill_ids = [bill.id for bill in self.reconciled_bill_ids]
        bill_update_ids = [bill.id for bill in self.reconciled_bill_ids.filtered(lambda r: r.payment_state == 'paid')]
        result2 = []
        temp_bill = self.temp_bill
        if self.no_credit_note:
            credit_note = self.no_credit_note.replace(' ','')
            credit_notes = credit_note.split(',')
            move_ids = []
            for crn in credit_notes:
                move_id = self.env['account.move'].sudo().search([('name', '=', crn)])
                if move_id:
                    move_ids.append(move_id)
            if move_ids:
                temp_bill = move_ids

        # for rec in self.temp_bill.filtered(lambda r: r.payment_state == 'paid'):
        for rec in temp_bill:
            bills_ids = []
            ## BILL DATA ##
            if rec.id not in bills_ids:
                bills_ids.append(rec.id)
                datas_bill = {
                    'name': rec.name,
                    'product_name': rec.ref,
                    'qty': 0,
                    'total': '{0:,.2f}'.format(rec.amount_total).replace(',', ',') or 0.0,
                    # 'total': '{0:,.2f}'.format(self.amount).replace(',', ',') or 0.0,
                    'invoice_date': rec.invoice_date
                }
                result2.append(datas_bill)


            ## RETUR DATA ##
            po2_name = [po.name for po in self.env['purchase.order'].sudo().search([('invoice_ids', '=', rec.id), ('state', 'in', ['purchase', 'done'])])]
            retur2_ids = self.env['stock.picking'].sudo().search([
                ('is_return', '=', True),
                ('group_id.name', 'in', po2_name),
                ('state', '=', 'done')
            ])

            for retur2 in retur2_ids:
                for retur2_line in retur2.move_line_ids_without_package:
                    bill_id = self.env['account.move'].search([('source_document_id', '=', retur2.id),('state', '=', 'posted'), ('payment_state', '=', 'paid')])
                    cn_sum = sum(am_line.tax_ids.compute_all(am_line.price_subtotal, am_line.currency_id).get('total_included', am_line.price_subtotal) for am_line in self.env['account.move.line'].sudo().search([
                        ('product_id', '=', retur2_line.product_id.id), ('exclude_from_invoice_tab', '!=', True),
                        ('move_id.state', '=', 'posted'), ('move_id.payment_state', 'in', ['partial', 'paid', 'in_payment']), ('move_id.source_document_id', '=', retur2.id),
                        ('quantity', '=', retur2_line.qty_done)
                    ]))


                    if bill_id and bill_id._get_reconciled_info_JSON_values():
                        if bill_id.id not in bills_ids:
                            bills_ids.append(bill_id.id)

                        ref = retur2_line.product_id.name
                        total = '{0:,.2f}'.format(cn_sum).replace(',', ',') or 0.0
                        total_cn = '('+str(total)+')'
                        total_cn_minus = total
                        if retur2_line.qty_done:
                            ref = retur2_line.product_id.name+' (qty: '+str(retur2_line.qty_done)+')'
                        data = {
                            'name': retur2.name,
                            'product_name': ref,
                            'qty': retur2_line.qty_done,
                            'total': total_cn,
                            'total_cn_minus': cn_sum,
                            'invoice_date': bill_id.invoice_date if bill_id else ''
                        }
                        for line in bill_id._get_reconciled_info_JSON_values():
                            print("line retur", line)
                        cn_summ = sum(line['amount'] for line in bill_id._get_reconciled_info_JSON_values())
                        result2.append(data)

            ## CREDIT NOTE MANUAL ##
            reconciled_info = rec._get_reconciled_info_JSON_values()
            for line in reconciled_info:
                if line['account_payment_id'] == False and line['move_id']:
                    move_id = self.env['account.move'].search([('id', '=', line['move_id'])], limit=1)
                    if move_id and move_id.id not in bills_ids:
                        bills_ids.append(move_id.id)
                        total = '{0:,.2f}'.format(line['amount']).replace(',', ',') or 0.0
                        total_cn = '('+str(total)+')'
                        total_cn_minus = total
                        data = {
                            'name': move_id.name,
                            'product_name': move_id.ref,
                            'qty': 0,
                            'total': total_cn,
                            'total_cn_minus': line['amount'],
                            'invoice_date': move_id.invoice_date
                        }
                        result2.append(data)
        return result2

    def get_amount_faktur(self):
        datas = self.get_document_retur_all()
        total_bills = 0
        total_cns = 0
        for rec in datas:
            total_bill = 0
            if rec.get('total_cn_minus',0) == 0:
                total_bill = float(rec.get('total').replace(",", ""))

            total_bills += total_bill
            total_cns += rec.get('total_cn_minus',0)
        amount = total_bills - total_cns
        return amount

