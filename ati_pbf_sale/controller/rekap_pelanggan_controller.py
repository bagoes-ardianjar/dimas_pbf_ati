from odoo import http
from odoo.http import content_disposition, request
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import io
import xlsxwriter

class pnl_sales_controller(http.Controller):
    @http.route(['/rekap_pelanggan_report/<model("wizard.rekap.pelanggan"):wizard>', ], type='http', auth="user",
                csrf=False)
    def get_rekap_pelanggan_report_excel(self, wizard=None, **args):
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', content_disposition('Laporan Rekap Penjualan Per Pelanggan' + '.xlsx'))
            ]
        )

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        header_style = workbook.add_format(
            {'font_size': 14, 'valign': 'vcenter', 'align': 'center', 'bold': True})
        header_style_left = workbook.add_format(
            {'font_size': 14, 'valign': 'vcenter', 'align': 'left', 'bold': True})
        header_style_bold_left = workbook.add_format(
            {'font_size': 11, 'valign': 'vcenter', 'align': 'left', 'bottom': 1})
        header_style_bold = workbook.add_format(
            {'font_size': 11, 'valign': 'vcenter', 'align': 'center', 'bold': True})
        sub_header_style = workbook.add_format({'font_size': 11, 'valign': 'vcenter', 'align': 'center'})
        table_style = workbook.add_format(
            {'font_size': 11, 'valign': 'vcenter', 'align': 'centre', 'bold': True, 'bg_color': '#4ead2f',
             'color': 'white', 'text_wrap': True, 'border': 1})
        detail_table_style = workbook.add_format(
            {'font_size': 11, 'valign': 'vcenter', 'align': 'centre', 'text_wrap': True, 'border': 1})
        table_left_style = workbook.add_format(
            {'font_size': 11, 'valign': 'vcenter', 'align': 'left', 'bold': True, 'text_wrap': True, 'border': 1})
        detail_table_left_style = workbook.add_format(
            {'font_size': 11, 'valign': 'vcenter', 'align': 'left', 'text_wrap': True, 'border': 1})
        currency_detail_table_style = workbook.add_format({'font_size': 11, 'valign': 'vcenter', 'align': 'centre',
                                                           'num_format': '_-"Rp"* #,##0.00_-;-"Rp"* #,##0.00_-;_-"Rp"* "-"_-;_-@_-',
                                                           'text_wrap': True, 'border': 1})
        currency_detail_table_bold_style = workbook.add_format({'font_size': 11, 'valign': 'vcenter', 'align': 'centre', 'bold': True,
                                                           'num_format': '_-"Rp"* #,##0.00_-;-"Rp"* #,##0.00_-;_-"Rp"* "-"_-;_-@_-',
                                                           'text_wrap': True, 'border': 1})

        for atas in wizard:
            sheet = workbook.add_worksheet(atas.name)

            sheet.set_landscape()

            sheet.set_paper(9)

            sheet.set_column(0, 0, 20)
            sheet.set_column(1, 1, 30)
            sheet.set_column(2, 2, 20)
            sheet.set_column(3, 3, 15)

            sheet.merge_range('A1:D1', 'PBF Berkat Mahkota Putra', header_style_left)
            sheet.merge_range('A2:D2', 'Taman Tekno Blok K2 No 19 dan 20 Bsd, Serpong, Tangerang Selatan, 081322811117, 021-22225555', header_style_bold_left)
            sheet.merge_range('A3:D3', '', header_style)
            sheet.merge_range('A4:D4', atas.name, header_style)
            sheet.merge_range('A5:D5', 'Periode ' + str(atas.start_date) + ' s.d ' + str(atas.end_date), header_style_bold)
            sheet.merge_range('A6:D6', 'Dalam Rupiah', sub_header_style)
            sheet.merge_range('A7:D7', '', header_style)

            record_line = request.env['wizard.rekap.pelanggan.line'].search([('wizard_rekap_pelanggan_id', '=', atas.id)])
            row = 7
            row_start_1 = row + 1
            for line in record_line :
                if line.category_name != False:
                    sheet.write(row, 1, 'Omset ' + str(line.category_name) or '', table_left_style)
                    sheet.write(row, 2, line.total_penjualan_category or 0, currency_detail_table_style)
                    row += 1
                if line.customer_panel_name != False:
                    sheet.write(row, 1, 'Omset Panel ' + str(line.customer_panel_name) or '', table_left_style)
                    sheet.write(row, 2, line.total_penjualan_panel or 0, currency_detail_table_style)
                    row += 1
            row_end_1 = row
            column_end_1 = row_end_1 + 1
            sheet.write(row, 1, 'Total', table_style)
            sheet.write_formula(f'C{column_end_1}', f'=SUM(C{row_start_1}:C{row_end_1})', currency_detail_table_bold_style)
            row = row + 2
            # isi judul tabel
            sheet.write(row, 0, 'Kode Pelanggan', table_style)
            sheet.write(row, 1, 'Nama Pelanggan', table_style)
            sheet.write(row, 2, 'Total Penjualan', table_style)
            row += 1
            row_start = row + 1
            # cari record data yang dipilih
            record_line = request.env['wizard.rekap.pelanggan.line'].search([('wizard_rekap_pelanggan_id', '=', atas.id)])
            for line in record_line:
                if line.code_customer != False:
                # content/isi tabel
                    sheet.write(row, 0, line.code_customer, detail_table_style)
                    sheet.write(row, 1, line.customer_name or 0, detail_table_left_style)
                    sheet.write(row, 2, line.total_penjualan or 0, currency_detail_table_style)

                    row += 1
            row_end = row
            column_end = row_end + 1
            sheet.merge_range(row, 0, row, 1, 'Total', table_style)
            sheet.write_formula(f'C{column_end}', f'=SUM(C{row_start}:C{row_end})', currency_detail_table_bold_style)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
        return response

