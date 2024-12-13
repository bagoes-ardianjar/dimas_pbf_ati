from odoo import http
from odoo.http import content_disposition, request
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import io
import xlsxwriter

class pnl_profit_sales_controller(http.Controller):
    @http.route(['/pnl_profit_sales_report/<model("pnl.profit.report.preview"):data>', ], type='http', auth="user",
                csrf=False)
    def get_pnl_profit_sales_report_excel(self, data=None, **args):
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', content_disposition('Rekap Penjualan Profit Sales' + '.xlsx'))
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

            sheet.set_column(0, 0, 20)
            sheet.set_column(1, 1, 20)
            sheet.set_column(2, 2, 20)
            sheet.set_column(3, 3, 20)
            sheet.set_column(4, 4, 20)

            sheet.merge_range('A1:E1', atas.name,header_style)
            sheet.merge_range('A2:E2', 'Periode '+ str(atas.start_date) + ' s.d ' + str(atas.end_date), header_style_bold)
            sheet.merge_range('A3:E3', 'Dalam Rupiah', sub_header_style)


            # isi judul tabel
            sheet.merge_range('A5:A6', 'Sales Person', table_style)
            sheet.merge_range('B5:B6', 'Total Beli', table_style)
            sheet.merge_range('C5:C6', 'Total Jual', table_style)
            sheet.merge_range('D5:D6', 'Profit', table_style)
            sheet.merge_range('E5:E6', 'Persentase', table_style)

            row = 6

            # cari record data yang dipilih
            record_line = request.env['pnl.profit.report.preview.line'].search([('pnl_profit_preview_id','=', atas.id)])
            for line in record_line:
                # content/isi tabel
                sheet.write(row, 0, line.sales_person, detail_table_style)
                sheet.write(row, 1, line.total_beli or 0, currency_detail_table_style)
                sheet.write(row, 2, line.total_jual or 0, currency_detail_table_style)
                sheet.write(row, 3, line.profit or 0, currency_detail_table_style)
                sheet.write(row, 4, line.persentase or 0, detail_table_style)
                row += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
        return response

class pnl_sales_controller(http.Controller):
    @http.route(['/pnl_profit_report/<model("wizard.pnl.profit.sales"):wizard>', ], type='http', auth="user",
                csrf=False)
    def get_pnl_profit_report_excel(self, wizard=None, **args):
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', content_disposition('Rekap Penjualan Profit Sales' + '.xlsx'))
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

            sheet.set_column(0, 0, 20)
            sheet.set_column(1, 1, 20)
            sheet.set_column(2, 2, 20)
            sheet.set_column(3, 3, 20)
            sheet.set_column(4, 4, 20)

            sheet.merge_range('A1:E1', atas.name, header_style)
            sheet.merge_range('A2:E2', 'Periode ' + str(atas.start_date) + ' s.d ' + str(atas.end_date), header_style_bold)
            sheet.merge_range('A3:E3', 'Dalam Rupiah', sub_header_style)

            # isi judul tabel
            sheet.merge_range('A5:A6', 'Sales Person', table_style)
            sheet.merge_range('B5:B6', 'Total Beli', table_style)
            sheet.merge_range('C5:C6', 'Total Jual', table_style)
            sheet.merge_range('D5:D6', 'Profit', table_style)
            sheet.merge_range('E5:E6', 'Persentase', table_style)

            row = 6

            # cari record data yang dipilih
            record_line = request.env['wizard.pnl.profit.sales.line'].search([('wizard_pnl_profit_id', '=', atas.id)])
            for line in record_line:
                # content/isi tabel
                sheet.write(row, 0, line.sales_person, detail_table_style)
                sheet.write(row, 1, line.total_beli or 0, currency_detail_table_style)
                sheet.write(row, 2, line.total_jual or 0, currency_detail_table_style)
                sheet.write(row, 3, line.profit or 0, currency_detail_table_style)
                sheet.write(row, 4, line.persentase or 0, detail_table_style)

                row += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
        return response

