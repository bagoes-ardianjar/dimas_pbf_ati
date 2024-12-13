# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import content_disposition, request
from datetime import date
import io
import xlsxwriter

class PurchaseExcelReportController(http.Controller):
    @http.route([
        '/purchase/retur/excel_report/<model("wizard.po.retur"):wizard>',
    ], type='http', auth="user", csrf=False)
    def get_excel_retur_supplier(self, wizard=None, **args):

        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', content_disposition('Retur Supplier' + '.xlsx'))
            ]
        )

        # buat object workbook dari library xlsxwriter
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        # buat style untuk mengatur jenis font, ukuran font, border dan alligment
        title_style = workbook.add_format(
            {'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'font_size': 11, 'valign': 'vcenter', 'align': 'center',
             'bg_color': '#D3D3D3', 'color': 'black', 'bold': True})
        header_style = workbook.add_format(
            {'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'font_size': 11, 'valign': 'vcenter', 'align': 'center',
             'bg_color': '#D3D3D3', 'color': 'black', 'bold': True})
        # code by adelia
        text_style = workbook.add_format(
            {'font_name': 'Times', 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'left'})
        text_style_mid = workbook.add_format(
            {'font_name': 'Times', 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'center'})
        number_style = workbook.add_format(
            {'font_name': 'Times', 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'right'})
        currency_detail_table_style = workbook.add_format({'font_size': 11, 'valign': 'vcenter', 'align': 'centre',
                                                           'num_format': '_-"Rp"* #,##0.00_-;-"Rp"* #,##0.00_-;_-"Rp"* "-"_-;_-@_-',
                                                           'text_wrap': True, 'border': 1})



        sheet = workbook.add_worksheet('Retur Supplier')
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
        sheet.set_column('J:R', 20)


        # judul report
        # merge cell A1 sampai E1 dengan ukuran font 14 dan bold
        sheet.merge_range('A1:O2', 'Retur Supplier', title_style)

        sheet.write(3, 0, 'NO.', header_style)
        sheet.write(3, 1, 'Tanggal Terima', header_style)
        sheet.write(3, 2, 'Nama PBF', header_style)
        sheet.write(3, 3, 'Nama Barang', header_style)
        sheet.write(3, 4, 'Batch', header_style)
        sheet.write(3, 5, 'QTY', header_style)
        sheet.write(3, 6, 'Satuan', header_style)
        sheet.write(3, 7, 'Harga Satuan Product', header_style)
        sheet.write(3, 8, 'Alasan Retur', header_style)
        sheet.write(3, 9, 'Nomer Retur', header_style)
        sheet.write(3, 10, 'Tanggal Retur', header_style)
        sheet.write(3, 11, 'Total Exc PPN', header_style)
        sheet.write(3, 12, 'Total Inc PPN', header_style)
        sheet.write(3, 13, 'No Faktur', header_style)
        sheet.write(3, 14, 'Tanggal Faktur', header_style)
        sheet.write(3, 15, 'Tanggal TF', header_style)
        sheet.write(3, 16, 'Keterangan', header_style)
        sheet.write(3, 17, 'Tanggal Konfirmasi', header_style)


        purchase = request.env['purchase.order'].search([('create_date','>=', wizard.start_date), ('create_date','<=', wizard.end_date)])


        row = 4
        number = 1

        # request.env.cr.execute(
        #     """
        #         select
        #             date(c.date_done) as tanggal_terima,
        #             e.name as partner_id,
        #             g.name as product_id,
        #             (select name from stock_production_lot where id = d.lot_id) as lot_id,
        #             d.qty_done as qty,
        #             g.hna as harga_satuan,
        #             k.name as uom_id,
        #             l.name as alasan_return,
        #             c.name as no_return,
        #             date(c.scheduled_date) as tanggal_return,
        #             g.hna * d.qty_done as total,
        #             case
        #                 when (select x.name from account_move x where x.source_document_id = c.id) = '/' then (select y.name from account_move y where y.id = (select reversed_entry_id from account_move x where x.source_document_id = c.id))
        #                 else concat((select y.name from account_move y where y.id = (select reversed_entry_id from account_move x where x.source_document_id = c.id)),', ',(select x.name from account_move x where x.source_document_id = c.id))
        #             end as no_faktur,
        #             (select date(x.invoice_date) from account_move x where x.source_document_id = c.id) as tanggal_faktur,
        #             (select date(x.payment_date) from account_move x where x.source_document_id = c.id) as tanggal_transfer,
        #             date(c.scheduled_date) as tanggal_konfirmasi
        #         from stock_move a
        #             left join account_move b on b.stock_move_id = a.id
        #             join stock_picking c on c.id = a.picking_id
        #             join stock_move_line d on d.move_id = a.id
        #             left join res_partner e on e.id = c.partner_id
        #             join product_product f on f.id = d.product_id
        #             join product_template g on g.id = f.product_tmpl_id
        #             left join margin_product h on h.id = g.margin
        #             join purchase_order_line i on i.id = a.purchase_line_id
        #             join purchase_order j on j.id = i.order_id
        #             join uom_uom k on k.id = d.product_uom_id
        #             left join return_reason l on l.id = c.return_reason
        #         where date(c.create_date) >= '{_start_date}' and date(c.create_date) <= '{_end_date}' and c.picking_type_id = 6 and (select x.state from account_move x where x.source_document_id = c.id) ='posted'
        #     """.format(_start_date=str(wizard.start_date), _end_date=str(wizard.end_date)))

        request.env.cr.execute(
            """
                select
                    a.id as am_id,
                    j.id as aml_id,
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
                    join stock_move b on b.picking_id = c.id 
                    join account_move_line j on j.move_id = a.id 
                where
                    date(a.invoice_date) >= '{_start_date}'
                    and date(a.invoice_date) <= '{_end_date}'
                    and a.state in ('draft','approval','posted')
                    and a.move_type = 'in_refund'
                    and j.exclude_from_invoice_tab = false	
                union
                select 
                    a.id as am_id,
                    b.id as aml_id,
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
                    and a.move_type = 'in_refund'
                    and b.exclude_from_invoice_tab = false
                    and a.reversed_entry_id is null
                order by tanggal_return
            """.format(_start_date=str(wizard.start_date), _end_date=str(wizard.end_date)))
        feth_so = request.env.cr.dictfetchall()
        if feth_so:
            for rec in feth_so:
                check_sm = request.env['stock.move'].sudo().search([('picking_id', '=', rec.get('source_document_id'))])
                sheet.write(row, 0, number or '-', text_style_mid)
                # date_done = rec.get('tanggal_terima').strftime('%Y-%m-%d') if rec.get('tanggal_terima') else '-'
                date_done = check_sm.origin_returned_move_id.picking_id.date_done.strftime(
                    '%Y-%m-%d') if check_sm.origin_returned_move_id.picking_id.date_done else '-'
                sheet.write(row, 1, date_done, text_style_mid)
                sheet.write(row, 2, rec.get('partner_id') or '-', text_style)
                sheet.write(row, 3, rec.get('product_id') or '-', text_style)
                sheet.write(row, 4, rec.get('lot_id') or '-', text_style)
                sheet.write(row, 5, rec.get('qty') or '-', text_style_mid)
                sheet.write(row, 6, rec.get('uom_id') or '-', text_style_mid)
                # if rec.get('harga_satuan') :
                #     harga = rec.get('harga_satuan')
                # else:
                #     harga = 0
                check_aml = request.env['account.move.line'].sudo().search(
                    [('move_id', '=', rec.get('am_id')), ('product_id', '=', rec.get('aml_product_id')),
                     ('exclude_from_invoice_tab', '=', False)])
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

                harga_inc_ppn = round((harga * rec.get('qty')),2) + total_tax
                sheet.write(row, 7, harga or '-', currency_detail_table_style)
                if rec.get('alasan_return') == False:
                    sheet.write(row, 8, '-', text_style)
                else:
                    sheet.write(row, 8, rec.get('alasan_return') or '-', text_style)
                sheet.write(row, 9, rec.get('no_return') or '-', text_style)
                schedule_date = rec.get('tanggal_return').strftime('%Y-%m-%d') if rec.get('tanggal_return') else '-'
                sheet.write(row, 10, schedule_date, text_style_mid)
                sheet.write(row, 11, round((harga * rec.get('qty')),2), currency_detail_table_style)
                sheet.write(row, 12, harga_inc_ppn, currency_detail_table_style)
                sheet.write(row, 13, rec.get('no_faktur'), currency_detail_table_style)
                invoice_date = str(rec.get('tanggal_faktur')) if rec.get('tanggal_faktur') else '-'
                sheet.write(row, 14, invoice_date, text_style_mid)
                tanggal_transfer = str(rec.get('tanggal_transfer')) if rec.get('tanggal_transfer') else '-'
                sheet.write(row, 15, tanggal_transfer, text_style_mid)
                sheet.write(row, 16, '', text_style)
                schedule_date = str(rec.get('tanggal_return')) if rec.get('tanggal_return') else '-'
                sheet.write(row, 17, schedule_date, text_style_mid)

                row += 1
                number += 1
        # for value in purchase:
        #     for picking in value.picking_ids:
        #         for invoice in value.invoice_ids:
        #             if invoice == value.invoice_ids[-1]:
        #                     sheet.write(row, 12, invoice.name, text_style)
        #                     sheet.write(row, 13, invoice.invoice_date, format_date)
        #                     sheet.write(row, 14, invoice.payment_date, format_date)
        #                     name = picking.name
        #                     type_retur = name[0:3]
        #                     if type_retur == 'RET':
        #                         for picking_lines in picking.move_line_ids_without_package:
        #                             for data in value.order_line:
        #                                     # if picking_lines.product_id.id == data.product_id.id:
        #                                 total = picking_lines.qty_done * data.price_unit
        #                                 sheet.write(row, 11, total, header_style)
        #                                 sheet.write(row, 7, data.price_unit, text_style)
        #                             sheet.write(row, 0, number, text_style)
        #                             sheet.write(row, 1,  picking.date_done, format_date)
        #                             sheet.write(row, 2, value.partner_id.name, text_style)
        #                             sheet.write(row, 3, picking_lines.product_id.name, text_style)
        #                             sheet.write(row, 4, picking_lines.lot_id.name, text_style)
        #                             sheet.write(row, 5, picking_lines.qty_done, text_style)
        #                             sheet.write(row, 6, picking_lines.product_uom_id.name, text_style)
        #                             sheet.write(row, 8, picking.return_reason.name, text_style)
        #                             sheet.write(row, 9, picking.name, text_style)
        #
        #                             sheet.write(row, 10, picking.scheduled_date, format_date)
        #                             sheet.write(row, 15, '', text_style)
        #                             sheet.write(row, 16,  picking.scheduled_date, format_date)
        #
        #                             row += 1
        #                             number += 1
        #

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
        return response
