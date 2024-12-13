from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta

header_title = ['Nomor Ref', 'Sales Person', 'Invoice Date', 'Due Date','Nomor Faktur', 'Customer', 'Faktur Pajak', 'Total Debit', 'Total Debit (Exc. Tax)']


class report_penjualan_perfakturr(models.TransientModel):
    _name = 'report.penjualan.perfakturr'

    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    partner_id = fields.Many2one('res.partner', 'Customer')

    def action_print_report_penjualan_perfaktur(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'partner_id': self.partner_id.id
            },
        }
        # data = {'start_date': self.start_date, 'end_date': self.end_date}
        return self.env.ref('ati_report_penjualan.action_report_penjualan_perfaktur').report_action(self, data=data)
    def action_print_report_penjualan_perfaktur_xlsx(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'partner_id': self.partner_id.id
            },
        }
        # data = {'start_date': self.start_date, 'end_date': self.end_date}
        return self.env.ref('ati_report_penjualan.action_report_penjualan_perfaktur_xlsx').report_action(self, data=data)

class so_faktur_template(models.AbstractModel):
    _name = 'report.ati_report_penjualan.so_faktur_template'

    def _get_report_values(self, docids, data=None):
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        partner_id = data['form']['partner_id']
        docs = []
        # print("1", data['form'], data['ids'])
        if partner_id != False:
            self._cr.execute(
                """
                    select 
                        DATE(am.invoice_date) as date_order,
                        so.name as reference,
                        hr.name as sales_person,
                        date(am.invoice_date)as inv_date,
                        date(am.invoice_date_due)as due_date,
                        am.name as invoice,
                        rp.name as customer,
                        am.l10n_id_tax_number as faktur_pajak,
                        am.amount_total as total_debit,
                        am.amount_untaxed as total_debit_untaxed,
                        am.total_all_tax as total_all_tax,
                        am.global_order_discount as global_order_discount
                    from
                        sale_order so
                        join sale_order_line sol on sol.order_id = so.id
                        join sale_order_line_invoice_rel rel on rel.order_line_id = sol.id
                        join account_move_line aml on rel.invoice_line_id = aml.id
                        join account_move am on aml.move_id = am.id
                        join res_partner rp on so.partner_id = rp.id
                        join hr_employee hr on hr.id = so.sales_person
                    where
                        DATE(am.invoice_date) between '{}' and '{}' and so.partner_id = {_partner_id}
                        and am.move_type = 'out_invoice'
                        and am.state in ('draft','approval','posted')
                    group by 
                        so.name,
                        hr.name,
                        am.invoice_date_due,
                        am.name,
                        rp.name,
                        am.l10n_id_tax_number,
                        am.amount_total,
                        am.amount_untaxed,
                        am.total_all_tax,
                        am.global_order_discount,
                        am.invoice_date
                    order by
                        am.invoice_date
                """.format(start_date, end_date, _partner_id=data['form']['partner_id']))
            res_penjualan_faktur = self._cr.dictfetchall()
            data = {}
            penjualan_faktur_list = []
            total_debit_all = 0
            total_debit_untaxed_all = 0
            if res_penjualan_faktur:
                for rec in res_penjualan_faktur:
                    faktur_pajak = str(rec.get('faktur_pajak'))
                    if len(faktur_pajak) > 13:
                        index = len(faktur_pajak) - 13
                    else:
                        index = 0
                    new_faktur_pajak = faktur_pajak[index:]
                    penjualan_faktur_list.append({
                        'date_order': rec.get('date_order'),
                        'reference': rec.get('reference'),
                        'sales_person': rec.get('sales_person'),
                        'inv_date': rec.get('inv_date'),
                        'due_date': rec.get('due_date'),
                        'invoice': rec.get('invoice'),
                        'customer': rec.get('customer'),
                        'faktur_pajak': new_faktur_pajak,
                        'total_debit': rec.get('total_debit_untaxed') - rec.get('global_order_discount') + rec.get('total_all_tax'),
                        'total_debit_untaxed': rec.get('total_debit_untaxed') - rec.get('global_order_discount'),
                        'global_order_discount': rec.get('global_order_discount')
                    })
                    total_debit_all += rec.get('total_debit_untaxed') - rec.get('global_order_discount') + rec.get('total_all_tax')
                    total_debit_untaxed_all += (rec.get('total_debit_untaxed') - rec.get('global_order_discount'))

            if penjualan_faktur_list:
                docs = penjualan_faktur_list

            result = {
                # 'doc_ids': data['ids'],
                # 'doc_model': data['model'],
                'start_date': start_date,
                'end_date': end_date,
                'partner_id': partner_id,
                'docs': docs,
                'total_debit_all': total_debit_all,
                'total_debit_untaxed_all': total_debit_untaxed_all
            }
            return result
        else:
            self._cr.execute(
                """
                    select 
                        DATE(am.invoice_date) as date_order,
                        so.name as reference,
                        hr.name as sales_person,
                        date(am.invoice_date)as inv_date,
                        date(am.invoice_date_due)as due_date,
                        am.name as invoice,
                        rp.name as customer,
                        am.l10n_id_tax_number as faktur_pajak,
                        am.amount_total as total_debit,
                        am.amount_untaxed as total_debit_untaxed,
                        am.total_all_tax as total_all_tax,
                        am.global_order_discount as global_order_discount
                    from
                        sale_order so
                        join sale_order_line sol on sol.order_id = so.id
                        join sale_order_line_invoice_rel rel on rel.order_line_id = sol.id
                        join account_move_line aml on rel.invoice_line_id = aml.id
                        join account_move am on aml.move_id = am.id
                        join res_partner rp on so.partner_id = rp.id
                        join hr_employee hr on hr.id = so.sales_person
                    where
                        DATE(am.invoice_date) between '{}' and '{}' 
                        and am.move_type = 'out_invoice'
                        and am.state in ('draft','approval','posted')
                    group by 
                        so.name,
                        hr.name,
                        am.invoice_date_due,
                        am.name,
                        rp.name,
                        am.l10n_id_tax_number,
                        am.amount_total,
                        am.amount_untaxed,
                        am.total_all_tax,
                        am.global_order_discount,
                        am.invoice_date
                    order by
                        am.invoice_date
                """.format(start_date, end_date))
            res_penjualan_faktur = self._cr.dictfetchall()
            data = {}
            penjualan_faktur_list = []
            total_debit_all = 0
            total_debit_untaxed_all = 0
            if res_penjualan_faktur:
                for rec in res_penjualan_faktur:
                    faktur_pajak = str(rec.get('faktur_pajak'))
                    if len(faktur_pajak) > 13:
                        index = len(faktur_pajak) - 13
                    else:
                        index = 0
                    new_faktur_pajak = faktur_pajak[index:]
                    penjualan_faktur_list.append({
                        'date_order': rec.get('date_order'),
                        'reference': rec.get('reference'),
                        'sales_person': rec.get('sales_person'),
                        'inv_date': rec.get('inv_date'),
                        'due_date': rec.get('due_date'),
                        'invoice': rec.get('invoice'),
                        'customer': rec.get('customer'),
                        'faktur_pajak': new_faktur_pajak,
                        'total_debit': rec.get('total_debit_untaxed') - rec.get('global_order_discount') + rec.get('total_all_tax'),
                        'total_debit_untaxed': rec.get('total_debit_untaxed') - rec.get('global_order_discount'),
                        'global_order_discount': rec.get('global_order_discount')
                    })
                    total_debit_all += rec.get('total_debit_untaxed') - rec.get('global_order_discount') + rec.get('total_all_tax')
                    total_debit_untaxed_all += (rec.get('total_debit_untaxed') - rec.get('global_order_discount'))

            if penjualan_faktur_list:
                docs = penjualan_faktur_list


            result = {
                # 'doc_ids': data['ids'],
                # 'doc_model': data['model'],
                'start_date': start_date,
                'end_date': end_date,
                'docs': docs,
                'total_debit_all': total_debit_all,
                'total_debit_untaxed_all': total_debit_untaxed_all
            }
            return result

class so_faktur_template_xlsx(models.AbstractModel):
    _name = 'report.ati_report_penjualan.so_faktur_template_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objs):
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        partner_id = data['form']['partner_id']
        docs = []

        # FORMAT TABLE #
        formatHeaderCompany = workbook.add_format({'font_size': 14, 'valign':'vcenter', 'align': 'center', 'bold': True})
        formatSubHeaderCompanyBold = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'center', 'bold': True})
        formatSubHeaderCompany = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'center'})
        formatHeaderTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'bold': True, 'bg_color':'#4ead2f', 'color':'white', 'text_wrap': True, 'border': 1})
        formatHeaderCurrencyTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'bold': True, 'bg_color':'#4ead2f', 'color':'white', 'num_format': '_-"Rp"* #,##0.00_-;-"Rp"* #,##0.00_-;_-"Rp"* "-"_-;_-@_-', 'text_wrap': True, 'border': 1})
        formatDetailTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre','text_wrap': True, 'border': 1})
        formatDetailCurrencyTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'num_format': '_-"Rp"* #,##0.00_-;-"Rp"* #,##0.00_-;_-"Rp"* "-"_-;_-@_-', 'text_wrap': True, 'border': 1})

        title = 'Laporan Rekap Penjualan Per Faktur'
        sheet = workbook.add_worksheet(title)

        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 20)
        sheet.set_column(3, 3, 20)
        sheet.set_column(4, 4, 20)
        sheet.set_column(5, 5, 20)

        start_date = datetime.strptime(data['form']['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['form']['end_date'], '%Y-%m-%d').date()
        periode = start_date.strftime("%d %B %Y") if start_date == end_date else f'{start_date.strftime("%d %B %Y")} - {end_date.strftime("%d %B %Y")}'

        sheet.merge_range(1, 0, 1, 4, 'Laporan Rekap Penjualan Per Faktur', formatHeaderCompany)
        sheet.merge_range(2, 0, 2, 4, f'Periode {periode}', formatSubHeaderCompanyBold)
        sheet.merge_range(3, 0, 3, 4, '(Dalam Rupiah)', formatSubHeaderCompany)

        row =  5
        column = 0
        for header in header_title:
            sheet.write(row, column, header, formatHeaderTable)
            column += 1

        #### DATA REPORT ####
        if partner_id != False:
            self._cr.execute(
                """
                    select 
                        DATE(am.invoice_date) as date_order,
                        so.name as reference,
                        hr.name as sales_person,
                        date(am.invoice_date)as inv_date,
                        date(am.invoice_date_due)as due_date,
                        am.name as invoice,
                        rp.name as customer,
                        am.l10n_id_tax_number as faktur_pajak,
                        am.amount_total as total_debit,
                        am.amount_untaxed as total_debit_untaxed,
                        am.total_all_tax as total_all_tax,
                        am.global_order_discount as global_order_discount
                    from
                        sale_order so
                        join sale_order_line sol on sol.order_id = so.id
                        join sale_order_line_invoice_rel rel on rel.order_line_id = sol.id
                        join account_move_line aml on rel.invoice_line_id = aml.id
                        join account_move am on aml.move_id = am.id
                        join res_partner rp on so.partner_id = rp.id
                        join hr_employee hr on hr.id = so.sales_person
                    where
                        DATE(am.invoice_date) between '{}' and '{}' and so.partner_id = {_partner_id}
                        and am.move_type = 'out_invoice'
                        and am.state in ('draft','approval','posted')
                    group by 
                        so.name,
                        am.name,
                        hr.name,
                        am.invoice_date_due,
                        rp.name,
                        am.l10n_id_tax_number,
                        am.amount_total,
                        am.amount_untaxed,
                        am.total_all_tax,
                        am.global_order_discount,
                        am.invoice_date
                    order by
                        am.invoice_date
                """.format(start_date, end_date,_partner_id=data['form']['partner_id']))
        else :
            self._cr.execute(
                """
                    select 
                        DATE(am.invoice_date) as date_order,
                        so.name as reference,
                        hr.name as sales_person,
                        date(am.invoice_date)as inv_date,
                        date(am.invoice_date_due)as due_date,
                        am.name as invoice,
                        rp.name as customer,
                        am.l10n_id_tax_number as faktur_pajak,
                        am.amount_total as total_debit,
                        am.total_all_tax as total_all_tax,
                        am.amount_untaxed as total_debit_untaxed,
                        am.global_order_discount as global_order_discount
                    from
                        sale_order so
                        join sale_order_line sol on sol.order_id = so.id
                        join sale_order_line_invoice_rel rel on rel.order_line_id = sol.id
                        join account_move_line aml on rel.invoice_line_id = aml.id
                        join account_move am on aml.move_id = am.id
                        join res_partner rp on so.partner_id = rp.id
                        join hr_employee hr on hr.id = so.sales_person
                    where
                        DATE(am.invoice_date) between '{}' and '{}' 
                        and am.move_type = 'out_invoice'
                        and am.state in ('draft','approval','posted')
                    group by 
                        so.name,
                        hr.name,
                        am.invoice_date_due,
                        am.name,
                        rp.name,
                        am.l10n_id_tax_number,
                        am.amount_total,
                        am.amount_untaxed,
                        am.total_all_tax,
                        am.global_order_discount,
                        am.invoice_date
                    order by
                        am.invoice_date
                """.format(start_date, end_date))
        res_penjualan_faktur = self._cr.dictfetchall()
        data = {}
        pembelian_faktur_list = []
        total_debit_all = 0
        total_debit_untaxed_all = 0
        row += 1
        row_start = row + 1
        if res_penjualan_faktur:
            for rec in res_penjualan_faktur:
                faktur_pajak = str(rec.get('faktur_pajak'))
                if len(faktur_pajak) > 13:
                    index = len(faktur_pajak) - 13
                else:
                    index = 0
                new_faktur_pajak = faktur_pajak[index:]
                sheet.write(row, 0, rec.get('reference'), formatDetailTable)
                sheet.write(row, 1, rec.get('sales_person'), formatDetailTable)
                inv_date = rec.get('inv_date').strftime("%Y/%m/%d")
                sheet.write(row, 2, inv_date, formatDetailTable)
                due_date = rec.get('due_date').strftime("%Y/%m/%d")
                sheet.write(row, 3, due_date, formatDetailTable)
                sheet.write(row, 4, rec.get('invoice'), formatDetailTable)
                sheet.write(row, 5, rec.get('customer'), formatDetailTable)
                sheet.write(row, 6, new_faktur_pajak, formatDetailTable)
                sheet.write(row, 7, rec.get('total_debit_untaxed') - rec.get('global_order_discount') + rec.get('total_all_tax'), formatDetailCurrencyTable)
                sheet.write(row, 8, rec.get('total_debit_untaxed') - rec.get('global_order_discount'), formatDetailCurrencyTable)
                row += 1
                total_debit_all += (rec.get('total_debit_untaxed') - rec.get('global_order_discount')) + rec.get('total_all_tax')
                total_debit_untaxed_all += (rec.get('total_debit_untaxed') - rec.get('global_order_discount'))

            row_end = row
            column_end = row_end + 1
            sheet.merge_range(row, 0, row, 6, 'Total', formatHeaderTable)
            sheet.write(row, 7, total_debit_all, formatHeaderCurrencyTable)
            sheet.write(row, 8, total_debit_untaxed_all, formatHeaderCurrencyTable)

