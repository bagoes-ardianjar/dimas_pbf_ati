from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta

header_title = ['ID Produk', 'Nama Produk', 'Nomor Izin Edar', 'Tipe dan Ukuran', 'Nomor Seri', 'Kode Produk', 'Jumlah', 'Tanggal Keluar', 'Tanggal Kadaluarsa', 'ID Partner', 'Nama Partner']

class report_alkes(models.TransientModel):
    _name = 'report.alkes'

    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    golongan_obat = fields.Many2one('jenis.obat', 'Golongan Obat')

    def action_print_report_alkes(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'golongan_obat': self.golongan_obat.id if self.golongan_obat else None
            },
        }
        # data = {'start_date': self.start_date, 'end_date': self.end_date}
        return self.env.ref('ati_report_penjualan.action_report_alkes').report_action(self, data=data)

class so_alkes_xlsx(models.AbstractModel):
    _name = 'report.ati_report_penjualan.so_alkes_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objs):

        # FORMAT TABLE #
        formatHeaderCompany = workbook.add_format({'font_size': 14, 'valign':'vcenter', 'align': 'center', 'bold': True})
        formatSubHeaderCompanyBold = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'center', 'bold': True})
        formatSubHeaderCompany = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'center'})
        formatHeaderTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'bold': True, 'bg_color':'#4ead2f', 'color':'white', 'text_wrap': True, 'border': 1})
        formatHeaderCurrencyTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'bold': True, 'bg_color':'#4ead2f', 'color':'white', 'num_format': '_-"Rp"* #,##0.00_-;-"Rp"* #,##0.00_-;_-"Rp"* "-"_-;_-@_-', 'text_wrap': True, 'border': 1})
        formatDetailTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre','text_wrap': True, 'border': 1})
        formatDetailTable_right = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'right','text_wrap': True, 'border': 1})
        formatDetailTable_left = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'left','text_wrap': True, 'border': 1})
        formatDetailCurrencyTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'num_format': '_-"Rp"* #,##0.00_-;-"Rp"* #,##0.00_-;_-"Rp"* "-"_-;_-@_-', 'text_wrap': True, 'border': 1})

        title = 'Laporan Alkes'
        sheet = workbook.add_worksheet(title)

        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 20)
        sheet.set_column(3, 3, 20)
        sheet.set_column(4, 4, 20)
        sheet.set_column(5, 5, 20)
        sheet.set_column(6, 6, 20)
        sheet.set_column(7, 6, 20)
        sheet.set_column(8, 6, 20)
        sheet.set_column(9, 6, 20)
        sheet.set_column(10, 6, 20)
        sheet.set_column(11, 6, 20)

        start_date = datetime.strptime(data['form']['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['form']['end_date'], '%Y-%m-%d').date()
        periode = start_date.strftime("%d %B %Y") if start_date == end_date else f'{start_date.strftime("%d %B %Y")} - {end_date.strftime("%d %B %Y")}'

        sheet.merge_range(1, 0, 1, 11, 'Laporan Alkes', formatHeaderCompany)
        sheet.merge_range(2, 0, 2, 11, f'Periode {periode}', formatSubHeaderCompanyBold)
        sheet.merge_range(3, 0, 3, 11, '(Dalam Rupiah)', formatSubHeaderCompany)

        row =  5
        column = 0
        for header in header_title:
            sheet.write(row, column, header, formatHeaderTable)
            column += 1

        ## DATA ##
        golongan_obat = data['form']['golongan_obat']

        _where = ""
        if start_date and end_date :
            _where = "where DATE(sp.date_done) between '{_start}' and '{_end}' ".format(_start=start_date, _end=end_date)
        if golongan_obat:
            _where += 'and pt.jenis_obat = {}'.format(golongan_obat)

        _query = """
                SELECT 
                    pt.kode_bpom,
                    pt.name,
                    pt.nie,
                    pt.description,
                    spl.name as batch,
                    sml.qty_done,
                    CAST(date(sp.scheduled_date  + interval '7 hours') AS DATE) as tanggal_keluar,
                    CAST(date(spl.expiration_date + interval '7 hours') AS DATE) as tanggal_kadaluarsa,
                    rp.code_alkes,
                    rp.name as partner
                FROM
                    stock_move_line sml
                    join stock_picking sp on sml.picking_id = sp.id
                    join product_product pp on sml.product_id = pp.id
                    join product_template pt on pp.product_tmpl_id = pt.id
                    join res_partner rp on sp.partner_id = rp.id
                    left join stock_production_lot spl on sml.lot_id = spl.id
                {_where}
                and sp.sale_id is not null
                and sml.state = 'done'
            """.format(_where=_where)
        self._cr.execute(_query)
        res_alkes = self._cr.dictfetchall()
        total_qty = 0
        total_penjualan_all = 0
        row += 1
        row_start = row + 1
        if res_alkes:
            for rec in res_alkes:
                tanggal_kadaluarsa = rec.get('tanggal_kadaluarsa').strftime("%d-%m-%Y") if rec.get('tanggal_kadaluarsa') else ''
                tanggal_keluar = rec.get('tanggal_keluar').strftime("%d-%m-%Y") if rec.get('tanggal_keluar') else ''

                sheet.write(row, 0, rec.get('kode_bpom'), formatDetailTable_left)
                sheet.write(row, 1, rec.get('name'), formatDetailTable_left)
                sheet.write(row, 2, rec.get('nie'), formatDetailTable_left)
                sheet.write(row, 3, rec.get('description'), formatDetailTable_left)
                sheet.write(row, 4, rec.get('batch'), formatDetailTable_right)
                sheet.write(row, 5, rec.get('batch'), formatDetailTable_right)
                sheet.write(row, 6, rec.get('qty_done'), formatDetailTable_right)
                sheet.write(row, 7, tanggal_keluar, formatDetailTable_right)
                sheet.write(row, 8, tanggal_kadaluarsa, formatDetailTable_right)
                sheet.write(row, 9, rec.get('code_alkes'), formatDetailTable_left)
                sheet.write(row, 10, rec.get('partner'), formatDetailTable_left)
                row += 1
                # total_qty += rec.get('product_uom_qty')
                # total_penjualan_all += rec.get('total_penjualan')