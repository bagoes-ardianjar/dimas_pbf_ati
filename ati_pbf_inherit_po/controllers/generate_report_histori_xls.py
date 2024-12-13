from datetime import date
from odoo import http
from odoo.http import content_disposition, request
import io
import xlsxwriter


class PurchasePerubahanHargaExcelReportController(http.Controller):
    @http.route([
        '/purchase/history_excel_report/<model("x.wizard.history.harga.xml"):wizard>',
    ], type='http', auth="user", csrf=False)
    def get_excel_report(self, wizard=None, **args):
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', content_disposition('Laporan History Perubahan Harga' + '.xlsx'))
            ]
        )

        # buat object workbook dari library xlsxwriter
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        # buat style untuk mengatur jenis font, ukuran font, border dan alligment
        title_style = workbook.add_format({'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'font_size': 11, 'valign':'vcenter', 'align': 'center','bg_color':'#D3D3D3', 'color': 'black', 'bold': True})
        header_style = workbook.add_format({'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'font_size': 11, 'valign':'vcenter', 'align': 'center','bg_color':'#D3D3D3', 'color': 'black', 'bold': True})
        # code by adelia
        text_style = workbook.add_format(
            {'font_name': 'Times', 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'left'})
        number_style = workbook.add_format(
            {'font_name': 'Times', 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'right'})

        # loop so sesuai tannggal yang dipilih
        history_obj = request.env['price.changes.line'].search(
            [('tanggal', '>=', wizard.start_date),
                ('tanggal', '<=', wizard.end_date)],order='po_id desc')

        sheet = workbook.add_worksheet('History Perubahan Harga')
        # set orientation jadi landscape
        sheet.set_landscape()
        # set ukuran kertas, 9 artinya kertas A4
        sheet.set_paper(9)
        # set margin kertas dalam satuan inchi
        sheet.set_margins(0.5, 0.5, 0.5, 0.5)

        # set lebar kolom
        sheet.set_column('A:A', 5)
        sheet.set_column('B:F', 20)

        # judul report
        # merge cell A1 sampai E1 dengan ukuran font 14 dan bold
        sheet.merge_range('A1:F1', 'Laporan Perubahan Harga', title_style)

        # judul tabel
        sheet.write(1, 0, 'NO.', header_style)
        sheet.write(1, 1, 'PO Number', header_style)
        sheet.write(1, 2, 'Date', header_style)
        sheet.write(1, 3, 'Product', header_style)
        sheet.write(1, 4, 'Old Price', header_style)
        sheet.write(1, 5, 'New Price', header_style)

        row = 2
        number = 1
        if history_obj:
            for v in history_obj:
                sheet.write(row, 0, number or '-', text_style)
                sheet.write(row, 1, v.po_id.name, text_style)
                tanggal = v.tanggal.strftime('%Y-%m-%d') if v.tanggal else '-'
                sheet.write(row, 2, tanggal, text_style)
                sheet.write(row, 3, v.product_id.name, text_style)
                sheet.write(row, 4, v.old_price, text_style)
                sheet.write(row, 5, v.new_price, text_style)

                row += 1
                number += 1

        else:
            pass

        # masukkan file excel yang sudah digenerate ke response dan return
        # sehingga browser bisa menerima response dan mendownload file yang sudah digenerate
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

        return response