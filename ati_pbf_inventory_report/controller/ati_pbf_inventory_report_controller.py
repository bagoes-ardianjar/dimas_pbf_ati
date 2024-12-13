from odoo import http
from odoo.http import content_disposition, request
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import io
import xlsxwriter

class ati_pbf_inventory_report_controller(http.Controller):
    @http.route(['/pbf_inventory_report/<model("ati.pbf.inventory.report"):wizard>', ], type='http', auth="user",
                csrf=False)
    def get_inventory_report(self, wizard=None, **args):
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', content_disposition('Laporan Triwulan E-Report Kemenkes' + '.xlsx'))
            ]
        )

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        header_style = workbook.add_format(
            {'font_size': 14, 'valign': 'vcenter', 'align': 'center', 'bold': True})
        header_style_bold = workbook.add_format(
            {'font_size': 11, 'valign': 'vcenter', 'align': 'center', 'bold': True})
        table_style = workbook.add_format(
            {'font_size': 11, 'valign': 'vcenter', 'align': 'centre', 'bold': True, 'bg_color': '#4ead2f',
             'color': 'white', 'text_wrap': True, 'border': 1})
        detail_table_style = workbook.add_format(
            {'font_size': 11, 'valign': 'vcenter', 'align': 'centre', 'text_wrap': True, 'border': 1})

        for atas in wizard:
            sheet = workbook.add_worksheet(atas.name)

            sheet.set_landscape()

            sheet.set_paper(9)

            sheet.set_column(0, 0, 15)
            sheet.set_column(1, 1, 20)
            sheet.set_column(2, 2, 20)
            sheet.set_column(3, 3, 15)
            sheet.set_column(4, 4, 15)
            sheet.set_column(5, 5, 15)
            sheet.set_column(6, 6, 15)
            sheet.set_column(7, 7, 15)
            sheet.set_column(8, 8, 15)
            sheet.set_column(9, 9, 15)
            sheet.set_column(10, 10, 15)
            sheet.set_column(11, 11, 15)
            sheet.set_column(12, 12, 15)
            sheet.set_column(13, 13, 15)
            sheet.set_column(14, 14, 15)
            sheet.set_column(15, 15, 15)
            sheet.set_column(16, 16, 15)
            sheet.set_column(17, 17, 15)
            sheet.set_column(18, 18, 15)
            sheet.set_column(19, 19, 15)
            sheet.set_column(20, 20, 15)

            sheet.merge_range('A1:M1', atas.name,header_style)
            sheet.merge_range('A2:M2', 'Periode '+ str(atas.start_date) + ' s.d ' + str(atas.end_date), header_style_bold)


            # isi judul tabel
            sheet.merge_range('A4:A5', 'Kode Obat (NIE)', table_style)
            sheet.write(5, 0, '1', table_style)
            sheet.merge_range('B4:B5', 'Nama Obat', table_style)
            sheet.write(5, 1, '2', table_style)
            sheet.merge_range('C4:C5', 'Kemasan', table_style)
            sheet.write(5, 2, '3', table_style)
            sheet.merge_range('D4:D5', 'Stock Awal', table_style)
            sheet.write(5, 3, '4', table_style)
            sheet.merge_range('E4:K4', 'Jumlah Pemasukan', table_style)
            sheet.write(4, 4, 'Masuk IF', table_style)
            sheet.write(5, 4, '5', table_style)
            sheet.write(4, 5, 'Kode IF', table_style)
            sheet.write(5, 5, '6', table_style)
            sheet.write(4, 6, 'Masuk PBF', table_style)
            sheet.write(5, 6, '7', table_style)
            sheet.write(4, 7, 'Kode PBF', table_style)
            sheet.write(5, 7, '8', table_style)
            sheet.write(4, 8, 'Masuk Lainnya', table_style)
            sheet.write(5, 8, '9', table_style)
            sheet.write(4, 9, 'Masuk Adjustment', table_style)
            sheet.write(5, 9, '10', table_style)
            sheet.write(4, 10, 'Retur', table_style)
            sheet.write(5, 10, '11', table_style)
            sheet.merge_range('L4:U4', 'Jumlah Pengeluaran', table_style)
            sheet.write(4, 11, 'PBF', table_style)
            sheet.write(5, 11, '12', table_style)
            sheet.write(4, 12, 'Kode PBF', table_style)
            sheet.write(5, 12, '13', table_style)
            sheet.write(4, 13, 'RS', table_style)
            sheet.write(5, 13, '14', table_style)
            sheet.write(4, 14, 'Apotek', table_style)
            sheet.write(5, 14, '15', table_style)
            sheet.write(4, 15, 'Sarana Pemerintah', table_style)
            sheet.write(5, 15, '16', table_style)
            sheet.write(4, 16, 'Puskesmas', table_style)
            sheet.write(5, 16, '17', table_style)
            sheet.write(4, 17, 'Klinik', table_style)
            sheet.write(5, 17, '18', table_style)
            sheet.write(4, 18, 'Toko Obat', table_style)
            sheet.write(5, 18, '19', table_style)
            sheet.write(4, 19, 'Retur', table_style)
            sheet.write(5, 19, '20', table_style)
            sheet.write(4, 20, 'Lainnya', table_style)
            sheet.write(5, 20, '21', table_style)
            sheet.merge_range('V4:V5', 'HJD', table_style)
            sheet.write(5, 21, '22', table_style)

            row = 6

            # cari record data yang dipilih
            record_line = request.env['ati.pbf.inventory.report.line'].search([('pbf_inventory_report_id','=', atas.id)])
            for line in record_line:
                # content/isi tabel
                sheet.write(row, 0, line.kode_obat, detail_table_style)
                sheet.write(row, 1, line.nama_obat, detail_table_style)
                sheet.write(row, 2, line.kemasan, detail_table_style)
                sheet.write(row, 3, line.stock_awal, detail_table_style)
                sheet.write(row, 4, line.masuk_if, detail_table_style)
                sheet.write(row, 5, line.kode_if, detail_table_style)
                sheet.write(row, 6, line.masuk_pbf, detail_table_style)
                sheet.write(row, 7, line.kode_pbf, detail_table_style)
                sheet.write(row, 8, line.masuk_lainnya, detail_table_style)
                sheet.write(row, 9, line.masuk_adjustment, detail_table_style)
                sheet.write(row, 10, line.return_pemasukan, detail_table_style)
                sheet.write(row, 11, line.pbf, detail_table_style)
                sheet.write(row, 12, line.code_pbf or '', detail_table_style)
                sheet.write(row, 13, line.rs, detail_table_style)
                sheet.write(row, 14, line.apotek, detail_table_style)
                sheet.write(row, 15, line.sarana_pemerintah, detail_table_style)
                sheet.write(row, 16, line.puskesmas, detail_table_style)
                sheet.write(row, 17, line.klinik, detail_table_style)
                sheet.write(row, 18, line.toko_obat, detail_table_style)
                sheet.write(row, 19, line.return_delivery_order, detail_table_style)
                sheet.write(row, 20, line.lain, detail_table_style)
                sheet.write(row, 21, line.hjd, detail_table_style)

                row += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
        return response
