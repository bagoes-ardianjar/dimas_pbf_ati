from datetime import date
from odoo import http
from odoo.http import content_disposition, request
import io
import xlsxwriter
import json
import math
     
class SaleReturExcelReportController(http.Controller):
    @http.route([
        '/return/excel_report/<model("x.report.return.xml"):wizard>',
    ], type='http', auth="user", csrf=False)
    def get_excel_report(self,wizard=None,**args):

        response = request.make_response(
                    None,
                    headers=[
                        ('Content-Type', 'application/vnd.ms-excel'),
                        ('Content-Disposition', content_disposition('Report Retur Customer' + '.xlsx'))
                    ]
                )
        # buat object workbook dari library xlsxwriter
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
 
        # buat style untuk mengatur jenis font, ukuran font, border dan alligment
        title_style = workbook.add_format({'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'font_size': 11, 'valign':'vcenter', 'align': 'center','bg_color':'#D3D3D3', 'color': 'black', 'bold': True})
        header_style = workbook.add_format({'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'font_size': 11, 'valign':'vcenter', 'align': 'center','bg_color':'#D3D3D3', 'color': 'black', 'bold': True})
        #code by adelia
        text_style = workbook.add_format({'font_name': 'Times', 'left': 1, 'bottom':1, 'right':1, 'top':1, 'align': 'left'})
        text_style_mid = workbook.add_format({'font_name': 'Times', 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'center'})
        number_style = workbook.add_format({'font_name': 'Times', 'left': 1, 'bottom':1, 'right':1, 'top':1, 'align': 'right'})
        currency_detail_table_style = workbook.add_format({'font_size': 11, 'valign': 'vcenter', 'align': 'centre',
                                                           'num_format': '_-"Rp"* #,##0.00_-;-"Rp"* #,##0.00_-;_-"Rp"* "-"_-;_-@_-',
                                                           'text_wrap': True, 'border': 1})

        # loop so sesuai tannggal yang dipilih
        so_obj = request.env['sale.order'].search([('create_date','>=', wizard.start_date), ('create_date','<=', wizard.end_date)])
        sheet = workbook.add_worksheet('Retur Customer')
        # set orientation jadi landscape
        sheet.set_landscape()
        # set ukuran kertas, 9 artinya kertas A4
        sheet.set_paper(9)
        # set margin kertas dalam satuan inchi
        sheet.set_margins(0.5,0.5,0.5,0.5)

        # set lebar kolom
        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 15)
        sheet.set_column('C:C', 35)
        sheet.set_column('D:D', 30)
        sheet.set_column('E:E', 15)
        sheet.set_column('F:F', 10)
        sheet.set_column('G:G', 20)
        sheet.set_column('H:H', 10)
        sheet.set_column('I:R', 20)


        # judul report
        # merge cell A1 sampai E1 dengan ukuran font 14 dan bold
        sheet.merge_range('A1:Q1', 'Laporan Retur Customer', title_style)
            
        # judul tabel
        sheet.write(1, 0, 'NO.', header_style)
        sheet.write(1, 1, 'Tgl Terima', header_style)
        sheet.write(1, 2, 'Nama PBF', header_style)
        sheet.write(1, 3, 'Nama Barang', header_style)
        sheet.write(1, 4, 'No Batch', header_style)
        sheet.write(1, 5, 'Qty', header_style)
        sheet.write(1, 6, 'Harga satuan Produk', header_style)
        sheet.write(1, 7, 'Satuan', header_style)
        sheet.write(1, 8, 'Alasan Retur', header_style)
        sheet.write(1, 9, 'NO Retur', header_style)
        # sheet.write(1, 8, 'PT/TB', header_style)
        sheet.write(1, 10, 'Tgl Retur', header_style)
        sheet.write(1, 11, 'Total Exc PPN', header_style)
        sheet.write(1, 12, 'Total Inc PPN', header_style)
        sheet.write(1, 13, 'No Faktur', header_style)
        sheet.write(1, 14, 'Tanggal Faktur', header_style)
        sheet.write(1, 15, 'Tanggal TF', header_style)
        sheet.write(1, 16, 'Keterangan', header_style)
        sheet.write(1, 17, 'Tgl Konfirmasi', header_style)

        row = 2
        number = 1

        request.env.cr.execute(
            """
                select
                    a.id as am_id,
                    a.source_document_id as source_document_id,
                    f.id as aml_product_id,
                    d.name as partner_id,
                    g.name as product_id,
                    (select name from stock_production_lot where id = e.lot_id) as lot_id,
                    e.qty_done as qty,
                    h.name as uom_id,
                    i.name as alasan_return,
                    c.scheduled_date as tanggal_return,
                    c.name as no_return,
                        case 
                        when a.name = '/' then (select m.name from account_move m where m.id = a.reversed_entry_id)
                        else concat((select m.name from account_move m where m.id = a.reversed_entry_id),', ',a.name)
                    end as no_faktur,
                    date(a.invoice_date) as tanggal_faktur,
                    date(a.payment_date) as tanggal_transfer,
                    date(a.payment_date) as tanggal_konfirmasi
                from account_move a 
                    join stock_picking c on c.id = a.source_document_id
                    join res_partner d on d.id = a.partner_id
                    join stock_move_line e on e.picking_id = c.id
                    join product_product f on f.id = e.product_id
                    join product_template g on g.id = f.product_tmpl_id
                    join uom_uom h on h.id = e.product_uom_id 
                    left join return_reason i on i.id = c.return_reason
                where
                    date(a.invoice_date) >= '{_start_date}'
                    and date(a.invoice_date) <= '{_end_date}'
                    and a.state in ('draft','approval','posted')
                    and a.move_type = 'out_refund'
                union
                select
                    a.id as am_id,
                    a.source_document_id as source_document_id,
                    d.id as aml_product_id,
                    c.name as partner_id,
                    e.name as product_id,
                    '-' as lot_id,
                    b.quantity as qty,
                    f.name as uom_id,
                    '-' as alasan_return,
                    date(a.invoice_date) as tanggal_return,
                    'From CN Manual' as no_return,
                    case
                        when a.name = '/' then '-'
                        else a.name
                    end as no_faktur,
                    date(a.invoice_date) as tanggal_faktur,
                    date(a.payment_date) as tanggal_transfer,
                    date(a.payment_date) as tanggal_konfirmasi
                from account_move a
                    join account_move_line b on b.move_id = a.id 
                    join res_partner c on c.id = a.partner_id
                    join product_product d on d.id = b.product_id 
                    join product_template e on e.id = d.product_tmpl_id
                    join uom_uom f on f.id = b.product_uom_id 
                where 
                    date(a.invoice_date) >= '{_start_date}'
                    and date(a.invoice_date) <= '{_end_date}'
                    and a.state in ('draft','approval','posted')
                    and a.move_type = 'out_refund'
                    and b.exclude_from_invoice_tab = false
                    and a.reversed_entry_id is null
                order by tanggal_return
                """.format(_start_date=str(wizard.start_date), _end_date=str(wizard.end_date)))
        feth_so = request.env.cr.dictfetchall()
        if feth_so:
            harga = 0
            for rec in feth_so:
                check_sm = request.env['stock.move'].sudo().search([('picking_id', '=', rec.get('source_document_id'))])
                sheet.write(row, 0, number or '-', text_style_mid)
                date_done = check_sm.origin_returned_move_id.picking_id.date_done.strftime('%Y-%m-%d') if check_sm.origin_returned_move_id.picking_id.date_done else '-'
                # date_done = rec.get('tanggal_terima').strftime('%Y-%m-%d') if rec.get('tanggal_terima') else '-'
                sheet.write(row, 1, date_done, text_style_mid)
                sheet.write(row, 2, rec.get('partner_id') or '-', text_style)
                sheet.write(row, 3, rec.get('product_id') or '-', text_style)
                sheet.write(row, 4, rec.get('lot_id') or '-', text_style_mid)
                sheet.write(row, 5, rec.get('qty') or '-', text_style_mid)

                check_aml = request.env['account.move.line'].sudo().search([('move_id', '=', rec.get('am_id')), ('product_id', '=', rec.get('aml_product_id')),('exclude_from_invoice_tab', '=', False)])
                if check_aml.harga_satuan:
                    harga = check_aml.harga_satuan
                else:
                    harga = 0

                if check_aml.tax_ids:
                    product_tax = 0
                    total_tax = 0
                    for data in check_aml.tax_ids:
                        tax_id = request.env['account.tax'].sudo().search([('id', '=', data.id)])
                        product_tax = round((harga * rec.get('qty')),2) * tax_id.amount /100
                        total_tax += product_tax
                else:
                    total_tax = 0
                harga_inc_ppn = round((harga * rec.get('qty')), 2) + total_tax
                # if rec.get('harga_satuan') :
                #     harga = rec.get('harga_satuan')
                # else:
                #     harga = 0
                sheet.write(row, 6, harga or '-', currency_detail_table_style)
                sheet.write(row, 7, rec.get('uom_id') or '-', text_style_mid)
                if rec.get('alasan_return') == False:
                    sheet.write(row, 8, '-', text_style)
                else:
                    sheet.write(row, 8, rec.get('alasan_return') or '-', text_style)
                sheet.write(row, 9, rec.get('no_return') or '-', text_style)
                tanggal_return = rec.get('tanggal_return').strftime('%Y-%m-%d') if rec.get('tanggal_return') else '-'
                sheet.write(row, 10, tanggal_return, text_style_mid)
                sheet.write(row, 11, round(harga * rec.get('qty'),2), currency_detail_table_style)
                sheet.write(row, 12, harga_inc_ppn, currency_detail_table_style)
                sheet.write(row, 13, rec.get('no_faktur'), text_style)
                invoice_date = str(rec.get('tanggal_faktur'))if rec.get('tanggal_faktur') else '-'
                sheet.write(row, 14, invoice_date, text_style_mid)
                tanggal_transfer = str(rec.get('tanggal_transfer')) if rec.get('tanggal_transfer') else '-'
                sheet.write(row, 15, tanggal_transfer, text_style_mid)
                sheet.write(row, 16, '', text_style)
                schedule_date = str(rec.get('tanggal_return')) if rec.get('tanggal_return') else '-'
                tanggal_konfirmasi = rec.get('tanggal_konfirmasi').strftime('%Y-%m-%d') if rec.get('tanggal_konfirmasi') else '-'
                sheet.write(row, 17, tanggal_konfirmasi, text_style_mid)
                row += 1
                number += 1

            # for v in so_obj:
            #     for i in v.picking_ids:
            #         if i.picking_type_id.name == 'Return:Delivery Orders':
            #             for order in v.order_line:
            #                 harga_satuan = int(order.harga_satuan_baru)
            #                 sheet.write(row, 6, harga_satuan or '-', text_style)
            #                 row += 1
            #                 number += 1
        # for v in so_obj:
        #     for i in v.picking_ids:
        #         if i.picking_type_id.name == 'Return:Delivery Orders':
        #             for invoice in v.invoice_ids:
        #
        #                 if invoice == v.invoice_ids[-1]:
        #
        #                     sheet.write(row, 15, '', text_style)
        #
        #                     # for line in invoice.invoice_line_ids:
        #                     #     print(line.product_id)
        #                     #     # sheet.write(row, 3, line.product_id.name or '-', text_style)
        #                     #     sheet.write(row, 4, line.quantity or '-', text_style)
        #                     #     sheet.write(row, 5, line.product_uom_id.name or '-', text_style)
        #                     #     nilai = int(line.price_unit) * int(line.quantity)
        #                     #     sheet.write(row, 10, nilai, text_style)
        #
        #                     for line in i.move_line_ids_without_package:
        #                         # print(line.product_id.name, i.name)
        #                         sheet.write(row, 12, invoice.name, text_style)
        #                         invoice_date = invoice.invoice_date.strftime('%Y-%m-%d') if invoice.invoice_date else '-'
        #                         sheet.write(row, 13, invoice_date, text_style)
        #
        #                         if invoice.invoice_payments_widget == False or invoice.invoice_payments_widget == 'false':
        #                             sheet.write(row, 14, '-', text_style)
        #                         else:
        #                             load =json.loads(invoice.invoice_payments_widget)
        #                             date = str(load['content'][0]['date'])
        #
        #                             sheet.write(row, 14, date, text_style)

                                # print(v.name)
                                # for order in v.order_line:
                                #     if order.product_id.id == line.product_id.id:
                                #         harga = int (order.price_unit) + int(order.product_margin_amount)
                                #         sheet.write(row, 6, harga or '-', text_style)
                                #
                                # sheet.write(row, 3, line.product_id.name or '-', text_style)
                                # sheet.write(row, 4, line.lot_id.name or '-', text_style)
                                # sheet.write(row, 5, line.qty_done or '-', text_style)
                                # sheet.write(row, 7, line.product_uom_id.name or '-', text_style)
                                # # print(line.product_id.lst_price, type(line.product_id.lst_price))
                                # nilai = int(line.product_id.lst_price) * int(line.qty_done)
                                # sheet.write(row, 11, nilai, text_style)
                                #
                                # date_done = i.date_done.strftime('%Y-%m-%d') if i.date_done else '-'
                                # sheet.write(row, 1, date_done, text_style)
                                # if i.return_reason.name == False:
                                #     sheet.write(row, 8, '-', text_style)
                                # else:
                                #     sheet.write(row, 8, i.return_reason.name or '-', text_style)
                                #
                                # # sheet.write(row, 3, i.product_id.name or '-', text_style)
                                # sheet.write(row, 9, i.name or '-', text_style)
                                # schedule_date = i.scheduled_date.strftime('%Y-%m-%d') if i.scheduled_date else '-'
                                # sheet.write(row, 10, schedule_date, text_style)
                                # sheet.write(row, 16, schedule_date, text_style)
                                #
                                # sheet.write(row, 0, number or '-', text_style)
                                # sheet.write(row, 2, v.partner_id.name or '-' , text_style)
                                # # sheet.write(row, 8, '', text_style)
                                #
                                # row += 1
                                # number += 1

        # masukkan file excel yang sudah digenerate ke response dan return 
        # sehingga browser bisa menerima response dan mendownload file yang sudah digenerate
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
 
        return response