from datetime import date
from odoo import models, fields, api, exceptions, _
from odoo import http
from odoo.http import content_disposition, request
import io
import xlsxwriter


class SaleBpomExcelReportController(http.Controller):
    @http.route([
        '/sale/excel_report/<model("x.report.bpom.xml"):wizard>',
    ], type='http', auth="user", csrf=False)
    def get_excel_report(self, wizard=None, **args):
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', content_disposition('Laporan Penyaluran Obat BPOM' + '.xlsx'))
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
            {'font_name': 'Times', 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'center'})
        alamat_style = workbook.add_format(
            {'font_name': 'Times', 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'left'})
        number_style = workbook.add_format(
            {'font_name': 'Times', 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'right'})

        # loop so sesuai tannggal yang dipilih
        so_obj = request.env['sale.order'].search(
            [('create_date', '>=', wizard.start_date),
                ('create_date', '<=', wizard.end_date)])

        sheet = workbook.add_worksheet('Penyaluran Obat BPOM')
        # set orientation jadi landscape
        sheet.set_landscape()
        # set ukuran kertas, 9 artinya kertas A4
        sheet.set_paper(9)
        # set margin kertas dalam satuan inchi
        sheet.set_margins(0.5, 0.5, 0.5, 0.5)

        # set lebar kolom
        sheet.set_column('A:A', 5)
        sheet.set_column('B:H', 20)
        sheet.set_column('I:K', 30)

        # judul report
        # merge cell A1 sampai E1 dengan ukuran font 14 dan bold
        sheet.merge_range('A1:K1', 'Laporan Penyaluran Obat BPOM', title_style)

        # judul tabel
        sheet.write(1, 0, 'NO.', header_style)
        sheet.write(1, 1, 'JENIS DISTRIBUSI', header_style)
        sheet.write(1, 2, 'TANGGAL DISTRIBUSI', header_style)
        sheet.write(1, 3, 'KODE OBAT JADI', header_style)
        sheet.write(1, 4, 'JUMLAH OBAT JADI', header_style)
        sheet.write(1, 5, 'BATCH OBAT JADI', header_style)
        sheet.write(1, 6, 'TANGGAL EXPIRED', header_style)
        sheet.write(1, 7, 'NOMOR SO', header_style)
        sheet.write(1, 8, 'TUJUAN', header_style)
        sheet.write(1, 9, 'ALAMAT', header_style)
        sheet.write(1, 10, 'KETERANGAN/PERUNTUKAN', header_style)

        row = 2
        number = 1

        if not wizard.golongan_obat :
            request.env.cr.execute(
                """
                    select 
                        g.distribution_type as jenis_distribusi,
                        date(d.date_order + interval '7 hours') as tanggal_distribusi,
                        d.id as so_id,
                        g.kode_bpom as kode_bpom,
                        a.qty_done as qty,
                        a.lot_id as lot_id,
                        (select name from stock_production_lot where id = a.lot_id) as lot_name,
                        date(a.expiration_date + interval '7 hours') as tanggal_expired,
                        d.name as no_so,
                        h."name" as partner_name,
                        h.street as street,
                        h.city as city
                    from stock_picking c
                        join stock_move_line a on a.picking_id = c.id 
                        join stock_move b on b.id = a.move_id 
                        join sale_order d on d.id = c.sale_id
                        join sale_order_line e on e.id = b.sale_line_id
                        join product_product f on f.id = a.product_id
                        join product_template g on g.id = f.product_tmpl_id
                        join res_partner h on h.id = d.partner_id
                    where Date(d.create_date) >= '{_start_date}' and Date(d.create_date) <= '{_end_date}' 
                        and c.picking_type_id_name = 'Delivery Orders'
                """.format(_start_date=str(wizard.start_date), _end_date=str(wizard.end_date)))

            feth_so = request.env.cr.dictfetchall()
            if feth_so:
                for rec in feth_so:
                    sheet.write(row, 0, number, text_style)
                    jenis_distribusi = '-'
                    if rec.get('jenis_distribusi') == 'dalam_negeri':
                        jenis_distribusi = 'Dalam Negeri'
                    elif rec.get('jenis_distribusi') == 'luar_negeri':
                        jenis_distribusi = 'Luar Negeri'
                    sheet.write(row, 1, jenis_distribusi or '-', text_style)
                    tanggal_distribusi = rec.get('tanggal_distribusi').strftime('%Y-%m-%d') if rec.get('tanggal_distribusi') else '-'
                    sheet.write(row, 2, tanggal_distribusi, text_style)
                    sheet.write(row, 3, rec.get('kode_bpom') or '', text_style)
                    sheet.write(row, 4, rec.get('qty') or 0, text_style)
                    sheet.write(row, 5, rec.get('lot_name') or '-', text_style)
                    tanggal_expired = rec.get('tanggal_expired').strftime('%Y-%m-%d') if rec.get('tanggal_expired') else '-'
                    sheet.write(row, 6, tanggal_expired, text_style)
                    sheet.write(row, 7, rec.get('no_so'), text_style)
                    sheet.write(row, 8, rec.get('partner_name') or '', text_style)
                    sheet.write(row, 9, str(rec.get('street')) or '' + ', ' + str(rec.get('city')) or '', alamat_style)
                    sheet.write(row, 10, rec.get('no_so'), text_style)

                    row += 1
                    number += 1

        elif wizard.golongan_obat:
            request.env.cr.execute(
                """
                    select 
                        g.distribution_type as jenis_distribusi,
                        date(d.date_order + interval '7 hours') as tanggal_distribusi,
                        d.id as so_id,
                        g.kode_bpom as kode_bpom,
                        a.qty_done as qty,
                        a.lot_id as lot_id,
                        (select name from stock_production_lot where id = a.lot_id) as lot_name,
                        date(a.expiration_date + interval '7 hours') as tanggal_expired,
                        d.name as no_so,
                        h."name" as partner_name,
                        h.street as street,
                        h.city as city,
                        f.jenis_obat
                    from stock_picking c
                        join stock_move_line a on a.picking_id = c.id 
                        join stock_move b on b.id = a.move_id 
                        join sale_order d on d.id = c.sale_id
                        join sale_order_line e on e.id = b.sale_line_id
                        join product_product f on f.id = a.product_id
                        join product_template g on g.id = f.product_tmpl_id
                        join res_partner h on h.id = d.partner_id
                    where Date(d.create_date) >= '{_start_date}' and Date(d.create_date) <= '{_end_date}' 
                        and c.picking_type_id_name = 'Delivery Orders'
                        and f.jenis_obat = {_jenis_obat}
                """.format(_start_date=str(wizard.start_date), _end_date=str(wizard.end_date),_jenis_obat=wizard.golongan_obat.id))

            feth_so = request.env.cr.dictfetchall()
            if feth_so:
                for rec in feth_so:
                    sheet.write(row, 0, number, text_style)
                    if rec.get('jenis_distribusi') == 'dalam_negeri':
                        jenis_distribusi = 'Dalam Negeri'
                    elif rec.get('jenis_distribusi') == 'luar_negeri':
                        jenis_distribusi = 'Luar Negeri'
                    else:
                        jenis_distribusi = '-'
                    sheet.write(row, 1, jenis_distribusi or '-', text_style)
                    tanggal_distribusi = rec.get('tanggal_distribusi').strftime('%Y-%m-%d') if rec.get(
                        'tanggal_distribusi') else '-'
                    sheet.write(row, 2, tanggal_distribusi, text_style)
                    sheet.write(row, 3, rec.get('kode_bpom') or '', text_style)
                    sheet.write(row, 4, rec.get('qty') or 0, text_style)
                    sheet.write(row, 5, rec.get('lot_name') or '-', text_style)
                    tanggal_expired = rec.get('tanggal_expired').strftime('%Y-%m-%d') if rec.get('tanggal_expired') else '-'
                    sheet.write(row, 6, tanggal_expired, text_style)
                    sheet.write(row, 7, rec.get('no_so'), text_style)
                    sheet.write(row, 8, rec.get('partner_name') or '', text_style)
                    sheet.write(row, 9, str(rec.get('street')) or '' + ', ' + str(rec.get('city')) or '', alamat_style)
                    sheet.write(row, 10, rec.get('no_so'), text_style)

                    row += 1
                    number += 1
        else :
            pass


        # for v in so_obj:
        #     if v.state == 'sale'or v.state =='done':
        #         for i in v.order_line:
        #             for move in i.move_ids:
        #                 for picking in move.picking_id:
        #                     if picking.picking_type_id.name == 'Delivery Orders':
        #                         date_done = picking.date_done.strftime('%Y-%m-%d') if picking.date_done else '-'
        #                         if not wizard.golongan_obat:
        #                             sheet.write(row, 2, date_done, text_style)
        #
        #                             for move_line in move.move_line_ids:
        #                                 sheet.write(row, 4, move_line.qty_done or 0, text_style)
        #                                 if not move_line.lot_id:
        #                                     sheet.write(row, 5, '-', text_style)
        #                                 else:
        #                                     sheet.write(row, 5, move_line.lot_id.name, text_style)
        #                                 if not move_line.expiration_date:
        #                                     sheet.write(row, 6, '-', text_style)
        #                                 else:
        #                                     sheet.write(row, 6, move_line.expiration_date.strftime('%Y-%m-%d'), text_style)
        #
        #
        #                             sheet.write(row, 3, i.product_id.kode_bpom or '', text_style)
        #                             # sheet.write(row, 4, i.product_uom_qty or '', text_style)
        #                             sheet.write(row, 7, v.name, text_style)
        #                             sheet.write(row, 8, v.partner_id.name or '', text_style)
        #                             if v.partner_id.street:
        #                                 sheet.write(row, 9, str(v.partner_id.street) + ', ' + str(v.partner_id.city), text_style)
        #                             else:
        #                                 sheet.write(row, 9, '-', text_style)
        #                             sheet.write(row, 10, '', text_style)
        #                             sheet.write(row, 0, number, text_style)
        #                             if i.product_id.distribution_type == 'dalam_negeri':
        #                                 sheet.write(row, 1, 'Dalam Negeri', text_style)
        #                             else:
        #                                 sheet.write(row, 1, 'Luar Negeri', text_style)
        #
        #                             row += 1
        #                             number += 1
        #                         elif wizard.golongan_obat:
        #                             if wizard.golongan_obat == i.product_id.jenis_obat:
        #                                 sheet.write(row, 2, date_done, text_style)
        #
        #                                 for move_line in move.move_line_ids:
        #                                     sheet.write(row, 4, move_line.qty_done or 0, text_style)
        #                                     if not move_line.lot_id:
        #                                         sheet.write(row, 5, '-', text_style)
        #                                     else:
        #                                         sheet.write(row, 5, move_line.lot_id.name, text_style)
        #                                     if not move_line.expiration_date:
        #                                         sheet.write(row, 6, '-', text_style)
        #                                     else:
        #                                         sheet.write(row, 6, move_line.expiration_date.strftime('%Y-%m-%d'), text_style)
        #
        #
        #                                 sheet.write(row, 3, i.product_id.kode_bpom or '', text_style)
        #                                 # sheet.write(row, 4, i.product_uom_qty or '', text_style)
        #                                 sheet.write(row, 7, v.name, text_style)
        #                                 sheet.write(row, 8, v.partner_id.name or '', text_style)
        #                                 if v.partner_id.street:
        #                                     sheet.write(row, 9, str(v.partner_id.street) + ', ' + str(v.partner_id.city), text_style)
        #                                 else:
        #                                     sheet.write(row, 9, '-', text_style)
        #                                 sheet.write(row, 10, '', text_style)
        #                                 sheet.write(row, 0, number, text_style)
        #                                 if i.product_id.distribution_type == 'dalam_negeri':
        #                                     sheet.write(row, 1, 'Dalam Negeri', text_style)
        #                                 else:
        #                                     sheet.write(row, 1, 'Luar Negeri', text_style)
        #
        #                                 row += 1
        #                                 number += 1
        #
        #         else:
        #             pass

        # masukkan file excel yang sudah digenerate ke response dan return
        # sehingga browser bisa menerima response dan mendownload file yang sudah digenerate
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

        return response