from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

header_title = ['Kode Supplier', 'Nama Supplier', 'Jum. Pembelian', 'Jumlah Pajak', 'Total Kredit', 'Jumlah Retur', 'Jum. Retur Pajak', 'Jumlah Refund', 'Net Purchase']
class XlsxVendorPurchaseReport(models.Model):
    _name = 'report.ati_purchase_pbf.vendor_purchase.xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objs):
        formatHeaderCompany = workbook.add_format({'font_size': 14, 'valign':'vcenter', 'align': 'center', 'bold': True})
        formatSubHeaderCompanyBold = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'center', 'bold': True})
        formatSubHeaderCompany = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'center'})
        formatHeaderTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'bold': True, 'bg_color':'#4ead2f', 'color':'white', 'text_wrap': True, 'border': 1})
        formatHeaderCurrencyTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'bold': True, 'bg_color':'#4ead2f', 'color':'white', 'num_format': '_-"Rp"* #,##0.00_-;-"Rp"* #,##0.00_-;_-"Rp"* "-"_-;_-@_-', 'text_wrap': True, 'border': 1})
        formatDetailTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre','text_wrap': True, 'border': 1})
        formatDetailCurrencyTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'num_format': '_-"Rp"* #,##0.00_-;-"Rp"* #,##0.00_-;_-"Rp"* "-"_-;_-@_-', 'text_wrap': True, 'border': 1})

        title = 'Laporan Pembelian Per Supplier'
        sheet = workbook.add_worksheet(title)

        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 1, 25)
        sheet.set_column(2, 2, 20)
        sheet.set_column(3, 3, 20)
        sheet.set_column(4, 4, 20)
        sheet.set_column(5, 5, 20)
        sheet.set_column(6, 6, 20)
        sheet.set_column(7, 7, 20)
        sheet.set_column(8, 8, 20)

        start_date = datetime.strptime(data['form']['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['form']['end_date'], '%Y-%m-%d').date()
        partner_id = data['form']['partner_id']
        n_date = (end_date - start_date).days
        periode = start_date.strftime("%d %B %Y") if start_date == end_date else f'{start_date.strftime("%d %B %Y")} - {end_date.strftime("%d %B %Y")}'
        len_header = len(header_title)

        # list_of_date = [start_date + timedelta(days=n) for n in range(n_date+1)]
        sheet.merge_range(1, 0, 1, len_header - 1, 'Laporan Rekap Pembelian Per Supplier', formatHeaderCompany)
        sheet.merge_range(2, 0, 2, len_header - 1, f'Periode {periode}', formatSubHeaderCompanyBold)
        sheet.merge_range(3, 0, 3, len_header -1, '(Dalam Rupiah)', formatSubHeaderCompany)

        row =  5
        column = 0
        for header in header_title:
            sheet.write(row, column, header, formatHeaderTable)
            column += 1
        
        data_all = {}
        list_partner = []
        # purchase_order_ids = self.env['purchase.order'].sudo().search([('state', 'in', ['purchase', 'done']), ('date_planned', '>=', start_date), ('date_planned', '<=', end_date)], order='date_planned asc')
        purchase_order_ids = self.env['account.move'].sudo().search([('state', 'in', ['draft','approval','posted']), ('invoice_date', '>=', start_date), ('invoice_date', '<=', end_date),('move_type','=','in_invoice'),('source_document','!=', False)], order='invoice_date asc')
        if partner_id:
            # purchase_order_ids = self.env['purchase.order'].sudo().search([('state', 'in', ['purchase', 'done']), ('date_planned', '>=', start_date), ('date_planned', '<=', end_date), ('partner_id', '=', partner_id)], order='date_planned asc')
            purchase_order_ids = self.env['account.move'].sudo().search([('state', 'in', ['draft','approval','posted']), ('invoice_date', '>=', start_date), ('invoice_date', '<=', end_date),('move_type','=','in_invoice'),('source_document','!=', False), ('partner_id', '=', partner_id)], order='invoice_date asc')
        for order in purchase_order_ids:
            if order.partner_id.id not in list_partner:
                list_partner.append(order.partner_id.id)
                data_all[order.partner_id.id] = {
                    'code': order.partner_id.code_customer, 
                    'name': order.partner_id.name, 
                    'pembelian': 0.0, 
                    'pajak': 0.0, 
                    'total': 0.0, 
                    'kredit': 0.0,
                    'retur': 0.0, 
                    'retur_pajak': 0.0, 
                    'refund': 0.0
                }
            data_all[order.partner_id.id]['pembelian'] += (order.amount_untaxed - order.total_global_discount)
            # data_all[order.partner_id.id]['pajak'] += order.amount_tax
            data_all[order.partner_id.id]['pajak'] += order.total_all_tax
            # data_all[order.partner_id.id]['pajak'] += (order.amount_total - order.amount_untaxed - order.total_global_discount)
            # data_all[order.partner_id.id]['kredit'] += ((order.amount_untaxed-order.total_global_discount)+order.amount_tax)
            data_all[order.partner_id.id]['kredit'] += ((order.amount_untaxed - order.total_global_discount) + order.total_all_tax)
            # data_all[order.partner_id.id]['kredit'] += (order.amount_total)

        # credit_note_ids = self.env['account.move'].sudo().search([('move_type', '=', 'in_refund'), ('state', '=', 'posted'), ('payment_state', 'in', ['paid', 'in_payment', 'partial']), ('invoice_date', '>=', start_date), ('invoice_date', '<=', end_date)])
        credit_note_ids = self.env['account.move'].sudo().search([('move_type', '=', 'in_refund'), ('state', 'in', ['draft','approval','posted']), ('invoice_date', '>=', start_date), ('invoice_date', '<=', end_date)])
        if partner_id:
            credit_note_ids = self.env['account.move'].sudo().search([('move_type', '=', 'in_refund'), ('state', 'in', ['draft','approval','posted']), ('invoice_date', '>=', start_date), ('invoice_date', '<=', end_date), ('partner_id', '=', partner_id)])
        for cn in credit_note_ids:
            if cn.partner_id.id not in list_partner:
                list_partner.append(cn.partner_id.id)
                data_all[cn.partner_id.id] = {
                    'code': cn.partner_id.code_customer, 
                    'name': cn.partner_id.name, 
                    'pembelian': 0.0, 
                    'pajak': 0.0, 
                    'total': 0.0, 
                    'kredit': 0.0,
                    'retur': 0.0, 
                    'retur_pajak': 0.0, 
                    'refund': 0.0
                }
            data_all[cn.partner_id.id]['retur'] += cn.amount_untaxed
            # cn_amount_tax = -1 * (cn.amount_tax)
            cn_amount_tax = -1 * (cn.total_all_tax)
            data_all[cn.partner_id.id]['retur_pajak'] += cn_amount_tax
            data_all[cn.partner_id.id]['refund'] += cn.amount_untaxed + cn_amount_tax
        
        row += 1
        row_start = row + 1
        for partner in list_partner:
            sheet.write(row, 0, data_all[partner]['code'] or '', formatDetailTable)
            sheet.write(row, 1, data_all[partner]['name'] or '', formatDetailTable)
            sheet.write(row, 2, data_all[partner]['pembelian'], formatDetailCurrencyTable)
            sheet.write(row, 3, data_all[partner]['pajak'], formatDetailCurrencyTable)
            sheet.write(row, 4, data_all[partner]['kredit'], formatDetailCurrencyTable)
            sheet.write(row, 5, data_all[partner]['retur'], formatDetailCurrencyTable)
            sheet.write(row, 6, data_all[partner]['retur_pajak'], formatDetailCurrencyTable)
            sheet.write(row, 7, data_all[partner]['refund'], formatDetailCurrencyTable)
            sheet.write(row, 8, data_all[partner]['kredit'] - data_all[partner]['refund'], formatDetailCurrencyTable)
            row += 1
        row_end = row
        column_end = row_end + 1
        sheet.merge_range(row, 0, row, 1, 'Total', formatHeaderTable)
        sheet.write_formula(f'C{column_end}', f'=SUM(C{row_start}:C{row_end})', formatHeaderCurrencyTable)
        sheet.write_formula(f'D{column_end}', f'=SUM(D{row_start}:D{row_end})', formatHeaderCurrencyTable)
        sheet.write_formula(f'E{column_end}', f'=SUM(E{row_start}:E{row_end})', formatHeaderCurrencyTable)
        sheet.write_formula(f'F{column_end}', f'=SUM(F{row_start}:F{row_end})', formatHeaderCurrencyTable)
        sheet.write_formula(f'G{column_end}', f'=SUM(G{row_start}:G{row_end})', formatHeaderCurrencyTable)
        sheet.write_formula(f'H{column_end}', f'=SUM(H{row_start}:H{row_end})', formatHeaderCurrencyTable)
        sheet.write_formula(f'I{column_end}', f'=SUM(I{row_start}:I{row_end})', formatHeaderCurrencyTable)