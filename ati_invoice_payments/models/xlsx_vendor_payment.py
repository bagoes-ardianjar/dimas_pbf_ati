from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

header_title = ['Nama PBF', 'No TF', 'No Faktur', 'Total Tagihan', 'No. CN/Retur', 'Potongan', 'Tanggal Faktur', 'No. Giro', 'Journal Bank', 'Kategori Rekap', 'Jumlah Giro', 'Umur']
class XlsxVendorPayment(models.Model):
    _name = 'report.ati_invoice_payments.vendor_payment.xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objs):
        formatHeaderCompany = workbook.add_format({'font_size': 14, 'valign':'vcenter', 'align': 'center', 'bold': True})
        formatSubHeaderCompanyBold = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'center', 'bold': True})
        formatSubHeaderCompany = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'center'})
        formatHeaderTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'bold': True, 'bg_color':'#4ead2f', 'color':'white', 'text_wrap': True, 'border': 1})
        formatHeaderCurrencyTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'bold': True, 'bg_color':'#4ead2f', 'color':'white', 'num_format': '_-"Rp"* #,##0.00_-;-"Rp"* #,##0.00_-;_-"Rp"* "-"_-;_-@_-', 'text_wrap': True, 'border': 1})
        formatDetailTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre','text_wrap': True, 'border': 1})
        formatDetailTableLeft = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'left','text_wrap': True, 'border': 1})
        formatDetailCurrencyTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'num_format': '_-"Rp"* #,##0.00_-;-"Rp"* #,##0.00_-;_-"Rp"* "-"_-;_-@_-', 'text_wrap': True, 'border': 1})
        formatDetailTableLeftBold = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'bold': True, 'align': 'left','text_wrap': True, 'border': 1})
        formatDetailCurrencyTableBold = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'bold': True, 'align': 'centre', 'num_format': '_-"Rp"* #,##0.00_-;-"Rp"* #,##0.00_-;_-"Rp"* "-"_-;_-@_-', 'text_wrap': True, 'border': 1})

        title = 'Laporan Tukar Faktur'
        sheet = workbook.add_worksheet(title)

        sheet.set_column(0, 0, 35)
        sheet.set_column(1, 1, 25)
        sheet.set_column(2, 2, 20)
        sheet.set_column(3, 3, 20)
        sheet.set_column(4, 4, 20)
        sheet.set_column(5, 5, 20)
        sheet.set_column(6, 6, 20)
        sheet.set_column(7, 7, 20)
        sheet.set_column(8, 8, 20)
        sheet.set_column(9, 9, 20)
        sheet.set_column(10, 10, 20)

        start_date = datetime.strptime(data['form']['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['form']['end_date'], '%Y-%m-%d').date()
        category = data['form']['category']
        periode = start_date.strftime("%d %B %Y") if start_date == end_date else f'{start_date.strftime("%d %B %Y")} - {end_date.strftime("%d %B %Y")}'
        len_header = len(header_title)

        sheet.merge_range(1, 0, 1, len_header - 1, 'Laporan Tukar Faktur', formatHeaderCompany)
        sheet.merge_range(2, 0, 2, len_header - 1, f'Periode {periode}', formatSubHeaderCompanyBold)
        sheet.merge_range(3, 0, 3, len_header -1, '(Dalam Rupiah)', formatSubHeaderCompany)

        row =  5
        column = 0
        for header in header_title:
            sheet.write(row, column, header, formatHeaderTable)
            column += 1
        partner_ids = self.env['res.partner'].sudo().search([('supplier_rank', '>', 0)], order='name asc')
        row += 1
        Payment = self.env['account.payment'].sudo()
        AccountMove = self.env['account.move'].sudo()
        for partner in partner_ids:
            amount_temp = 0
            ## PAYMENT ##
            payment_ids = self.env['account.payment']
            if not category:
                payment_ids |= self.env['account.payment'].sudo().search(
                    [('partner_id', '=', partner.id), ('state', '=', 'draft'),
                     ('create_date', '>=', start_date),
                     ('create_date', '<=', end_date)])
            else:
                payment_ids |= self.env['account.payment'].sudo().search([('partner_id', '=', partner.id), ('state', '=', 'draft'), ('partner_id.x_studio_jenis_order', '=', category), ('create_date', '>=', start_date), ('create_date', '<=', end_date)])
            if payment_ids:
                # print("\npartner", partner.name, payment_ids)
                for rec in payment_ids.filtered(lambda r: r.state == 'draft'):
                    temp_bill = rec.temp_bill
                    if rec.no_credit_note:
                        credit_note = rec.no_credit_note.replace(' ','')
                        credit_notes = credit_note.split(',')
                        move_ids = []
                        for crn in credit_notes:
                            move_id = self.env['account.move'].sudo().search([('name', '=', crn)])
                            if move_id:
                                move_ids.append(move_id)
                        if move_ids:
                            temp_bill = move_ids
                    # print("\npayment", rec.name, rec.temp_bill, rec.no_credit_note, rec.reconciled_bill_ids, partner.name)
                    # bills_ids = []
                    # for bill in rec.temp_bill.filtered(lambda r: r.payment_state == 'paid'):
                    for bill in temp_bill:
                        bills_ids = []
                        ## BILL DATA ##
                        if bill.id not in bills_ids:
                            bills_ids.append(bill.id)
                            ttf_name = 'TTF/'+rec.name
                            json_values = bill._get_reconciled_info_JSON_values()
                            no_cek = ', '.join(Payment.browse(val['account_payment_id']).no_check or '' if val['account_payment_id'] else '' for val in json_values)
                            aging_vb = (bill.invoice_date_due - fields.Date.today()).days
                            # print("\nbill.name", row, bill.name)

                            ## WRITE DATA ##
                            sheet.write(row, 0, rec.partner_id.name or '', formatDetailTableLeft)
                            sheet.write(row, 1, ttf_name or '', formatDetailTable)
                            sheet.write(row, 2, bill.name or '', formatDetailTable)
                            sheet.write(row, 3, bill.amount_total, formatDetailCurrencyTable)
                            sheet.write(row, 6, datetime.strftime(bill.invoice_date, "%d-%m-%Y"), formatDetailTable)
                            sheet.write(row, 7, no_cek or '', formatDetailTable)
                            sheet.write(row, 8, rec.journal_id.name or '', formatDetailTable)
                            if not category:
                                sheet.write(row, 9, '', formatDetailTable)
                            else:
                                if rec.partner_id.x_studio_jenis_order == 'jabodetabek':
                                    sheet.write(row, 9, 'Jabodetabek', formatDetailTable)
                                elif rec.partner_id.x_studio_jenis_order == 'non-jabodetabek':
                                    sheet.write(row, 9, 'Non Jabodetabek', formatDetailTable)
                            # sheet.write(row, 8, bill.amount_total, formatDetailCurrencyTable)
                            sheet.write(row, 11, aging_vb or '', formatDetailTable)
                            # sheet.write(row, 6, aging_vb if bill.payment_state == 'not_paid' else '')
                            row += 1
                            x = 0
                            total_potongan = 0
                            result_crn = []

                            ## RETUR DATA ##
                            po2_name = [po.name for po in self.env['purchase.order'].sudo().search([('invoice_ids', '=', bill.id), ('state', 'in', ['purchase', 'done'])])]
                            retur2_ids = self.env['stock.picking'].sudo().search([
                                ('is_return', '=', True),
                                ('group_id.name', 'in', po2_name),
                                ('state', '=', 'done')
                            ])

                            for retur2 in retur2_ids:
                                refs = []
                                bills_name = []
                                returs_name = []
                                total = 0
                                bill_id = self.env['account.move'].search([('source_document_id', '=', retur2.id),('state', '=', 'posted'), ('payment_state', '=', 'paid')])
                                for retur2_line in retur2.move_line_ids_without_package:
                                    cn_sum_2 = sum(am_line.tax_ids.compute_all(am_line.price_subtotal, am_line.currency_id).get('total_included', am_line.price_subtotal) for am_line in self.env['account.move.line'].sudo().search([
                                        ('product_id', '=', retur2_line.product_id.id), ('exclude_from_invoice_tab', '!=', True),
                                        ('move_id.state', '=', 'posted'), ('move_id.payment_state', 'in', ['partial', 'paid', 'in_payment']), ('move_id.source_document_id', '=', retur2.id)
                                    ]))
                                    cn_sum = 0

                                    if bill_id:
                                        if bill_id.id not in bills_ids:
                                            bills_ids.append(bill_id.id)
                                            bills_name.append(bill_id.name)
                                            cn_sum = sum(line['amount'] for line in bill_id._get_reconciled_info_JSON_values())
                                        if retur2.name not in returs_name:
                                            returs_name.append(retur2.name)

                                        ref = retur2_line.product_id.name
                                        total += cn_sum
                                        total_potongan += cn_sum
                                        # total = '{0:,.2f}'.format(cn_sum).replace(',', ',') or 0.0
                                        # total_cn = '('+str(total)+')'
                                        if retur2_line.qty_done:
                                            ref = retur2_line.product_id.name+' (qty: '+str(retur2_line.qty_done)+')'

                                        if ref:
                                            refs.append(ref)



                                if bill_id:
                                    # print("\nbill", bill.name)
                                    refs_str = ', '.join(x for x in refs)
                                    bills_name_str = ' '.join(x for x in bills_name)
                                    returs_name_str = ' '.join(x for x in returs_name)
                                    # print("detail Return", row, bills_name_str, returs_name_str, bill_id.reason_return_id.name, refs_str)
                                    detail_return = ''
                                    retur = bill_id._get_reconciled_info_JSON_values()
                                    if retur:
                                        if bills_name_str:
                                            detail_return += bills_name_str
                                        if returs_name_str:
                                            detail_return += ', '
                                            detail_return += returs_name_str
                                        if bill_id.reason_return_id:
                                            detail_return += ', '
                                            detail_return += bill_id.reason_return_id.name
                                        if refs_str:
                                            detail_return += ', '
                                            detail_return += refs_str
                                    data = {
                                        'bill_name': bills_name_str,
                                        'retur_name': returs_name_str,
                                        'reason': bill_id.reason_return_id.name,
                                        'ref': refs_str
                                    }
                                    result_crn.append(data)

                                    ## WRITE DATA ##
                                    if x == 0:
                                        row = row-1
                                        sheet.write(row, 4, detail_return or '', formatDetailTable)
                                        sheet.write(row, 5, total, formatDetailCurrencyTable)
                                        row += 1
                                        x += 1
                                    else:
                                        sheet.write(row, 0, rec.partner_id.name or '', formatDetailTableLeft)
                                        sheet.write(row, 1, ttf_name or '', formatDetailTable)
                                        sheet.write(row, 2, bill.name or '', formatDetailTable)
                                        sheet.write(row, 3, '', formatDetailTable)
                                        sheet.write(row, 4, detail_return or '', formatDetailTable)
                                        sheet.write(row, 5, total, formatDetailCurrencyTable)
                                        sheet.write(row, 6, datetime.strftime(bill.invoice_date, "%d-%m-%Y"),formatDetailTable)
                                        sheet.write(row, 7, '', formatDetailTable)
                                        sheet.write(row, 8, rec.journal_id.name or '', formatDetailTable)
                                        sheet.write(row, 9, '', formatDetailTable)
                                        sheet.write(row, 10, '', formatDetailTable)
                                        sheet.write(row, 11, '', formatDetailTable)
                                        row += 1
                                        x += 1

                            ## CREDIT NOTE MANUAL ##
                            reconciled_info = bill._get_reconciled_info_JSON_values()
                            refs_manual = []
                            bills_name_manual = []
                            for line in reconciled_info:
                                if line['account_payment_id'] == False and line['move_id']:
                                    move_id = self.env['account.move'].search([('id', '=', line['move_id'])], limit=1)
                                    if move_id and move_id.id not in bills_ids:
                                        bills_ids.append(move_id.id)
                                        total = '{0:,.2f}'.format(line['amount']).replace(',', ',') or 0.0
                                        total_cn = '('+str(total)+')'
                                        ref = move_id.ref or ''
                                        name = move_id.name or ''
                                        data = {
                                            'name': name,
                                            'product_name': ref,
                                            'qty': 0,
                                            'total': total_cn,
                                            'invoice_date': move_id.invoice_date
                                        }
                                        result_crn.append(data)
                                        refs_manual.append(ref)
                                        bills_name_manual.append(name)
                                        total_potongan += line['amount']
                                        detail_return = name
                                        if ref:
                                            detail_return += ', '
                                            detail_return += ref
                                        if x == 0:
                                            row = row-1
                                            sheet.write(row, 4, detail_return or '', formatDetailTable)
                                            sheet.write(row, 5, line['amount'] or 0, formatDetailCurrencyTable)
                                            row += 1
                                            x += 1
                                        else:
                                            sheet.write(row, 0, rec.partner_id.name or '', formatDetailTableLeft)
                                            sheet.write(row, 1, ttf_name or '', formatDetailTable)
                                            sheet.write(row, 2, bill.name or '', formatDetailTable)
                                            sheet.write(row, 3, '', formatDetailTable)
                                            sheet.write(row, 4, detail_return or '', formatDetailTable)
                                            sheet.write(row, 5, line['amount'] or 0, formatDetailCurrencyTable)
                                            sheet.write(row, 6, datetime.strftime(bill.invoice_date, "%d-%m-%Y"),formatDetailTable)
                                            sheet.write(row, 7, '', formatDetailTable)
                                            sheet.write(row, 8, rec.journal_id.name or '', formatDetailTable)
                                            sheet.write(row, 9, '', formatDetailTable)
                                            sheet.write(row, 10, '', formatDetailTable)
                                            sheet.write(row, 11, '', formatDetailTable)
                                            row += 1
                                            x += 1
                                        # row += 1
                            # print("XXXXX TERAKHIR", row, x, total_potongan, bill.amount_total-total_potongan)
                            total = bill.amount_total-total_potongan
                            if result_crn:
                                sheet.write(row-x, 10, total, formatDetailCurrencyTable)
                            else:
                                sheet.write(row-1, 4, '', formatDetailTable)
                                sheet.write(row-1, 5, 0, formatDetailCurrencyTable)
                                sheet.write(row-1, 10, total, formatDetailCurrencyTable)

                            refs_str_manual = ''
                            bills_name_str_manual = ''
                            if bills_name_manual:
                                bills_name_str_manual = ' '.join(x for x in bills_name_manual)
                            if refs_manual:
                                refs_str_manual = ' '.join(x for x in refs_manual)

                            # print("\nbill", bill.name, bills_ids)
                            # print("detail", refs_str_manual, bills_name_str_manual)

                            amount_temp += total

                sheet.write(row, 0, f'{partner.name} Total' or '', formatDetailTableLeftBold)
                sheet.write(row, 1, '', formatDetailTable)
                sheet.write(row, 2, '', formatDetailTable)
                sheet.write(row, 3, '', formatDetailTable)
                sheet.write(row, 4, '', formatDetailTable)
                sheet.write(row, 5, '', formatDetailTable)
                sheet.write(row, 6, '', formatDetailTable)
                sheet.write(row, 7, '', formatDetailTable)
                sheet.write(row, 8, '', formatDetailTable)
                sheet.write(row, 9, '', formatDetailTable)
                sheet.write(row, 10, amount_temp, formatDetailCurrencyTableBold)
                sheet.write(row, 11, '', formatDetailTable)
                row += 1
                sheet.write(row, 0, '', formatDetailTable)
                sheet.write(row, 1, '', formatDetailTable)
                sheet.write(row, 2, '', formatDetailTable)
                sheet.write(row, 3, '', formatDetailTable)
                sheet.write(row, 4, '', formatDetailTable)
                sheet.write(row, 5, '', formatDetailTable)
                sheet.write(row, 6, '', formatDetailTable)
                sheet.write(row, 7, '', formatDetailTable)
                sheet.write(row, 8, '', formatDetailTable)
                sheet.write(row, 9, '', formatDetailTable)
                sheet.write(row, 10, '', formatDetailTable)
                sheet.write(row, 11, '', formatDetailTable)
                row += 1


            # vendor_bill_ids = self.env['account.move'].sudo().search([('partner_id', '=', partner.id), ('move_type', '=', 'in_invoice'), ('state', '=', 'posted'), ('invoice_date', '>=', start_date), ('invoice_date', '<=', end_date)], order='invoice_date asc')
            # for bill in vendor_bill_ids:
            #     ttf_name = False
            #     no_cek = False
            #     aging_vb = False
            #     if bill.payment_state != 'not_paid':
            #         json_values = bill._get_reconciled_info_JSON_values()
            #
            #         no_cek = ', '.join(Payment.browse(val['account_payment_id']).no_check or '' if val['account_payment_id'] else '' for val in json_values)
            #         ttf_name = ', '.join(f"TTF/{Payment.browse(val['account_payment_id']).name}" or '' if val['account_payment_id'] else f"TTF/{AccountMove.browse(val['move_id']).name}" or '' for val in json_values)
            #     aging_vb = (bill.invoice_date_due - fields.Date.today()).days
            #
            #     sheet.write(row, 0, bill.partner_id.name or '', formatDetailTableLeft)
            #     sheet.write(row, 1, ttf_name or '', formatDetailTable)
            #     sheet.write(row, 2, bill.name or '', formatDetailTable)
            #     sheet.write(row, 3, bill.amount_total, formatDetailCurrencyTable)
            #     sheet.write(row, 4, datetime.strftime(bill.invoice_date, "%d-%m-%Y"), formatDetailTable)
            #     sheet.write(row, 5, no_cek or '', formatDetailTable)
            #     sheet.write(row, 6, bill.amount_total, formatDetailCurrencyTable)
            #     sheet.write(row, 7, aging_vb or '', formatDetailTable)
            #     # sheet.write(row, 6, aging_vb if bill.payment_state == 'not_paid' else '')
            #     row += 1
            #     amount_temp += bill.amount_total
            # if len(vendor_bill_ids) > 0:
            #     sheet.write(row, 0, f'{partner.name} Total' or '', formatDetailTableLeftBold)
            #     sheet.write(row, 1, '', formatDetailTable)
            #     sheet.write(row, 2, '', formatDetailTable)
            #     sheet.write(row, 3, '', formatDetailTable)
            #     sheet.write(row, 4, '', formatDetailTable)
            #     sheet.write(row, 5, '', formatDetailTable)
            #     sheet.write(row, 6, amount_temp, formatDetailCurrencyTableBold)
            #     sheet.write(row, 7, '', formatDetailTable)
            #     row += 1
            #     sheet.write(row, 0, '', formatDetailTable)
            #     sheet.write(row, 1, '', formatDetailTable)
            #     sheet.write(row, 2, '', formatDetailTable)
            #     sheet.write(row, 3, '', formatDetailTable)
            #     sheet.write(row, 4, '', formatDetailTable)
            #     sheet.write(row, 5, '', formatDetailTable)
            #     sheet.write(row, 6, '', formatDetailTable)
            #     sheet.write(row, 7, '', formatDetailTable)
            #     row += 1