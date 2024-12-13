from odoo import http
from odoo.http import content_disposition, request
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import io
import xlsxwriter

class pnl_sale_sales_controller(http.Controller):
    @http.route(['/pnl_sale_sales_report/<model("pnl.sales.report.preview"):data>', ], type='http', auth="user",
                csrf=False)
    def get_pnl_sale_sales_report_excel(self, data=None, **args):
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', content_disposition('Laporan Laba/Rugi Per Sales Produk' + '.xlsx'))
            ]
        )

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        header_style = workbook.add_format(
            {'font_size': 14, 'valign': 'vcenter', 'align': 'center', 'bold': True})
        header_style_bold = workbook.add_format(
            {'font_size': 11, 'valign': 'vcenter', 'align': 'center', 'bold': True})
        sub_header_style = workbook.add_format({'font_size': 11, 'valign': 'vcenter', 'align': 'center'})
        table_style = workbook.add_format(
            {'font_size': 11, 'valign': 'vcenter', 'align': 'centre', 'bold': True, 'bg_color': '#4ead2f',
             'color': 'white', 'text_wrap': True, 'border': 1})
        detail_table_style = workbook.add_format(
            {'font_size': 11, 'valign': 'vcenter', 'align': 'centre', 'text_wrap': True, 'border': 1})
        currency_detail_table_style = workbook.add_format({'font_size': 11, 'valign': 'vcenter', 'align': 'centre',
                                                         'num_format': '_-"Rp"* #,##0.00_-;-"Rp"* #,##0.00_-;_-"Rp"* "-"_-;_-@_-',
                                                         'text_wrap': True, 'border': 1})
        for atas in data:
            sheet = workbook.add_worksheet(atas.name)

            sheet.set_landscape()

            sheet.set_paper(9)

            sheet.set_column(0, 0, 15)
            sheet.set_column(1, 1, 20)
            sheet.set_column(2, 2, 20)
            sheet.set_column(3, 3, 20)
            sheet.set_column(4, 4, 20)
            sheet.set_column(5, 5, 20)
            sheet.set_column(6, 6, 20)
            sheet.set_column(7, 7, 15)
            sheet.set_column(8, 8, 20)
            sheet.set_column(9, 9, 20)
            sheet.set_column(10, 10, 20)
            sheet.set_column(11, 11, 20)
            sheet.set_column(12, 12, 20)
            sheet.set_column(13, 13, 15)

            sheet.merge_range('A1:M1', atas.name,header_style)
            sheet.merge_range('A2:M2', 'Periode '+ str(atas.start_date) + ' s.d ' + str(atas.end_date), header_style_bold)
            sheet.merge_range('A3:M3', 'Dalam Rupiah', sub_header_style)


            # isi judul tabel
            sheet.merge_range('A5:A6', 'Tanggal', table_style)
            sheet.merge_range('B5:C5', 'No. Faktur', table_style)
            sheet.write(5, 1, 'Penjualan', table_style)
            sheet.write(5, 2, 'Order', table_style)
            sheet.merge_range('D5:D6', 'Pelanggan', table_style)
            sheet.merge_range('E5:E6', 'Sales Person', table_style)
            sheet.merge_range('F5:F6', 'Barang', table_style)
            sheet.merge_range('G5:G6', 'Satuan', table_style)
            sheet.merge_range('H5:H6', 'QTY', table_style)
            sheet.merge_range('I5:I6', 'Harga Beli', table_style)
            sheet.merge_range('J5:J6', 'Harga Jual', table_style)
            sheet.merge_range('K5:K6', 'Total Beli', table_style)
            sheet.merge_range('L5:L6', 'Total Jual', table_style)
            sheet.merge_range('M5:M6', 'Profit', table_style)
            sheet.merge_range('N5:N6', 'Persentase', table_style)

            row = 6

            # cari record data yang dipilih
            record_line = request.env['pnl.sales.report.preview.line'].search([('pnl_sales_preview_id','=', atas.id)])
            for line in record_line:
                # content/isi tabel
                get_tanggal_awal = datetime.strptime(str(line.tanggal), "%Y-%m-%d")
                get_tanggal = get_tanggal_awal.strftime("%d/%m/%Y")
                sheet.write(row, 0, str(get_tanggal), detail_table_style)
                sheet.write(row, 1, line.no_penjualan, detail_table_style)
                sheet.write(row, 2, '', detail_table_style)
                sheet.write(row, 3, line.pelanggan.name, detail_table_style)
                sheet.write(row, 4, line.sales_person, detail_table_style)
                sheet.write(row, 5, line.product_id.name, detail_table_style)
                sheet.write(row, 6, line.uom_id.name, detail_table_style)
                sheet.write(row, 7, line.qty or 0, detail_table_style)
                sheet.write(row, 8, line.harga_beli or 0, currency_detail_table_style)
                sheet.write(row, 9, line.harga_jual or 0, currency_detail_table_style)
                sheet.write(row, 10, line.total_beli or 0, currency_detail_table_style)
                sheet.write(row, 11, line.total_jual or 0, currency_detail_table_style)
                sheet.write(row, 12, line.profit or 0, currency_detail_table_style)
                sheet.write(row, 13, line.persentase or 0, detail_table_style)

                row += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
        return response

class pnl_sales_controller(http.Controller):
    @http.route(['/pnl_sales_report/<model("wizard.pnl.sale.sales"):wizard>', ], type='http', auth="user",
                csrf=False)
    def get_pnl_sales_report_excel(self, wizard=None, **args):
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', content_disposition('Laporan Laba/Rugi Per Sales Produk' + '.xlsx'))
            ]
        )

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        header_style = workbook.add_format(
            {'font_size': 14, 'valign': 'vcenter', 'align': 'center', 'bold': True})
        header_style_bold = workbook.add_format(
            {'font_size': 11, 'valign': 'vcenter', 'align': 'center', 'bold': True})
        sub_header_style = workbook.add_format({'font_size': 11, 'valign': 'vcenter', 'align': 'center'})
        table_style = workbook.add_format(
            {'font_size': 11, 'valign': 'vcenter', 'align': 'centre', 'bold': True, 'bg_color': '#4ead2f',
             'color': 'white', 'text_wrap': True, 'border': 1})
        detail_table_style = workbook.add_format(
            {'font_size': 11, 'valign': 'vcenter', 'align': 'centre', 'text_wrap': True, 'border': 1})
        currency_detail_table_style = workbook.add_format({'font_size': 11, 'valign': 'vcenter', 'align': 'centre',
                                                           'num_format': '_-"Rp"* #,##0.00_-;-"Rp"* #,##0.00_-;_-"Rp"* "-"_-;_-@_-',
                                                           'text_wrap': True, 'border': 1})
        for atas in wizard:
            sheet = workbook.add_worksheet(atas.name)

            sheet.set_landscape()

            sheet.set_paper(9)

            sheet.set_column(0, 0, 15)
            sheet.set_column(1, 1, 20)
            sheet.set_column(2, 2, 20)
            sheet.set_column(3, 3, 20)
            sheet.set_column(4, 4, 20)
            sheet.set_column(5, 5, 20)
            sheet.set_column(6, 6, 20)
            sheet.set_column(7, 7, 15)
            sheet.set_column(8, 8, 20)
            sheet.set_column(9, 9, 20)
            sheet.set_column(10, 10, 20)
            sheet.set_column(11, 11, 20)
            sheet.set_column(12, 12, 20)
            sheet.set_column(13, 13, 15)

            sheet.merge_range('A1:M1', atas.name, header_style)
            sheet.merge_range('A2:M2', 'Periode ' + str(atas.start_date) + ' s.d ' + str(atas.end_date), header_style_bold)
            sheet.merge_range('A3:M3', 'Dalam Rupiah', sub_header_style)

            # isi judul tabel
            sheet.merge_range('A5:A6', 'Tanggal', table_style)
            sheet.merge_range('B5:C5', 'No. Faktur', table_style)
            sheet.write(5, 1, 'Penjualan', table_style)
            sheet.write(5, 2, 'Order', table_style)
            sheet.merge_range('D5:D6', 'Pelanggan', table_style)
            sheet.merge_range('E5:E6', 'Sales Person', table_style)
            sheet.merge_range('F5:F6', 'Barang', table_style)
            sheet.merge_range('G5:G6', 'Satuan', table_style)
            sheet.merge_range('H5:H6', 'QTY', table_style)
            sheet.merge_range('I5:I6', 'Harga Beli', table_style)
            sheet.merge_range('J5:J6', 'Harga Jual', table_style)
            sheet.merge_range('K5:K6', 'Total Beli', table_style)
            sheet.merge_range('L5:L6', 'Total Jual', table_style)
            sheet.merge_range('M5:M6', 'Profit', table_style)
            sheet.merge_range('N5:N6', 'Persentase', table_style)

            row = 6

            # cari record data yang dipilih
            record_line = request.env['wizard.pnl.sale.sales.line'].search([('wizard_pnl_sales_id', '=', atas.id)])
            for line in record_line:
                # content/isi tabel
                get_tanggal_awal = datetime.strptime(str(line.tanggal), "%Y-%m-%d")
                get_tanggal = get_tanggal_awal.strftime("%d/%m/%Y")
                sheet.write(row, 0, str(get_tanggal), detail_table_style)
                sheet.write(row, 1, line.no_penjualan, detail_table_style)
                sheet.write(row, 2, '', detail_table_style)
                sheet.write(row, 3, line.pelanggan.name, detail_table_style)
                sheet.write(row, 4, line.sales_person, detail_table_style)
                sheet.write(row, 5, line.product_id.name, detail_table_style)
                sheet.write(row, 6, line.uom_id.name, detail_table_style)
                sheet.write(row, 7, line.qty, detail_table_style)
                sheet.write(row, 8, line.harga_beli, currency_detail_table_style)
                sheet.write(row, 9, line.harga_jual, currency_detail_table_style)
                sheet.write(row, 10, line.total_beli, currency_detail_table_style)
                sheet.write(row, 11, line.total_jual, currency_detail_table_style)
                sheet.write(row, 12, line.profit, currency_detail_table_style)
                sheet.write(row, 13, line.persentase, detail_table_style)

                row += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
        return response

