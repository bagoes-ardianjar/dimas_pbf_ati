# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import content_disposition, request
import io
import xlsxwriter

class PurchaseExcelReportController(http.Controller):
    @http.route([
        '/purchase/excel_report/<model("wizard.po"):wizard>',
    ], type='http', auth="user", csrf=False)
    def get_excel_report_bpom(self, wizard=None, **args):


        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', content_disposition('Pemasukan obat BPOM' + '.xlsx'))
            ]
        )

        # buat object workbook dari library xlsxwriter
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        # buat style untuk mengatur jenis font, ukuran font, border dan alligment
        title_style = workbook.add_format({'font_name': 'Times', 'font_size': 14, 'bold': True, 'align': 'center'})
        header_style = workbook.add_format(
            {'font_name': 'Times', 'bold': True, 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'center'})
        text_style = workbook.add_format(
            {'font_name': 'Times', 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'left'})
        number_style = workbook.add_format(
            {'font_name': 'Times', 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'right'})
        format_date = workbook.add_format({'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'num_format': 'd mmm yyyy'})



        sheet = workbook.add_worksheet('Report Pemasukan Obat BPOM')
        # set orientation jadi landscape
        sheet.set_landscape()
        # set ukuran kertas, 9 artinya kertas A4
        sheet.set_paper(9)
        # set margin kertas dalam satuan inchi
        sheet.set_margins(0.5, 0.5, 0.5, 0.5)

        # set lebar kolom
        sheet.set_column('A:A', 5)
        sheet.set_column('B:E', 15)
        sheet.set_column('G:I', 20)


        # judul report
        # merge cell A1 sampai E1 dengan ukuran font 14 dan bold
        sheet.merge_range('A1:O2', 'Report Pemasukan Obat BPOM', title_style)

        sheet.write(3, 0, 'NO.', header_style)
        sheet.write(3, 1, 'Jenis Transaksi', header_style)
        sheet.write(3, 2, 'Tanggal Pemasukan', header_style)
        sheet.write(3, 3, 'Kode obat Jadi', header_style)
        sheet.write(3, 4, 'Jumlah', header_style)
        sheet.write(3, 5, 'Batch', header_style)
        sheet.write(3, 6, 'Tanggal Expired', header_style)
        sheet.write(3, 7, 'Nomer Faktur', header_style)
        sheet.write(3, 8, 'Sumber', header_style)

        purchase = request.env['purchase.order'].sudo().search([('create_date','>=', wizard.start_date), ('create_date','<=', wizard.end_date)])
        row = 4
        number = 1

        if not wizard.golongan_obat:
            _query = """
                            select
                                date(a.date_order + interval '7 hours') as date_done,
                                g.kode_bpom as kode_bpom,
                                d.qty_done as qty_done,
                                (select name from stock_production_lot where id = d.lot_id) as lot_id,
                                date(d.expiration_date + interval '7 hours') as exp_date,
                                a.name as po_name,
                                (select name from res_partner where id= a.partner_id) as partner_id
                            from purchase_order a
                                join purchase_order_line b on b.order_id = a.id 
                                join stock_move c on c.purchase_line_id = b.id 
                                join stock_move_line d on d.move_id = c.id 
                                join stock_picking e on e.id = c.picking_id
                                join product_product f on f.id = d.product_id 
                                join product_template g on g.id = f.product_tmpl_id 
                            where date(a.create_date) >= '{_start_date}' 
                                and date(a.create_date) <= '{_end_date}' 
                                and e.picking_type_id_name = 'Receipts'
                        """.format(_start_date=wizard.start_date,_end_date=wizard.end_date)
        elif wizard.golongan_obat:
            _query = """
                        select
                            date(a.date_order + interval '7 hours') as date_done,
                            g.kode_bpom as kode_bpom,
                            d.qty_done as qty_done,
                            (select name from stock_production_lot where id = d.lot_id) as lot_id,
                            date(d.expiration_date + interval '7 hours') as exp_date,
                            a.name as po_name,
                            (select name from res_partner where id= a.partner_id) as partner_id
                        from purchase_order a
                            join purchase_order_line b on b.order_id = a.id 
                            join stock_move c on c.purchase_line_id = b.id 
                            join stock_move_line d on d.move_id = c.id 
                            join stock_picking e on e.id = c.picking_id
                            join product_product f on f.id = d.product_id 
                            join product_template g on g.id = f.product_tmpl_id 
                        where date(a.create_date) >= '{_start_date}' 
                            and date(a.create_date) <= '{_end_date}' 
                            and e.picking_type_id_name = 'Receipts'
                            and f.jenis_obat = {_jenis_obat}
                    """.format(_start_date=wizard.start_date, _end_date=wizard.end_date, _jenis_obat=wizard.golongan_obat.id)
        request.env.cr.execute(_query)
        check_data = request.env.cr.dictfetchall()
        for rec in check_data:
            sheet.write(row, 5, rec.get('lot_id') or '', text_style)
            sheet.write(row, 0, number or '', text_style)
            sheet.write(row, 1, 'Penerimaan', text_style)
            sheet.write(row, 2, rec.get('date_done') or '', format_date)
            sheet.write(row, 3, rec.get('kode_bpom') or '', text_style)
            sheet.write(row, 4, rec.get('qty_done') or '', text_style)
            sheet.write(row, 6, rec.get('exp_date') or '', format_date)
            sheet.write(row, 7, rec.get('po_name') or '', text_style)
            sheet.write(row, 8, rec.get('partner_id') or '', text_style)
            row += 1
            number += 1
        # for value in purchase:
        #     for picking in value.picking_ids:
        #         if not picking.is_return:
        #             for picking_lines in picking.move_line_ids_without_package:
        #                 if not wizard.golongan_obat:
        #                     sheet.write(row, 5, picking_lines.lot_id.name or '', text_style)
        #                     sheet.write(row, 0, number or '', text_style)
        #                     sheet.write(row, 1, 'Penerimaan', text_style)
        #                     sheet.write(row, 2, picking.date_done or 0, format_date)
        #                     sheet.write(row, 3, picking_lines.product_id.kode_bpom or '', text_style)
        #                     sheet.write(row, 4, picking_lines.qty_done or '', text_style)
        #                     sheet.write(row, 6, picking_lines.expiration_date or '', format_date)
        #                     sheet.write(row, 7, value.name or '', text_style)
        #                     sheet.write(row, 8, value.partner_id.name or '', text_style)
        #
        #                     row += 1
        #                     number += 1
        #                 elif wizard.golongan_obat:
        #                     if wizard.golongan_obat == picking_lines.product_id.jenis_obat:
        #                         sheet.write(row, 5, picking_lines.lot_id.name or '', text_style)
        #                         sheet.write(row, 0, number or '', text_style)
        #                         sheet.write(row, 1, 'Penerimaan', text_style)
        #                         sheet.write(row, 2, picking.date_done or 0, format_date)
        #                         sheet.write(row, 3, picking_lines.product_id.kode_bpom or '', text_style)
        #                         sheet.write(row, 4, picking_lines.qty_done or '', text_style)
        #                         sheet.write(row, 6, picking_lines.expiration_date or '', format_date)
        #                         sheet.write(row, 7, value.name or '', text_style)
        #                         sheet.write(row, 8, value.partner_id.name or '', text_style)
        #
        #                         row += 1
        #                         number += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

        return response
