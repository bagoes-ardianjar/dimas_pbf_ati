from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

header_title = ['Tanggal', 'Jum. Penjualan', 'Jumlah Pajak', 'Jum. Ongkir', 'Jum. Retur', 'Jum. Retur Pajak', 'Total COD', 'Total Tempo', 'Total Debit']
class ReportInOutStock(models.Model):
    _name = 'report.ati_pbbf_sale.sale_daily.xlsx'
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
        sheet.merge_range(1, 0, 1, 7, 'Laporan Rekap Penjualan Per Hari', formatHeaderCompany)
        sheet.merge_range(2, 0, 2, 7, f'Periode {periode}', formatSubHeaderCompanyBold)
        sheet.merge_range(3, 0, 3, 7, '(Dalam Rupiah)', formatSubHeaderCompany)

        row =  5
        column = 0
        for header in header_title:
            sheet.write(row, column, header, formatHeaderTable)
            column += 1
        
        row += 1
        row_start = row + 1
        self._cr.execute(
            """
                select
                    o.tanggal as tanggal,
                    coalesce(sum(o.penjualan),0) as penjualan,
                    coalesce(sum(o.pajak),0) as pajak,
                    coalesce(sum(o.retur),0) as retur,
                    coalesce(sum(o.retur_pajak),0) as retur_pajak,
                    coalesce(sum(o.total_cod_so),0) as total_cod_so,
                    coalesce(sum(o.total_tempo_so),0) as total_tempo_so,
                    coalesce(sum(o.total_cod_retur),0) as total_cod_retur,
                    coalesce(sum(o.total_tempo_retur),0) as total_tempo_retur
                    from(
                        select 
                            date(a.invoice_date) as tanggal,
                            case 
                                when a.total_global_discount >= 0 then 
                                coalesce((a.amount_untaxed - a.total_global_discount),0)
                                else coalesce((a.amount_untaxed + a.total_global_discount),0)
                            end as penjualan,
                            case 
                                when a.total_all_tax >= 0 then
                                coalesce((a.total_all_tax),0)
                                else coalesce((a.total_all_tax),0)
                            end as pajak,
                            coalesce((select sum(x.amount_untaxed) 
                                from account_move x 
                                where x.reversed_entry_id = a.id 
                                and x.state in ('draft','approval','posted') 
                                and x.move_type = 'out_refund' 
                                group by x.reversed_entry_id),0) as retur,
                            coalesce((select sum(x.total_all_tax) 
                                from account_move x 
                                where x.reversed_entry_id = a.id 
                                and x.state in ('draft','approval','posted') 
                                and x.move_type = 'out_refund' 
                                group by x.reversed_entry_id),0) as retur_pajak,
                            (select 
                                case 
                                    when y.total_all_tax > 0 then
                                    coalesce((y.amount_untaxed - y.global_order_discount + y.total_all_tax),0)
                                    else coalesce((y.amount_untaxed - y.global_order_discount + y.total_all_tax),0)
                                end
                            from account_move y
                                left join account_payment_term z on z.id = y.invoice_payment_term_id 
                            where y.id = a.id and
                                z.is_cod is True) as total_cod_so,
                            (select 
                                case 
                                    when y.total_all_tax > 0 then
                                    coalesce((y.amount_untaxed - y.global_order_discount + y.total_all_tax),0)
                                    else coalesce((y.amount_untaxed - y.global_order_discount + y.total_all_tax),0)
                                end
                            from account_move y
                                left join account_payment_term z on z.id = y.invoice_payment_term_id 
                            where y.id = a.id and
                                z.is_cod is not True) as total_tempo_so,
                            coalesce((select sum(m.amount_untaxed + m.total_all_tax) 
                                from account_move m 
                                left join account_payment_term n on n.id = m.invoice_payment_term_id
                                where m.reversed_entry_id = a.id 
                                and m.state in ('draft','approval','posted') 
                                and m.move_type = 'out_refund'
                                and n.is_cod is True
                                group by m.reversed_entry_id),0) as total_cod_retur,
                            coalesce((select sum(m.amount_untaxed + m.total_all_tax) 
                                from account_move m 
                                left join account_payment_term n on n.id = m.invoice_payment_term_id
                                where m.reversed_entry_id = a.id 
                                and m.state in ('draft','approval','posted') 
                                and m.move_type = 'out_refund'
                                and n.is_cod is not True
                                group by m.reversed_entry_id),0) as total_tempo_retur
                        from account_move a
                        where
                            DATE(a.invoice_date) >= '{_start_date}' 
                            and DATE(a.invoice_date) <= '{_end_date}'
                            and a.state in ('draft','approval','posted')
                            and a.source_document is not Null
                            and a.move_type = 'out_invoice' ) o
                    group by
                    o.tanggal
                    order by o.tanggal asc
            """.format(_start_date=start_date,_end_date=end_date))
        res_penjualan = self._cr.dictfetchall()

        if res_penjualan:
            total_cod= 0
            total_tempo = 0
            total_debit = 0
            for rec in res_penjualan:
                tanggal = rec.get('tanggal').strftime('%Y-%m-%d') if rec.get('tanggal') else '-'
                sheet.write(row, 0, tanggal, formatDetailTable)
                sheet.write(row, 1, rec.get('penjualan') or '-', formatDetailCurrencyTable)
                sheet.write(row, 2, rec.get('pajak') or '-', formatDetailCurrencyTable)
                sheet.write(row, 3, '', formatDetailCurrencyTable)
                sheet.write(row, 4, rec.get('retur') or '-', formatDetailCurrencyTable)
                sheet.write(row, 5, rec.get('retur_pajak') or '-', formatDetailCurrencyTable)
                total_cod = rec.get('total_cod_so') - rec.get('total_cod_retur')
                sheet.write(row, 6, total_cod, formatDetailCurrencyTable)
                total_tempo = rec.get('total_tempo_so') - rec.get('total_tempo_retur')
                sheet.write(row, 7, total_tempo, formatDetailCurrencyTable)
                total_debit = (rec.get('penjualan') + rec.get('pajak')) - (rec.get('retur') + rec.get('retur_pajak'))
                sheet.write(row, 8, total_debit, formatDetailCurrencyTable)
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
        # total_debit = 0
        # for lod in list_of_date:
        #     pembelian = 0
        #     pajak = 0
        #     ongkir = 0
        #     retur = 0
        #     retur_pajak = 0
        #     total_tunai = 0
        #     total_debit = 0
        #     amount_tax = 0
        #     total_cod = 0
        #     total_tempo = 0
        #     total_cod_so = 0
        #     total_tempo_so = 0
        #     total_cod_return = 0
        #     total_tempo_return = 0
        #     # sale_order_ids = self.env['sale.order'].sudo().search([('state', 'in', ['sale', 'done']), ('date_order', '>=', lod), ('date_order', '<=', lod)], order='date_order asc')
        #     sale_order_ids = self.env['account.move'].sudo().search([('state', 'in', ['draft','posted']), ('invoice_date', '>=', lod), ('invoice_date', '<=', lod),('move_type','=','out_invoice')], order='invoice_date asc')
        #
        #     for order in sale_order_ids:
        #         pembelian += ((order.amount_untaxed or 0) + (order.total_global_discount or 0))
        #         if order.amount_tax >= 0 :
        #             amount_tax = order.amount_tax
        #         elif order.amount_tax < 0 :
        #             amount_tax = -1 * order.amount_tax
        #         pajak += amount_tax or 0
        #         if order.invoice_payment_term_id.is_cod != False:
        #             total_cod_so += ((order.amount_untaxed or 0) + (order.total_global_discount or 0)) + (amount_tax or 0)
        #         if order.invoice_payment_term_id.is_cod == False:
        #             total_tempo_so += ((order.amount_untaxed or 0) + (order.total_global_discount or 0)) + (amount_tax or 0)
        #         # total_debit += (((order.amount_untaxed or 0) + (order.total_global_discount or 0)) + (amount_tax or 0))
        #         # if order.carrier_id and order.order_line and order.order_line.filtered(lambda x: x.product_id == order.carrier_id.product_id):
        #         #     ongkir += sum(ongkos.price_subtotal for ongkos in order.order_line.filtered(lambda x: x.product_id == order.carrier_id.product_id))
        #     credit_note_ids = self.env['account.move'].sudo().search([('move_type', '=', 'out_refund'), ('state', 'in', ['draft','posted']), ('invoice_date', '=', lod)])
        #     for cn in credit_note_ids:
        #         retur += cn.amount_untaxed or 0
        #         retur_pajak += cn.amount_tax or 0
        #         if cn.invoice_payment_term_id.is_cod != False:
        #             total_cod_return += (cn.amount_untaxed or 0) + (cn.amount_tax or 0)
        #         if cn.invoice_payment_term_id.is_cod == False:
        #             total_tempo_return += (cn.amount_untaxed or 0) + (cn.amount_tax or 0)
        #
        #     total_debit = (pembelian + pajak) - (retur + retur_pajak)
        #     total_cod = total_cod_so - total_cod_return
        #     total_tempo = total_tempo_so - total_tempo_return
        #
        #     sheet.write(row, 0, lod.strftime("%d-%m-%Y"), formatDetailTable)
        #     sheet.write(row, 1, pembelian, formatDetailCurrencyTable)
        #     sheet.write(row, 2, pajak, formatDetailCurrencyTable)
        #     sheet.write(row, 3, ongkir, formatDetailCurrencyTable)
        #     sheet.write(row, 4, retur, formatDetailCurrencyTable)
        #     sheet.write(row, 5, retur_pajak, formatDetailCurrencyTable)
        #     sheet.write(row, 6, total_cod, formatDetailCurrencyTable)
        #     sheet.write(row, 7, total_tempo, formatDetailCurrencyTable)
        #     sheet.write(row, 8, total_debit, formatDetailCurrencyTable)
        #     row += 1
        # row_end = row
        # column_end = row_end + 1
        # sheet.write(row, 0, 'Total', formatHeaderTable)
        # sheet.write_formula(f'B{column_end}', f'=SUM(B{row_start}:B{row_end})', formatHeaderCurrencyTable)
        # sheet.write_formula(f'C{column_end}', f'=SUM(C{row_start}:C{row_end})', formatHeaderCurrencyTable)
        # sheet.write_formula(f'D{column_end}', f'=SUM(D{row_start}:D{row_end})', formatHeaderCurrencyTable)
        # sheet.write_formula(f'E{column_end}', f'=SUM(E{row_start}:E{row_end})', formatHeaderCurrencyTable)
        # sheet.write_formula(f'F{column_end}', f'=SUM(F{row_start}:F{row_end})', formatHeaderCurrencyTable)
        # sheet.write_formula(f'G{column_end}', f'=SUM(G{row_start}:G{row_end})', formatHeaderCurrencyTable)
        # sheet.write_formula(f'H{column_end}', f'=SUM(H{row_start}:H{row_end})', formatHeaderCurrencyTable)
        # sheet.write_formula(f'I{column_end}', f'=SUM(I{row_start}:I{row_end})', formatHeaderCurrencyTable)
