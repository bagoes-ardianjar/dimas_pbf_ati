from odoo import models, fields, api, exceptions, _
from datetime import datetime

header_title = ['Nomor Ref', 'Tanggal', 'Kode PLU', 'Nama Barang', 'Qty', 'Batch/S.N/IMEI', 'Exp. Date', 'Satuan', 'Harga Beli', 'Jumlah Diskon Per Line', 'Global Discount', 'Jumlah Pembelian Inc PPN']

class x_report_pembelian_po(models.TransientModel):
    _name = 'x.report.pembelian.po'
 
 
    # so_id = fields.Many2many('sale.order', string='Sale Order')
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    company_id = fields.Many2one('res.company', 'Company')
 
 
    def action_print_report_po(self):
        data = {'start_date': self.start_date, 'end_date': self.end_date, 'company_id':self.company_id.id}
        return self.env.ref('ati_report_sale.action_report_po_peritem').report_action(self, data=data)

    def action_print_report_po_xlsx(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'x.report.pembelian.po'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        return self.env.ref('ati_report_sale.action_report_po_peritem_xlsx').report_action(self, data=datas)

class x_report_pembelian_po_pdf(models.AbstractModel):
    _name = 'report.ati_report_sale.po_peritem_pdf_template'

    def _get_report_values(self, docids, data=None):
        domain = [('state', '=', 'purchase')]
        if data.get('start_date'):
            domain.append(('create_date', '>=', data.get('start_date')))
        if data.get('end_date'):
            domain.append(('create_date', '<=', data.get('end_date')))
        if data.get('company_id'):
            domain.append(('company_id', '=', data.get('company_id')))

        if data.get('company_id'):
            domain_c = [('id', '=', data.get('company_id'))]
            company_obj = self.env['res.company'].search(domain_c)

        curr_c =self.env.company

        start_date = data.get('start_date')
        # datetime.strptime(str(data.get('start_date')), "%Y-%m-%d")
        end_date = data.get('end_date')
        # datetime.strptime(str(data.get('end_date')), "%Y-%m-%d")
        docs = []
        self._cr.execute(
            """
                select 
                    d.id as sml_id,
                    a.name as no_po,
                    DATE(a.date_approve) as tanggal,
                    f.sku as kode_plu,
                    f.name as nama_barang,
                    d.qty_done as qty,
                    d.lot_name as batch,
                    DATE(d.expiration_date) as exp_date,
                    g.name as uom,
                    b.ati_price_unit as harga,
                    i.total_tax as total_tax,
                    (coalesce(b.discount_1,0) * coalesce(b.ati_price_unit,0) / 100)+ (coalesce(b.discount_2,0) * coalesce(b.ati_price_unit,0) / 100) + coalesce(b.discount_3,0) + coalesce(b.discount_4,0) as diskon,
                    a.total_global_discount as total_global_discount,
                    coalesce(b.ati_price_unit - (coalesce ((b.discount_1 + b.discount_2)*b.ati_price_unit/100,0) + coalesce((b.discount_3 + b.discount_4),0)),0) * d.qty_done as subtotal,
                    (SELECT COUNT(o.id)
                    FROM purchase_order x
                    JOIN purchase_order_line y ON y.order_id = x.id
                    JOIN stock_move z ON z.purchase_line_id = y.id
                    JOIN stock_move_line o ON o.move_id = z.id
                    join stock_picking p on p.id = z.picking_id
                    WHERE x.id = a.id and p.picking_type_id_name = 'Receipts' and y.ati_price_unit <> 0) as jumlah_line
                from purchase_order a
                    join purchase_order_line b on b.order_id = a.id
                    join stock_move c on c.purchase_line_id = b.id
                    join stock_move_line d on d.move_id = c.id
                    join product_product e on e.id = d.product_id
                    join product_template f on f.id = e.product_tmpl_id
                    join uom_uom g on g.id = d.product_uom_id
                    join stock_picking h on h.id = c.picking_id
                    join account_move_line i on i.purchase_line_id = b.id
                    join account_move j on j.id = i.move_id 
                where DATE(j.invoice_date) >= '{_start_date}' and DATE(j.invoice_date) <= '{_end_date}'and a.company_id = {_company_id} and h.picking_type_id_name = 'Receipts' and h.state = 'done' and j.state in ('draft','approval','posted') and j.move_type ='in_invoice'
            """.format(_start_date=str(data.get('start_date')), _end_date=str(data.get('end_date')), _company_id=data.get('company_id')))

        feth_purchase = self._cr.dictfetchall()
        pembelian_list = []
        subtotal = 0
        jumlah_pembelian = 0
        picking_list = []
        total = 0
        global_discount = 0
        if feth_purchase :
            jml_picking = ()
            for rec in feth_purchase:
                sml_id = rec.get('sml_id')
                sml = self.env['stock.move.line'].sudo().search([('id', '=', sml_id)])
                if rec.get('harga'):
                    global_discount = rec.get('total_global_discount')/rec.get('jumlah_line')
                if not rec.get('harga'):
                    global_discount = 0
                var_pembelian = ((rec.get('harga') - rec.get('diskon')) * rec.get('qty')) -global_discount
                # var_pembelian = rec.get('subtotal')-global_discount
                # ppn = var_pembelian*11/100
                ppn = rec.get('total_tax')
                # jumlah_pembelian_inc_ppn =  var_pembelian + ppn
                jumlah_pembelian_inc_ppn = sml.price_subtotal - sml.global_diskon_line + sml.total_tax
                pembelian_list.append({
                    'no_po': rec.get('no_po'),
                    'tanggal': rec.get('tanggal'),
                    'kode_plu': rec.get('kode_plu'),
                    'nama_barang': rec.get('nama_barang'),
                    'qty': rec.get('qty'),
                    'batch': rec.get('batch'),
                    'exp_date': rec.get('exp_date'),
                    'uom': rec.get('uom'),
                    'harga': rec.get('harga') or 0,
                    'diskon': rec.get('diskon') or 0,
                    'global_discount': sml.global_diskon_line,
                    'subtotal': sml.price_subtotal,
                    'jumlah_pembelian_inc_ppn': jumlah_pembelian_inc_ppn
                })
                total += rec.get('qty')
                jumlah_pembelian += jumlah_pembelian_inc_ppn
        if pembelian_list:
            docs = pembelian_list

        result = {
            'doc_model': 'purchase.order',
            'docs': docs,
            'cmp': company_obj,
            'datas': data,
            'start': start_date,
            'end': end_date,
            'docs': docs,
            'total': total,
            'jumlah_pembelian': jumlah_pembelian
        }
        return result

class x_report_pembelian_po_xlsx(models.AbstractModel):
    _name = 'report.ati_report_sale.po_peritem_xlsx_template'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objs):

        # FORMAT TABLE #
        formatHeaderCompany = workbook.add_format({'font_size': 14, 'valign':'vcenter', 'align': 'center', 'bold': True})
        formatSubHeaderCompanyBold = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'center', 'bold': True})
        formatSubHeaderCompany = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'center'})
        formatHeaderTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'bold': True, 'bg_color':'#4ead2f', 'color':'white', 'text_wrap': True, 'border': 1})
        formatHeaderCurrencyTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'bold': True, 'bg_color':'#4ead2f', 'color':'white', 'num_format': '_-"Rp"* #,##0.00_-;-"Rp"* #,##0.00_-;_-"Rp"* "-"_-;_-@_-', 'text_wrap': True, 'border': 1})
        formatDetailTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre','text_wrap': True, 'border': 1})
        formatDetailCurrencyTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'num_format': '_-"Rp"* #,##0.00_-;-"Rp"* #,##0.00_-;_-"Rp"* "-"_-;_-@_-', 'text_wrap': True, 'border': 1})

        title = 'Laporan Rekap Pembelian Per Item'
        sheet = workbook.add_worksheet(title)

        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 20)
        sheet.set_column(3, 3, 20)
        sheet.set_column(4, 4, 20)
        sheet.set_column(5, 5, 20)
        sheet.set_column(6, 6, 20)
        sheet.set_column(7, 7, 20)
        sheet.set_column(8, 8, 20)
        sheet.set_column(9, 9, 20)
        sheet.set_column(10, 10, 20)
        sheet.set_column(11, 11, 20)
        # sheet.set_column(12, 12, 20)

        start_date = datetime.strptime(data['form']['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['form']['end_date'], '%Y-%m-%d').date()
        periode = start_date.strftime("%d %B %Y") if start_date == end_date else f'{start_date.strftime("%d %B %Y")} - {end_date.strftime("%d %B %Y")}'

        sheet.merge_range(1, 0, 1, 10, 'Laporan Rekap Pembelian Per Item', formatHeaderCompany)
        sheet.merge_range(2, 0, 2, 10, f'Periode {periode}', formatSubHeaderCompanyBold)
        sheet.merge_range(3, 0, 3, 10, '(Dalam Rupiah)', formatSubHeaderCompany)

        row =  5
        column = 0

        for header in header_title:
            sheet.write(row, column, header, formatHeaderTable)
            column += 1


        #### DATA REPORT ####
        domain = [('state', '=', 'purchase')]
        if data['form']['start_date']:
            domain.append(('create_date', '>=', data['form']['start_date']))
        if data['form']['end_date']:
            domain.append(('create_date', '<=', data['form']['end_date']))
        if data['form']['company_id']:
            domain.append(('company_id', '=', data['form']['company_id']))

        if data['form']['company_id']:
            domain_c = [('id', '=', data['form']['company_id'])]
            company_obj = self.env['res.company'].search(domain_c)

        curr_c = self.env.company
        start_date = data['form']['start_date']
        # datetime.strptime(str(data.get('start_date')), "%Y-%m-%d")
        end_date = data['form']['end_date']
        # datetime.strptime(str(data.get('end_date')), "%Y-%m-%d")

        self._cr.execute(
            """
                select 
                    d.id as sml_id,
                    a.name as no_po,
                    DATE(a.date_approve) as tanggal,
                    f.sku as kode_plu,
                    f.name as nama_barang,
                    d.qty_done as qty,
                    d.lot_name as batch,
                    DATE(d.expiration_date) as exp_date,
                    g.name as uom,
                    b.ati_price_unit as harga,
                    i.total_tax as total_tax,
                    (coalesce(b.discount_1,0) * coalesce(b.ati_price_unit,0) / 100)+ (coalesce(b.discount_2,0) * coalesce(b.ati_price_unit,0) / 100) + coalesce(b.discount_3,0) + coalesce(b.discount_4,0) as diskon,
                    a.total_global_discount as total_global_discount,
                    coalesce(b.ati_price_unit - (coalesce ((b.discount_1 + b.discount_2)*b.ati_price_unit/100,0) + coalesce((b.discount_3 + b.discount_4),0)),0) * d.qty_done as subtotal,
                    (SELECT COUNT(o.id)
                    FROM purchase_order x
                    JOIN purchase_order_line y ON y.order_id = x.id
                    JOIN stock_move z ON z.purchase_line_id = y.id
                    JOIN stock_move_line o ON o.move_id = z.id
                    join stock_picking p on p.id = z.picking_id
                    WHERE x.id = a.id and p.picking_type_id_name = 'Receipts' and y.ati_price_unit <> 0) as jumlah_line
                from purchase_order a
                    join purchase_order_line b on b.order_id = a.id
                    join stock_move c on c.purchase_line_id = b.id
                    join stock_move_line d on d.move_id = c.id
                    join product_product e on e.id = d.product_id
                    join product_template f on f.id = e.product_tmpl_id
                    join uom_uom g on g.id = d.product_uom_id
                    join stock_picking h on h.id = c.picking_id
                    join account_move_line i on i.purchase_line_id = b.id
                    join account_move j on j.id = i.move_id 
                where DATE(j.invoice_date) >= '{_start_date}' and DATE(j.invoice_date) <= '{_end_date}'and a.company_id = {_company_id} and h.picking_type_id_name = 'Receipts' and h.state = 'done' and j.state in ('draft','approval','posted') and j.move_type ='in_invoice' and j.source_document is not null
            """.format(_start_date=str(data['form']['start_date']), _end_date=str(data['form']['end_date']),
                       _company_id=data['form']['company_id']))

        feth_purchase = self._cr.dictfetchall()
        total = 0
        jumlah_pembelian_inc_ppn = 0
        jumlah_pembelian = 0
        row += 1
        row_start = row + 1
        global_discount = 0
        if feth_purchase:
            for rec in feth_purchase:
                sml_id = rec.get('sml_id')
                sml = self.env['stock.move.line'].sudo().search([('id', '=', sml_id)])
                if rec.get('harga'):
                    global_discount = rec.get('total_global_discount') / rec.get('jumlah_line')
                if not rec.get('harga'):
                    global_discount = 0
                # global_discount = rec.get('total_global_discount') / rec.get('jumlah_line')
                var_pembelian = ((rec.get('harga') - rec.get('diskon')) * rec.get('qty')) - global_discount
                # var_pembelian = rec.get('subtotal') - global_discount
                # ppn = var_pembelian * 11 / 100
                ppn = rec.get('total_tax')
                # jumlah_pembelian_inc_ppn = var_pembelian + ppn
                jumlah_pembelian_inc_ppn = sml.price_subtotal - sml.global_diskon_line + sml.total_tax
                total += rec.get('qty')
                jumlah_pembelian += jumlah_pembelian_inc_ppn

                #### WRITE DATA ####
                sheet.write(row, 0, rec.get('no_po'), formatDetailTable)
                sheet.write(row, 1, str(rec.get('tanggal')), formatDetailTable)
                sheet.write(row, 2, rec.get('kode_plu'), formatDetailTable)
                sheet.write(row, 3, rec.get('nama_barang'), formatDetailTable)
                sheet.write(row, 4, rec.get('qty'), formatDetailTable)
                sheet.write(row, 5, rec.get('batch'), formatDetailCurrencyTable)
                sheet.write(row, 6, str(rec.get('exp_date')), formatDetailTable)
                sheet.write(row, 7, rec.get('uom'), formatDetailTable)
                #### WRITE DATA ####
                sheet.write(row, 8, rec.get('harga') or 0, formatDetailCurrencyTable)
                sheet.write(row, 9, rec.get('diskon'), formatDetailCurrencyTable)
                sheet.write(row, 10, sml.global_diskon_line, formatDetailCurrencyTable)
                # sheet.write(row, 11, var_pembelian, formatDetailCurrencyTable)
                sheet.write(row, 11, jumlah_pembelian_inc_ppn, formatDetailCurrencyTable)
                row += 1

        row_end = row
        column_end = row_end + 1
        sheet.merge_range(row, 0, row, 3, 'Total', formatHeaderTable)
        sheet.write(row, 4, total, formatHeaderTable)
        sheet.write(row, 5, '', formatHeaderTable)
        sheet.write(row, 6, '', formatHeaderTable)
        sheet.write(row, 7, '', formatHeaderTable)
        sheet.write(row, 8, '', formatHeaderTable)
        sheet.write(row, 9, '', formatHeaderTable)
        sheet.write(row, 10, '', formatHeaderTable)
        # sheet.write(row, 11, '', formatHeaderTable)
        sheet.write(row, 11, jumlah_pembelian, formatHeaderCurrencyTable)




        # docs = self.env['purchase.order'].search(domain)
        #
        # if data.get('company_id'):
        #     domain_c = [('id', '=', data.get('company_id'))]
        #     company_obj = self.env['res.company'].search(domain_c)
        #
        # curr_c =self.env.company
        # print(curr_c, )
        #
        # start_date = data.get('start_date')
        # # datetime.strptime(str(data.get('start_date')), "%Y-%m-%d")
        # end_date = data.get('end_date')
        # # datetime.strptime(str(data.get('end_date')), "%Y-%m-%d")
        #
        # total = 0
        # ati_price_unit = 0
        # diskon = 0
        # jml_pembelian = 0
        # total_jml_pembelian = 0
        # for doc in docs:
        #     for i in doc.picking_ids:
        #         if i.picking_type_id.name == 'Receipts':
        #             for line in i.move_line_ids_without_package:
        #                 total += line.qty_done
        #                 ati_price_unit = round(line.move_id.purchase_line_id.ati_price_unit, 2)
        #                 diskon = round((((line.move_id.purchase_line_id.discount_1 + line.move_id.purchase_line_id.discount_2 + line.move_id.purchase_line_id.discount_3 + line.move_id.purchase_line_id.discount_4) / 100) * ati_price_unit),2)
        #                 jml_pembelian = round(((ati_price_unit - diskon) * line.qty_done), 2)
        #                 total_jml_pembelian += jml_pembelian

        # total=0
        # harga_jual =0
        # jml_diskon =0
        # # jml_pembelian = 0
        # total_jml_pembelian = 0
        # for doc in docs:
        #     for i in doc.picking_ids:
        #         if i.picking_type_id.name == 'Receipts':
        #             for line in i.move_line_ids_without_package:
        #                 total+= line.qty_done
        #
        #                 for oline in doc.order_line:
        #                     if oline.product_id.id == line.product_id.id:
        #                         harga_jual += oline.price_unit + oline.product_margin_amount
        #                         # total+= oline.product_uom_qty
        #                         jml_diskon += (oline.amount_disc1 + oline.amount_disc2 + oline.discount_3 +oline.discount_4)
        #                         all_diskon = (oline.amount_disc1 + oline.amount_disc2 + oline.discount_3 +oline.discount_4)
        #                         jml_pembelian = (oline.ati_price_unit - all_diskon) * line.qty_done
        #                         oline.total_pembelian_for_report = jml_pembelian
        #                         # print(jml_pembelian, oline.id, '=====================================')
        #                         # po_line_obj = self.env['purchase.order.line'].sudo().search([('id', '=', oline.id)])
        #                         total_jml_pembelian +=jml_pembelian
        #                         # jml_pembelian +=oline.price_subtotal


        # return {
        #
        #     'doc_ids': docs.ids,
        #     'doc_model': 'purchase.order',
        #     'docs': docs,
        #     'cmp': company_obj,
        #     'datas': data,
        #     'total':total,
        #     # 'harga_jual':harga_jual,
        #     # 'jml_diskon': jml_diskon,
        #     'start':start_date,
        #     'end': end_date,
        #     # 'jml_pembelian': jml_pembelian,
        #     'total_jml_pembelian':total_jml_pembelian
        #     # 'total': total
        # }
