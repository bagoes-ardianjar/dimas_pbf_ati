from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta

header_title = ['Nomor Ref', 'Nomor Faktur', 'Supplier', 'Total Kredit']

class report_pembelian_nonppn(models.TransientModel):
    _name = 'report.pembelian.nonppn'

    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")

    def action_print_report_pembelian_nonppn(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'start_date': self.start_date,
                'end_date': self.end_date
            },
        }
        # data = {'start_date': self.start_date, 'end_date': self.end_date}
        return self.env.ref('ati_report_pembelian.action_report_pembelian_nonppn').report_action(self, data=data)

    def action_print_report_pembelian_nonppn_xlsx(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'report.pembelian.perbarang'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        return self.env.ref('ati_report_pembelian.action_report_pembelian_nonppn_xlsx').report_action(self, data=datas)

class po_nonppn_template(models.AbstractModel):
    _name = 'report.ati_report_pembelian.po_nonppn_template'

    def _get_report_values(self, docids, data=None):
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        docs = []
        # print("1", data['form'], data['ids'])
        self._cr.execute(
            """
                select 
                    DATE(po.date_approve) as date_order,
                    po.name as reference,
                    am.name as invoice,
                    rp.name as supplier,
                    am.amount_total as total_debit,
                    am.amount_untaxed as total_debit_untaxed
                from
                    purchase_order po
                    join purchase_order_line pol on pol.order_id = po.id
                    join account_move_line aml on aml.purchase_line_id = pol.id
                    join account_move am on aml.move_id = am.id
                    join res_partner rp on po.partner_id = rp.id
                where
                    DATE(am.invoice_date) between '{}' and '{}'
                    and am.move_type = 'in_invoice'
                    and rp.l10n_id_pkp != True
                    and am.state in ('draft','approval','posted')
                group by 
                    po.name,
                    am.name,
                    rp.name,
                    am.amount_total,
                    am.amount_untaxed,
                    po.date_approve
                order by
                    po.date_approve
            """.format(start_date, end_date))
        res_pembelian_faktur = self._cr.dictfetchall()
        data = {}
        pembelian_faktur_list = []
        total_debit_all = 0
        total_debit_untaxed_all = 0
        if res_pembelian_faktur:
            for rec in res_pembelian_faktur:
                pembelian_faktur_list.append({
                    'date_order': rec.get('date_order'),
                    'reference': rec.get('reference'),
                    'invoice': rec.get('invoice'),
                    'supplier': rec.get('supplier'),
                    'total_debit': rec.get('total_debit'),
                    'total_debit_untaxed': rec.get('total_debit_untaxed')
                })
                total_debit_all += rec.get('total_debit')
                total_debit_untaxed_all += rec.get('total_debit_untaxed')

        if pembelian_faktur_list:
            docs = pembelian_faktur_list


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

class po_nonppn_template_xlsx(models.AbstractModel):
    _name = 'report.ati_report_pembelian.po_nonppn_template_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objs):

        # FORMAT TABLE #
        formatHeaderCompany = workbook.add_format({'font_size': 14, 'valign':'vcenter', 'align': 'center', 'bold': True})
        formatSubHeaderCompanyBold = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'center', 'bold': True})
        formatSubHeaderCompany = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'center'})
        formatHeaderTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'bold': True, 'bg_color':'#4ead2f', 'color':'white', 'text_wrap': True, 'border': 1})
        formatHeaderCurrencyTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'bold': True, 'bg_color':'#4ead2f', 'color':'white', 'num_format': '_-"Rp"* #,##0.00_-;-"Rp"* #,##0.00_-;_-"Rp"* "-"_-;_-@_-', 'text_wrap': True, 'border': 1})
        formatDetailTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre','text_wrap': True, 'border': 1})
        formatDetailCurrencyTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'num_format': '_-"Rp"* #,##0.00_-;-"Rp"* #,##0.00_-;_-"Rp"* "-"_-;_-@_-', 'text_wrap': True, 'border': 1})

        title = 'Laporan Rekap Pembelian Non PPN'
        sheet = workbook.add_worksheet(title)

        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 20)
        sheet.set_column(3, 3, 20)

        start_date = datetime.strptime(data['form']['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['form']['end_date'], '%Y-%m-%d').date()
        periode = start_date.strftime("%d %B %Y") if start_date == end_date else f'{start_date.strftime("%d %B %Y")} - {end_date.strftime("%d %B %Y")}'

        sheet.merge_range(1, 0, 1, 3, 'Laporan Rekap Pembelian Non PPN', formatHeaderCompany)
        sheet.merge_range(2, 0, 2, 3, f'Periode {periode}', formatSubHeaderCompanyBold)
        sheet.merge_range(3, 0, 3, 3, '(Dalam Rupiah)', formatSubHeaderCompany)

        row = 5
        column = 0
        for header in header_title:
            sheet.write(row, column, header, formatHeaderTable)
            column += 1

        #### DATA REPORT ####
        self._cr.execute(
            """
                select 
                    DATE(po.date_approve) as date_order,
                    po.name as reference,
                    am.name as invoice,
                    rp.name as supplier,
                    am.amount_total as total_debit,
                    am.amount_untaxed as total_debit_untaxed
                from
                    purchase_order po
                    join purchase_order_line pol on pol.order_id = po.id
                    join account_move_line aml on aml.purchase_line_id = pol.id
                    join account_move am on aml.move_id = am.id
                    join res_partner rp on po.partner_id = rp.id
                where
                    DATE(am.invoice_date) between '{}' and '{}'
                    and am.move_type = 'in_invoice'
                    and rp.l10n_id_pkp != True
                    and am.state in ('draft','approval','posted')
                group by 
                    po.name,
                    am.name,
                    rp.name,
                    am.amount_total,
                    am.amount_untaxed,
                    po.date_approve
                order by
                    po.date_approve
            """.format(start_date, end_date))
        res_pembelian_faktur = self._cr.dictfetchall()
        data = {}
        pembelian_faktur_list = []
        total_debit_all = 0
        total_debit_untaxed_all = 0
        row += 1
        row_start = row + 1
        if res_pembelian_faktur:
            for rec in res_pembelian_faktur:
                sheet.write(row, 0, rec.get('reference'), formatDetailTable)
                sheet.write(row, 1, rec.get('invoice'), formatDetailTable)
                sheet.write(row, 2, rec.get('supplier'), formatDetailTable)
                sheet.write(row, 3, rec.get('total_debit'), formatDetailCurrencyTable)
                row += 1
                total_debit_all += rec.get('total_debit')
                total_debit_untaxed_all += rec.get('total_debit_untaxed')

            row_end = row
            column_end = row_end + 1
            sheet.merge_range(row, 0, row, 2, 'Total', formatHeaderTable)
            sheet.write(row, 3, total_debit_all, formatHeaderCurrencyTable)
