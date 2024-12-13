from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

header_title = ['Kode Customer', 'Nama Customer', 'Nama Panel', 'Jum. Penjualan', 'Jumlah Pajak', 'Total Debit', 'Jumlah Retur', 'Jum. Retur Pajak', 'Jumlah Refund', 'Net Sales']
class XlsxCustomerSaleReport(models.Model):
    _name = 'report.ati_pbf_sale.customer_sale.xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objs):
        formatHeaderCompany = workbook.add_format({'font_size': 14, 'valign':'vcenter', 'align': 'center', 'bold': True})
        formatSubHeaderCompanyBold = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'center', 'bold': True})
        formatSubHeaderCompany = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'center'})
        formatHeaderTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'bold': True, 'bg_color':'#4ead2f', 'color':'white', 'text_wrap': True, 'border': 1})
        formatHeaderCurrencyTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'bold': True, 'bg_color':'#4ead2f', 'color':'white', 'num_format': '_-"Rp"* #,##0.00_-;-"Rp"* #,##0.00_-;_-"Rp"* "-"_-;_-@_-', 'text_wrap': True, 'border': 1})
        formatDetailTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre','text_wrap': True, 'border': 1})
        formatDetailCurrencyTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'num_format': '_-"Rp"* #,##0.00_-;-"Rp"* #,##0.00_-;_-"Rp"* "-"_-;_-@_-', 'text_wrap': True, 'border': 1})

        title = 'Laporan Penjualan Per Customer'
        sheet = workbook.add_worksheet(title)

        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 1, 25)
        sheet.set_column(2, 2, 15)
        sheet.set_column(3, 3, 20)
        sheet.set_column(4, 4, 20)
        sheet.set_column(5, 5, 20)
        sheet.set_column(6, 6, 20)
        sheet.set_column(7, 7, 20)
        sheet.set_column(8, 8, 20)
        sheet.set_column(9, 9, 20)

        start_date = datetime.strptime(data['form']['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['form']['end_date'], '%Y-%m-%d').date()
        partner_id = data['form']['partner_id']
        is_pasien = data['form']['is_pasien']
        n_date = (end_date - start_date).days
        periode = start_date.strftime("%d %B %Y") if start_date == end_date else f'{start_date.strftime("%d %B %Y")} - {end_date.strftime("%d %B %Y")}'
        len_header = len(header_title)

        # list_of_date = [start_date + timedelta(days=n) for n in range(n_date+1)]
        sheet.merge_range(1, 0, 1, len_header - 1, 'Laporan Rekap Penjualan Per Customer', formatHeaderCompany)
        sheet.merge_range(2, 0, 2, len_header - 1, f'Periode {periode}', formatSubHeaderCompanyBold)
        sheet.merge_range(3, 0, 3, len_header -1, '(Dalam Rupiah)', formatSubHeaderCompany)

        row =  5
        column = 0
        for header in header_title:
            sheet.write(row, column, header, formatHeaderTable)
            column += 1
        
        data_all = {}
        list_partner = []
        total_all_tax = 0
        # sale_order_ids = self.env['sale.order'].sudo().search([('state', 'in', ['sale', 'done']), ('date_order', '>=', start_date), ('date_order', '<=', end_date)], order='date_order asc')
        # sale_order_ids = self.env['account.move'].sudo().search([('state', 'in', ['posted']), ('invoice_date', '>=', start_date), ('invoice_date', '<=', end_date),('move_type','=','out_invoice')], order='invoice_date asc')
        if partner_id and is_pasien==True:
            self._cr.execute("""(
                   select a.id 
                   from account_move a
                       left join sale_order b on b.name = a.invoice_origin 
                   where a.state in ('draft', 'approval','posted') 
                       and date(a.invoice_date) >= '{_start_date}'
                       and date(a.invoice_date) <= '{_end_date}'
                       and a.move_type = 'out_invoice' 
                       and a.source_document is not Null
                       and b.is_pasien = True
                       and a.partner_id = {_partner_id}
                       order by date(a.invoice_date) asc
               )""".format(_start_date=str(start_date), _end_date=str(end_date), _partner_id=partner_id))
            move_id = self._cr.fetchall()
            sale_order_ids = self.env['account.move'].sudo().search([('id', 'in', move_id)], order='invoice_date asc')
            credit_note_ids = self.env['account.move'].sudo().search([('reversed_entry_id', 'in', move_id)])
        elif partner_id and is_pasien==False:
            self._cr.execute("""(
                   select a.id 
                   from account_move a
                       left join sale_order b on b.name = a.invoice_origin 
                   where a.state in ('draft', 'approval', 'posted')  
                       and date(a.invoice_date) >= '{_start_date}'
                       and date(a.invoice_date) <= '{_end_date}'
                       and a.move_type = 'out_invoice' 
                       and a.source_document is not Null
                       and b.is_pasien is not True
                       and a.partner_id = {_partner_id}
                       order by date(a.invoice_date) asc
               )""".format(_start_date=str(start_date), _end_date=str(end_date),_partner_id=partner_id))
            move_id = self._cr.fetchall()
            sale_order_ids = self.env['account.move'].sudo().search([('id', 'in', move_id)], order='invoice_date asc')
            credit_note_ids = self.env['account.move'].sudo().search([('reversed_entry_id', 'in', move_id)])
        elif not partner_id and is_pasien==True:
            self._cr.execute("""(
                select a.id 
                from account_move a
                    left join sale_order b on b.name = a.invoice_origin 
                where a.state in ('draft', 'approval', 'posted') 
                    and date(a.invoice_date) >= '{_start_date}'
                    and date(a.invoice_date) <= '{_end_date}'
                    and a.move_type = 'out_invoice' 
                    and a.source_document is not Null
                    and b.is_pasien = True
                    order by date(a.invoice_date) asc
            )""".format(_start_date=str(start_date),_end_date=str(end_date)))
            move_id = self._cr.fetchall()
            sale_order_ids = self.env['account.move'].sudo().search([('id', 'in', move_id)], order='invoice_date asc')
            credit_note_ids = self.env['account.move'].sudo().search([('reversed_entry_id', 'in', move_id)])
        elif not partner_id and is_pasien == False:
            self._cr.execute("""(
                            select a.id 
                            from account_move a
                                left join sale_order b on b.name = a.invoice_origin 
                            where a.state in ('draft', 'approval','posted') 
                                and date(a.invoice_date) >= '{_start_date}'
                                and date(a.invoice_date) <= '{_end_date}'
                                and a.move_type = 'out_invoice' 
                                and a.source_document is not Null
                                and b.is_pasien is not True
                                order by date(a.invoice_date) asc
                        )""".format(_start_date=str(start_date), _end_date=str(end_date)))
            move_id = self._cr.fetchall()
            sale_order_ids = self.env['account.move'].sudo().search([('id', 'in', move_id)], order='invoice_date asc')
            credit_note_ids = self.env['account.move'].sudo().search([('reversed_entry_id', 'in', move_id)])
        for order in sale_order_ids:
            if order.partner_id.id not in list_partner:
                list_partner.append(order.partner_id.id)
                data_all[order.partner_id.id] = {
                    'code': order.partner_id.code_customer, 
                    'name': order.partner_id.name,
                    'is_pasien': order.is_pasien,
                    'pasien': order.pasien.name,
                    'penjualan': 0.0, 
                    'pajak': 0.0, 
                    'total': 0.0, 
                    'debit': 0.0, 
                    'retur': 0.0, 
                    'retur_pajak': 0.0, 
                    'refund': 0.0
                }
            if order.total_all_tax >= 0:
                total_all_tax = order.total_all_tax
            elif order.total_all_tax < 0:
                total_all_tax = order.total_all_tax
            data_all[order.partner_id.id]['penjualan'] += (order.amount_untaxed - order.global_order_discount)
            data_all[order.partner_id.id]['pajak'] += total_all_tax
            data_all[order.partner_id.id]['debit'] += ((order.amount_untaxed - order.global_order_discount)+total_all_tax)
        # credit_note_ids = self.env['account.move'].sudo().search([('id', 'in', move_id)])
        for cn in credit_note_ids:
            if cn.partner_id.id not in list_partner:
                list_partner.append(cn.partner_id.id)
                data_all[cn.partner_id.id] = {
                    'code': cn.partner_id.code_customer,
                    'name': cn.partner_id.name,
                    'is_pasien': order.is_pasien,
                    'pasien': order.pasien.name,
                    'penjualan': 0.0,
                    'pajak': 0.0,
                    'total': 0.0,
                    'debit': 0.0,
                    'retur': 0.0,
                    'retur_pajak': 0.0,
                    'refund': 0.0
                }
            data_all[cn.partner_id.id]['retur'] += cn.amount_untaxed
            data_all[cn.partner_id.id]['retur_pajak'] += cn.total_all_tax
            data_all[cn.partner_id.id]['refund'] += (cn.amount_untaxed + cn.total_all_tax)

        # credit_note_ids = self.env['account.move'].sudo().search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'), ('invoice_date', '>=', start_date), ('invoice_date', '<=', end_date)])
        # if partner_id and is_pasien == True:
        #     # credit_note_ids = self.env['account.move'].sudo().search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'), ('invoice_date', '>=', start_date), ('invoice_date', '<=', end_date), ('partner_id', '=', partner_id)])
        #     self._cr.execute("""(
        #            select a.id
        #            from account_move a
        #                join sale_order b on b.name = a.invoice_origin
        #            where a.state in ('draft', 'posted')
        #                and date(a.invoice_date) >= '{_start_date}'
        #                and date(a.invoice_date) <= '{_end_date}'
        #                and a.move_type = 'out_refund'
        #                and b.is_pasien = True
        #                and a.partner_id = {_partner_id}
        #        )""".format(_start_date=str(start_date), _end_date=str(end_date), _partner_id=partner_id))
        #     move_id = self._cr.fetchall()
        #     credit_note_ids = self.env['account.move'].sudo().search([('id', 'in', move_id)])
        # elif partner_id and is_pasien == False:
        #     self._cr.execute("""(
        #           select a.id
        #           from account_move a
        #               join sale_order b on b.name = a.invoice_origin
        #           where a.state in ('draft', 'posted')
        #               and date(a.invoice_date) >= '{_start_date}'
        #               and date(a.invoice_date) <= '{_end_date}'
        #               and a.move_type = 'out_refund'
        #               and b.is_pasien = False
        #               and a.partner_id = {_partner_id}
        #       )""".format(_start_date=str(start_date), _end_date=str(end_date), _partner_id=partner_id))
        #     move_id = self._cr.fetchall()
        #     credit_note_ids = self.env['account.move'].sudo().search([('id', 'in', move_id)])
        # elif not partner_id and is_pasien == False:
        #     self._cr.execute("""(
        #           select a.id
        #           from account_move a
        #               join sale_order b on b.name = a.invoice_origin
        #           where a.state in ('draft', 'posted')
        #               and date(a.invoice_date) >= '{_start_date}'
        #               and date(a.invoice_date) <= '{_end_date}'
        #               and a.move_type = 'out_refund'
        #               and b.is_pasien = False
        #       )""".format(_start_date=str(start_date), _end_date=str(end_date)))
        #     move_id = self._cr.fetchall()
        #     credit_note_ids = self.env['account.move'].sudo().search([('id', 'in', move_id)])
        # elif not partner_id and is_pasien == True:
        #     self._cr.execute("""(
        #           select a.id
        #           from account_move a
        #               join sale_order b on b.name = a.invoice_origin
        #           where a.state in ('draft', 'posted')
        #               and date(a.invoice_date) >= '{_start_date}'
        #               and date(a.invoice_date) <= '{_end_date}'
        #               and a.move_type = 'out_refund'
        #               and b.is_pasien = True
        #       )""".format(_start_date=str(start_date), _end_date=str(end_date)))
        #     move_id = self._cr.fetchall()
        #     credit_note_ids = self.env['account.move'].sudo().search([('id', 'in', move_id)])
        # for cn in credit_note_ids:
        #     if cn.partner_id.id not in list_partner:
        #         list_partner.append(cn.partner_id.id)
        #         data_all[cn.partner_id.id] = {
        #             'code': cn.partner_id.code_customer,
        #             'name': cn.partner_id.name,
        #             'is_pasien': order.is_pasien,
        #             'pasien': order.pasien.name,
        #             'penjualan': 0.0,
        #             'pajak': 0.0,
        #             'total': 0.0,
        #             'debit': 0.0,
        #             'retur': 0.0,
        #             'retur_pajak': 0.0,
        #             'refund': 0.0
        #         }
        #     data_all[cn.partner_id.id]['retur'] += cn.amount_untaxed
        #     data_all[cn.partner_id.id]['retur_pajak'] += cn.amount_tax
        #     data_all[cn.partner_id.id]['refund'] += (cn.amount_untaxed + cn.amount_tax)
        
        row += 1
        row_start = row + 1
        for partner in list_partner:
            sheet.write(row, 0, data_all[partner]['code'] or '', formatDetailTable)
            sheet.write(row, 1, data_all[partner]['name'] or '', formatDetailTable)
            sheet.write(row, 2, data_all[partner]['pasien'] or '-', formatDetailTable)
            sheet.write(row, 3, data_all[partner]['penjualan'], formatDetailCurrencyTable)
            sheet.write(row, 4, data_all[partner]['pajak'], formatDetailCurrencyTable)
            sheet.write(row, 5, data_all[partner]['debit'], formatDetailCurrencyTable)
            sheet.write(row, 6, data_all[partner]['retur'], formatDetailCurrencyTable)
            sheet.write(row, 7, data_all[partner]['retur_pajak'], formatDetailCurrencyTable)
            sheet.write(row, 8, data_all[partner]['refund'], formatDetailCurrencyTable)
            sheet.write(row, 9, data_all[partner]['debit'] - data_all[partner]['refund'], formatDetailCurrencyTable)
            row += 1
        row_end = row
        column_end = row_end + 1
        sheet.merge_range(row, 0, row, 2, 'Total', formatHeaderTable)
        sheet.write_formula(f'D{column_end}', f'=SUM(D{row_start}:D{row_end})', formatHeaderCurrencyTable)
        sheet.write_formula(f'E{column_end}', f'=SUM(E{row_start}:E{row_end})', formatHeaderCurrencyTable)
        sheet.write_formula(f'F{column_end}', f'=SUM(F{row_start}:F{row_end})', formatHeaderCurrencyTable)
        sheet.write_formula(f'G{column_end}', f'=SUM(G{row_start}:G{row_end})', formatHeaderCurrencyTable)
        sheet.write_formula(f'H{column_end}', f'=SUM(H{row_start}:H{row_end})', formatHeaderCurrencyTable)
        sheet.write_formula(f'I{column_end}', f'=SUM(I{row_start}:I{row_end})', formatHeaderCurrencyTable)
        sheet.write_formula(f'J{column_end}', f'=SUM(J{row_start}:J{row_end})', formatHeaderCurrencyTable)
