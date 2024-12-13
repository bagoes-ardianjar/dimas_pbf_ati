from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

header_title = ['Tanggal', 'Jum. Pembelian', 'Jumlah Pajak', 'Jum. Ongkir', 'Jum. Retur', 'Jum. Retur Pajak', 'Total COD', 'Total Tempo', 'Total Credit']
class ReportInOutStock(models.Model):
    _name = 'report.ati_purchase_pbf.purchase_daily.xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objs):
        formatHeaderCompany = workbook.add_format({'font_size': 14, 'valign':'vcenter', 'align': 'center', 'bold': True})
        formatSubHeaderCompanyBold = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'center', 'bold': True})
        formatSubHeaderCompany = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'center'})
        formatHeaderTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'bold': True, 'bg_color':'#4ead2f', 'color':'white', 'text_wrap': True, 'border': 1})
        formatHeaderCurrencyTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'bold': True, 'bg_color':'#4ead2f', 'color':'white', 'num_format': '_-"Rp"* #,##0.00_-;-"Rp"* #,##0.00_-;_-"Rp"* "-"_-;_-@_-', 'text_wrap': True, 'border': 1})
        formatDetailTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre','text_wrap': True, 'border': 1})
        formatDetailCurrencyTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'num_format': '_-"Rp"* #,##0.00_-;-"Rp"* #,##0.00_-;_-"Rp"* "-"_-;_-@_-', 'text_wrap': True, 'border': 1})

        title = 'Laporan Rekap Pembelian Per Hari'
        sheet = workbook.add_worksheet(title)

        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 20)
        sheet.set_column(3, 3, 20)
        sheet.set_column(4, 4, 20)
        sheet.set_column(5, 5, 20)
        sheet.set_column(6, 6, 20)
        sheet.set_column(7, 7, 20)
        sheet.set_column(8, 8, 20)

        start_date = datetime.strptime(data['form']['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['form']['end_date'], '%Y-%m-%d').date()
        n_date = (end_date - start_date).days
        periode = start_date.strftime("%d %B %Y") if start_date == end_date else f'{start_date.strftime("%d %B %Y")} - {end_date.strftime("%d %B %Y")}'

        list_of_date = [start_date + timedelta(days=n) for n in range(n_date+1)]
        sheet.merge_range(1, 0, 1, 7, 'Laporan Rekap Pembelian Per Hari', formatHeaderCompany)
        sheet.merge_range(2, 0, 2, 7, f'Periode {periode}', formatSubHeaderCompanyBold)
        sheet.merge_range(3, 0, 3, 7, '(Dalam Rupiah)', formatSubHeaderCompany)

        row =  5
        column = 0
        for header in header_title:
            sheet.write(row, column, header, formatHeaderTable)
            column += 1
        
        delivery_product = [delivery.product_id.id for delivery in self.env['delivery.carrier'].sudo().search([('active', '=', True)])]

        row += 1
        row_start = row + 1
        total_kredit = 0
        for lod in list_of_date:
            pembelian = 0
            pajak = 0
            ongkir = 0
            retur = 0
            retur_pajak = 0
            total_tunai = 0
            total_kredit = 0
            kredit = 0
            # purchase_order_ids = self.env['purchase.order'].sudo().search([('state', 'in', ['purchase', 'done']), ('date_planned', '>=', lod), ('date_planned', '<=', lod)], order='date_planned asc')
            purchase_order_ids = self.env['account.move'].sudo().search([('state', 'in', ['draft','approval','posted']), ('invoice_date', '>=', lod), ('invoice_date', '<=', lod),('move_type','=','in_invoice'),('source_document','!=', False)], order='invoice_date asc')
            for order in purchase_order_ids:
                kredit += order.amount_total
                pembelian += ((order.amount_untaxed or 0) - (order.total_global_discount or 0))
                # pajak += order.amount_tax or 0
                pajak += order.total_all_tax or 0
                # pajak += (order.amount_total - round(order.amount_untaxed,2) - order.total_global_discount) or 0
                # total_kredit += (((order.amount_untaxed or 0) - (order.total_global_discount or 0)) + (order.amount_tax or 0))
                # if delivery_product and order.order_line and order.order_line.filtered(lambda x: x.product_id.id in delivery_product):
                #     ongkir += sum(ongkos.price_subtotal for ongkos in order.order_line.filtered(lambda x: x.product_id.id in delivery_product))
            # refund_ids = self.env['account.move'].sudo().search([('move_type', '=', 'in_refund'), ('state', '=', 'posted'), ('payment_state', 'in', ['paid', 'in_payment', 'partial']), ('invoice_date', '=', lod)])
            refund_ids = self.env['account.move'].sudo().search([('move_type', '=', 'in_refund'), ('state', 'in', ['draft','approval','posted']), ('invoice_date', '>=', lod), ('invoice_date', '<=', lod)])
            for refund in refund_ids:
                retur += refund.amount_untaxed or 0
                # retur = refund.amount_untaxed or 0
                # refund_amount_tax = -1 * (refund.amount_tax)
                refund_amount_tax = -1 * (refund.total_all_tax)
                retur_pajak += refund_amount_tax or 0
            total_kredit = (pembelian + pajak) - (retur + retur_pajak)
            # total_kredit = (kredit) - (retur + retur_pajak)
            total_cod = 0
            total_tempo = 0
            for order in purchase_order_ids:
                if order.invoice_payment_term_id.is_cod != False:
                    total_cod = total_kredit
                    total_tempo = 0
                else:
                    total_cod = 0
                    total_tempo = total_kredit
            sheet.write(row, 0, lod.strftime("%d-%m-%Y"), formatDetailTable)
            sheet.write(row, 1, pembelian, formatDetailCurrencyTable)
            sheet.write(row, 2, pajak, formatDetailCurrencyTable)
            sheet.write(row, 3, ongkir, formatDetailCurrencyTable)
            sheet.write(row, 4, retur, formatDetailCurrencyTable)
            sheet.write(row, 5, retur_pajak, formatDetailCurrencyTable)
            sheet.write(row, 6, total_cod, formatDetailCurrencyTable)
            sheet.write(row, 7, total_tempo, formatDetailCurrencyTable)
            sheet.write(row, 8, total_kredit, formatDetailCurrencyTable)
            row += 1
        row_end = row
        column_end = row_end + 1
        sheet.write(row, 0, 'Total', formatHeaderTable)
        sheet.write_formula(f'B{column_end}', f'=SUM(B{row_start}:B{row_end})', formatHeaderCurrencyTable)
        sheet.write_formula(f'C{column_end}', f'=SUM(C{row_start}:C{row_end})', formatHeaderCurrencyTable)
        sheet.write_formula(f'D{column_end}', f'=SUM(D{row_start}:D{row_end})', formatHeaderCurrencyTable)
        sheet.write_formula(f'E{column_end}', f'=SUM(E{row_start}:E{row_end})', formatHeaderCurrencyTable)
        sheet.write_formula(f'F{column_end}', f'=SUM(F{row_start}:F{row_end})', formatHeaderCurrencyTable)
        sheet.write_formula(f'G{column_end}', f'=SUM(G{row_start}:G{row_end})', formatHeaderCurrencyTable)
        sheet.write_formula(f'H{column_end}', f'=SUM(H{row_start}:H{row_end})', formatHeaderCurrencyTable)
        sheet.write_formula(f'I{column_end}', f'=SUM(I{row_start}:I{row_end})', formatHeaderCurrencyTable)
