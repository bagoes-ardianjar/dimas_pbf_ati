from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta

from datetime import datetime as dt

class ReportPrekusorKemenkes(models.TransientModel):
    _name = 'report.prekusor.kemenkes'
    _description = 'Report Prekusor Kemenkes'

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    type = fields.Selection([
        ("receipt","Pemasukan"),
        ("do","Pengeluaraan"),
        ("receipt_do", "Pemasukan & Pengeluaran")
    ], string='Type', default="receipt_do")
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    product_ids = fields.Many2many("product.product", string="Product")
    golongan_obat = fields.Many2one(comodel_name='jenis.obat', string='Golongan Obat')

    def download_report(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'report.prekusor.kemenkes'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        return self.env.ref('ati_pbf_stock.prekusor_kemenkes').report_action(self, data=datas)

class PrekusorKemenkesReportXlsx(models.AbstractModel):
    _name = 'report.ati_pbf_stock.prekusor_kemenkes_xls.xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        formatHeader = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'center','bg_color':'#D3D3D3', 'color': 'black', 'bold': True})
        formatTabel = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'center', 'color': 'black', 'bold': False})
        formatTabelLeft = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'left', 'color': 'black', 'bold': False})
        formatHeaderCompany = workbook.add_format({'font_size': 14, 'valign': 'vcenter', 'align': 'center', 'bold': True})

        formatHeader.set_border(1)
        formatTabel.set_border(1)
        formatTabelLeft.set_border(1)
        formatHeader.set_text_wrap()
        formatTabel.set_text_wrap()
        formatTabelLeft.set_text_wrap()

        datas = data.get('form', {})
        warehouse = datas.get('warehouse_id', False)
        warehouse_id = self.env['stock.warehouse'].sudo().browse(warehouse)

        sheet = workbook.add_worksheet('Prekusor Kemenkes')

        start_date = datetime.strptime(datas.get('date_from'), '%Y-%m-%d').date()
        end_date = datetime.strptime(datas.get('date_to'), '%Y-%m-%d').date()
        periode = start_date.strftime("%d %B %Y") if start_date == end_date else f'{start_date.strftime("%d %B %Y")} - {end_date.strftime("%d %B %Y")}'

        if warehouse:
            sheet.merge_range(0, 0, 0, 15, 'Prekusor Kemenkes ' + f'Periode {periode}' + ' ( Warehouse : '+ warehouse_id.name + ' )', formatHeaderCompany)
        else:
            sheet.merge_range(0, 0, 0, 15, 'Prekusor Kemenkes ' + f'Periode {periode}',formatHeaderCompany)

        sheet.set_column(4, 0, 15)
        sheet.set_column(4, 1, 25)
        sheet.set_column(4, 2, 15)
        sheet.set_column(4, 3, 15)
        sheet.set_column(4, 4, 15)
        sheet.set_column(4, 5, 15)
        sheet.set_column(4, 6, 15)
        sheet.set_column(4, 7, 15)
        sheet.set_column(4, 8, 15)
        sheet.set_column(4, 9, 15)
        sheet.set_column(4, 10, 15)
        sheet.set_column(4, 11, 15)
        sheet.set_column(4, 12, 15)
        sheet.set_column(4, 13, 15)
        sheet.set_column(4, 14, 15)
        sheet.set_column(4, 15, 15)

        sheet.merge_range(2,0,4,0, 'Kode Obat', formatHeader)
        sheet.merge_range(2,1,4,1, 'Nama Obat', formatHeader)

        sheet.merge_range(2,2,2,8, 'Pemasukan', formatHeader)
        sheet.merge_range(3,2,4,2, 'Tanggal Transaksi', formatHeader)
        sheet.merge_range(3,3,4,3, 'Dokumen Penerima', formatHeader)
        sheet.merge_range(3,4,4,4, 'Kode Industri', formatHeader)
        sheet.merge_range(3,5,4,5, 'Kode PBF', formatHeader)
        sheet.merge_range(3,6,4,6, 'Jumlah Masuk', formatHeader)
        sheet.merge_range(3,7,4,7, 'Kode Batch', formatHeader)
        sheet.merge_range(3,8,4,8, 'Expired Date', formatHeader)

        sheet.merge_range(2,9,2,15, 'Pengeluaran', formatHeader)
        sheet.merge_range(3,9,4,9, 'Tanggal Transaksi', formatHeader)
        sheet.merge_range(3,10,4,10, 'Nomor Faktur', formatHeader)
        sheet.merge_range(3,11,4,11, 'Kode Batch', formatHeader)
        sheet.merge_range(3,12,3,14, 'Sarana', formatHeader)
        sheet.write(4, 12, 'Jumlah', formatHeader)
        sheet.write(4, 13, 'Kode Sarana', formatHeader)
        sheet.write(4, 14, 'Jumlah', formatHeader)
        sheet.merge_range(3,15,4,15, 'HJD (BOX)', formatHeader)

        # print(warehouse,datas.get('golongan_obat'))
        # xxx

        row = 5
        if warehouse and not datas.get('product_ids') and not datas.get('golongan_obat'):
            _query = """
                        select
                            f.nie as kode_obat,
                            f.name as nama_obat,
                            case 
                                when c.location_dest_id = b.lot_stock_id 
                                then date(g.scheduled_date  + interval '7 hours') else null
                            end as tanggal_terima,
                            case 
                                when c.location_dest_id = b.lot_stock_id 
                                then c.origin else ''
                            end as dokumen_penerima,
                            case 
                                when c.location_dest_id = b.lot_stock_id 
                                then f.industry_code else ''
                            end as kode_industri,
                            case 
                                when c.location_dest_id = b.lot_stock_id 
                                then f.sku else ''
                            end as kode_pbf,
                            case 
                                when c.location_dest_id = b.lot_stock_id 
                                then a.qty_done else 0
                            end as jumlah_masuk,
                            case 
                                when c.location_dest_id = b.lot_stock_id 
                                then (select name from stock_production_lot where id = a.lot_id) else ''
                            end as lot_id,
                            case 
                                when c.location_dest_id = b.lot_stock_id 
                                then date(a.expiration_date  + interval '7 hours') else null
                            end as expired_date,
                            case 
                                when c.location_id = b.lot_stock_id 
                                then date(g.scheduled_date  + interval '7 hours') else null
                            end as tanggal_transaksi,
                            case 
                                when c.location_id = b.lot_stock_id 
                                then c.origin else ''
                            end as nomor_faktur,
                            case 
                                when c.location_id = b.lot_stock_id 
                                then (select name from stock_production_lot where id = a.lot_id) else ''
                            end as batch_name,
                            case 
                                when c.location_id = b.lot_stock_id 
                                then a.qty_done else 0
                            end as jumlah_keluar,
                            case 
                                when c.location_id = b.lot_stock_id 
                                then i.no_izin_sarana else ''
                            end as no_sarana
                        from stock_move_line a
                            join stock_move c on c.id = a.move_id 
                            join stock_warehouse b on b.lot_stock_id in (c.location_dest_id,c.location_id)
                            left join purchase_order_line d on d.id = c.purchase_line_id 
                            left join sale_order_line h on h.id = c.sale_line_id 
                            join product_product e on e.id = a.product_id 
                            join product_template f on f.id = e.product_tmpl_id 
                            join stock_picking g on g.id = a.picking_id 
                            join res_partner i on i.id = g.partner_id 
                        where date(g."date") >= '{_start_date}'
                            and date(g."date") <= '{_end_date}'
                            and b.id = {_warehouse_id}
                            and a.state = 'done'
                            and g.picking_type_id_name in ('Receipts','Delivery Orders')
                            order by a.date asc
                    """.format(_start_date=start_date, _end_date=end_date,_warehouse_id=warehouse)

        elif warehouse and not datas.get('product_ids') and datas.get('golongan_obat'):
            _query = """
                        select
                            f.nie as kode_obat,
                            f.name as nama_obat,
                            case 
                                when c.location_dest_id = b.lot_stock_id 
                                then date(g.date_done) else null
                            end as tanggal_terima,
                            case 
                                when c.location_dest_id = b.lot_stock_id 
                                then c.origin else ''
                            end as dokumen_penerima,
                            case 
                                when c.location_dest_id = b.lot_stock_id 
                                then f.industry_code else ''
                            end as kode_industri,
                            case 
                                when a.location_dest_id = b.lot_stock_id 
                                then f.sku else ''
                            end as kode_pbf,
                            case 
                                when c.location_dest_id = b.lot_stock_id 
                                then a.qty_done else 0
                            end as jumlah_masuk,
                            case 
                                when c.location_dest_id = b.lot_stock_id 
                                then (select name from stock_production_lot where id = a.lot_id) else ''
                            end as lot_id,
                            case 
                                when c.location_dest_id = b.lot_stock_id 
                                then date(a.expiration_date) else null
                            end as expired_date,
                            case 
                                when c.location_id = b.lot_stock_id 
                                then date(g.date_done) else null
                            end as tanggal_transaksi,
                            case 
                                when c.location_id = b.lot_stock_id 
                                then c.origin else ''
                            end as nomor_faktur,
                            case 
                                when c.location_id = b.lot_stock_id 
                                then (select name from stock_production_lot where id = a.lot_id) else ''
                            end as batch_name,
                            case 
                                when c.location_id = b.lot_stock_id 
                                then a.qty_done else 0
                            end as jumlah_keluar,
                            case 
                                when c.location_id = b.lot_stock_id 
                                then i.no_izin_sarana else ''
                            end as no_sarana
                        from stock_move_line a
                            join stock_move c on c.id = a.move_id 
                            join stock_warehouse b on b.lot_stock_id in (c.location_dest_id,c.location_id)
                            left join purchase_order_line d on d.id = c.purchase_line_id 
                            left join sale_order_line h on h.id = c.sale_line_id 
                            join product_product e on e.id = a.product_id 
                            join product_template f on f.id = e.product_tmpl_id 
                            join stock_picking g on g.id = a.picking_id 
                            join res_partner i on i.id = g.partner_id 
                        where date(g."date") >= '{_start_date}'
                            and date(g."date") <= '{_end_date}'
                            and b.id = {_warehouse_id}
                            and a.state = 'done'
                            and g.picking_type_id_name in ('Receipts','Delivery Orders')
                            and f.jenis_obat = {_jenis_obat}
                            order by a.date asc
                    """.format(_start_date=start_date, _end_date=end_date, _warehouse_id=warehouse, _jenis_obat=datas.get('golongan_obat'))
        elif warehouse and datas.get('product_ids') and datas.get('golongan_obat'):
            print(warehouse,datas.get('golongan_obat'))
            product = datas.get('product_ids')
            product.append(0)
            product.append(0)
            products = tuple(datas.get('product_ids'))
            _query = """
                        select
                            f.nie as kode_obat,
                            f.name as nama_obat,
                            case 
                                when c.location_dest_id = b.lot_stock_id 
                                then date(g.date_done) else null
                            end as tanggal_terima,
                            case 
                                when c.location_dest_id = b.lot_stock_id 
                                then c.origin else ''
                            end as dokumen_penerima,
                            case 
                                when c.location_dest_id = b.lot_stock_id 
                                then f.industry_code else ''
                            end as kode_industri,
                            case 
                                when c.location_dest_id = b.lot_stock_id 
                                then f.sku else ''
                            end as kode_pbf,
                            case 
                                when c.location_dest_id = b.lot_stock_id 
                                then a.qty_done else 0
                            end as jumlah_masuk,
                            case 
                                when c.location_dest_id = b.lot_stock_id 
                                then (select name from stock_production_lot where id = a.lot_id) else ''
                            end as lot_id,
                            case 
                                when c.location_dest_id = b.lot_stock_id 
                                then date(a.expiration_date) else null
                            end as expired_date,
                            case 
                                when c.location_id = b.lot_stock_id 
                                then date(g.date_done) else null
                            end as tanggal_transaksi,
                            case 
                                when c.location_id = b.lot_stock_id 
                                then c.origin else ''
                            end as nomor_faktur,
                            case 
                                when c.location_id = b.lot_stock_id 
                                then (select name from stock_production_lot where id = a.lot_id) else ''
                            end as batch_name,
                            case 
                                when c.location_id = b.lot_stock_id 
                                then c.qty_done else 0
                            end as jumlah_keluar,
                            case 
                                when c.location_id = b.lot_stock_id 
                                then i.no_izin_sarana else ''
                            end as no_sarana
                        from stock_move_line a
                            join stock_move c on c.id = a.move_id 
                            join stock_warehouse b on b.lot_stock_id in (c.location_dest_id,c.location_id)
                            left join purchase_order_line d on d.id = c.purchase_line_id 
                            left join sale_order_line h on h.id = c.sale_line_id 
                            join product_product e on e.id = a.product_id 
                            join product_template f on f.id = e.product_tmpl_id 
                            join stock_picking g on g.id = a.picking_id 
                            join res_partner i on i.id = g.partner_id 
                        where date(g."date") >= '{_start_date}'
                            and date(g."date") <= '{_end_date}'
                            and b.id = {_warehouse_id}
                            and a.state = 'done'
                            and g.picking_type_id_name in ('Receipts','Delivery Orders')
                            and f.jenis_obat = {_jenis_obat}
                            and a.product_id in {_products}
                            order by a.date asc
                    """.format(_start_date=start_date, _end_date=end_date, _warehouse_id=warehouse, _jenis_obat=datas.get('golongan_obat'),_products=products)

        elif warehouse and datas.get('product_ids') and not datas.get('golongan_obat'):
            product = datas.get('product_ids')
            product.append(0)
            product.append(0)
            products = tuple(datas.get('product_ids'))
            _query = """
                        select
                            f.nie as kode_obat,
                            f.name as nama_obat,
                            case 
                                when c.location_dest_id = b.lot_stock_id 
                                then date(g.date_done) else null
                            end as tanggal_terima,
                            case 
                                when c.location_dest_id = b.lot_stock_id 
                                then c.origin else ''
                            end as dokumen_penerima,
                            case 
                                when c.location_dest_id = b.lot_stock_id 
                                then f.industry_code else ''
                            end as kode_industri,
                            case 
                                when c.location_dest_id = b.lot_stock_id 
                                then f.sku else ''
                            end as kode_pbf,
                            case 
                                when c.location_dest_id = b.lot_stock_id 
                                then a.qty_done else 0
                            end as jumlah_masuk,
                            case 
                                when c.location_dest_id = b.lot_stock_id 
                                then (select name from stock_production_lot where id = a.lot_id) else ''
                            end as lot_id,
                            case 
                                when c.location_dest_id = b.lot_stock_id 
                                then date(a.expiration_date) else null
                            end as expired_date,
                            case 
                                when c.location_id = b.lot_stock_id 
                                then date(g.date_done) else null
                            end as tanggal_transaksi,
                            case 
                                when c.location_id = b.lot_stock_id 
                                then c.origin else ''
                            end as nomor_faktur,
                            case 
                                when c.location_id = b.lot_stock_id 
                                then (select name from stock_production_lot where id = a.lot_id) else ''
                            end as batch_name,
                            case 
                                when c.location_id = b.lot_stock_id 
                                then a.qty_done else 0
                            end as jumlah_keluar,
                            case 
                                when c.location_id = b.lot_stock_id 
                                then i.no_izin_sarana else ''
                            end as no_sarana
                        from stock_move_line a
                            join stock_move c on c.id = a.move_id 
                            join stock_warehouse b on b.lot_stock_id in (c.location_dest_id,c.location_id)
                            left join purchase_order_line d on d.id = c.purchase_line_id 
                            left join sale_order_line h on h.id = c.sale_line_id 
                            join product_product e on e.id = a.product_id 
                            join product_template f on f.id = e.product_tmpl_id 
                            join stock_picking g on g.id = a.picking_id 
                            join res_partner i on i.id = g.partner_id 
                        where date(g."date") >= '{_start_date}'
                            and date(g."date") <= '{_end_date}'
                            and b.id = {_warehouse_id}
                            and a.state = 'done'
                            and g.picking_type_id_name in ('Receipts','Delivery Orders')
                            and a.product_id in {_products}
                            order by a.date asc
                    """.format(_start_date=start_date, _end_date=end_date, _warehouse_id=warehouse,_products=products)
        self._cr.execute(_query)
        check_data = self._cr.dictfetchall()
        for rec in check_data:
            sheet.write(row, 0, rec.get('kode_obat') or '', formatTabelLeft)
            sheet.write(row, 1, rec.get('nama_obat') or '', formatTabelLeft)
            ''' Pemasukan '''
            date_done = rec.get('tanggal_terima').strftime('%Y-%m-%d') if rec.get('tanggal_terima') else ''
            sheet.write(row, 2, date_done, formatTabel)
            sheet.write(row, 3, rec.get('dokumen_penerima') or '', formatTabel)
            sheet.write(row, 4, rec.get('kode_industri') or '', formatTabel)
            sheet.write(row, 5, rec.get('kode_pbf') or '', formatTabel)
            sheet.write(row, 6, rec.get('jumlah_masuk') or '', formatTabel)
            sheet.write(row, 7, rec.get('lot_id') or '', formatTabel)
            expiration_date = rec.get('expired_date').strftime('%Y-%m-%d') if rec.get('expired_date') else ''
            sheet.write(row, 8, expiration_date, formatTabel)
            ''' Pengeluaran '''
            tanggal_transaksi = rec.get('tanggal_transaksi').strftime('%Y-%m-%d') if rec.get('tanggal_transaksi') else ''
            sheet.write(row, 9, tanggal_transaksi, formatTabel)
            sheet.write(row, 10, rec.get('nomor_faktur') or '', formatTabel)
            sheet.write(row, 11, rec.get('batch_name') or '', formatTabel)
            sheet.write(row, 12, rec.get('jumlah_keluar') or '', formatTabel)
            sheet.write(row, 13, rec.get('no_sarana') or '', formatTabel)
            sheet.write(row, 14, '', formatTabel)
            sheet.write(row, 15, '', formatTabel)
            row += 1

        #
        # datas = data.get('form', {})
        # if datas:
        #     warehouse = datas.get('warehouse_id', False)
        #     location_ids = []
        #     if warehouse:
        #         warehouse_id = self.env['stock.warehouse'].sudo().browse(warehouse)
        #         # location_ids = self.env['stock.location'].sudo().search([('id', '=', warehouse_id.lot_stock_id.id)])
        #         # location_ids = self.env['stock.location'].sudo().search([('warehouse_id', '=', warehouse), ('usage', '=', 'internal')])
        #         location = self.env['stock.location'].sudo().browse(warehouse_id.lot_stock_id.id)
        #         product_move = self.env['stock.move.line'].sudo().search([
        #             '|',
        #             ('location_id', '=', location.id),
        #             ('location_dest_id', '=', location.id),
        #             ('date', '>=', datas.get('date_from')),
        #             ('date', '<=', datas.get('date_to')),
        #             ('state', '=', 'done'),
        #         ], order='date asc')
        #
        #         ## PRODUCT IDS ##
        #         if datas.get('product_ids'):
        #             products = tuple(datas.get('product_ids'))
        #             if products:
        #                 product_move = self.env['stock.move.line'].sudo().search([
        #                     '|',
        #                     ('location_id', '=', location.id),
        #                     ('location_dest_id', '=', location.id),
        #                     ('date', '>=', datas.get('date_from')),
        #                     ('date', '<=', datas.get('date_to')),
        #                     ('state', '=', 'done'),
        #                     ('product_id', 'in', products)
        #                 ], order='date asc')
        #
        #         row = 5
        #         for move in product_move:
        #             # print("golongan", datas.get('golongan_obat'), move.product_id.jenis_obat)
        #             if not datas.get('golongan_obat'):
        #                 if move.picking_id and move.picking_id.purchase_id and location.id == move.location_dest_id.id:
        #                     sheet.write(row, 0, move.product_id.nie or '', formatTabelLeft)
        #                     sheet.write(row, 1, move.product_id.name or '', formatTabelLeft)
        #                     ''' Pemasukan '''
        #                     date_done = move.picking_id.date_done.strftime('%Y-%m-%d') if move.picking_id.date_done else ''
        #                     sheet.write(row, 2, date_done, formatTabel)
        #                     sheet.write(row, 3, move.origin or '', formatTabel)
        #                     sheet.write(row, 4, move.product_id.industry_code or '', formatTabel)
        #                     sheet.write(row, 5, move.product_id.sku or '', formatTabel)
        #                     sheet.write(row, 6, move.qty_done or '', formatTabel)
        #                     sheet.write(row, 7, move.lot_id.name or '', formatTabel)
        #                     expiration_date = move.expiration_date.strftime('%Y-%m-%d') if move.expiration_date else ''
        #                     sheet.write(row, 8, expiration_date, formatTabel)
        #                     ''' Pengeluaran '''
        #                     sheet.write(row, 9, '', formatTabel)
        #                     sheet.write(row, 10, '', formatTabel)
        #                     sheet.write(row, 11, '', formatTabel)
        #                     sheet.write(row, 12, '', formatTabel)
        #                     sheet.write(row, 13, '', formatTabel)
        #                     sheet.write(row, 14, '', formatTabel)
        #                     sheet.write(row, 15, '', formatTabel)
        #                     row += 1
        #
        #                 elif move.picking_id and move.picking_id.sale_id and location.id == move.location_id.id:
        #                     sheet.write(row, 0, move.product_id.nie or '', formatTabelLeft)
        #                     sheet.write(row, 1, move.product_id.name or '', formatTabelLeft)
        #                     ''' Pemasukan '''
        #                     sheet.write(row, 2, '', formatTabel)
        #                     sheet.write(row, 3, '', formatTabel)
        #                     sheet.write(row, 4, '', formatTabel)
        #                     sheet.write(row, 5, '', formatTabel)
        #                     sheet.write(row, 6, '', formatTabel)
        #                     sheet.write(row, 7, '', formatTabel)
        #                     sheet.write(row, 8, '', formatTabel)
        #                     ''' Pengeluaran '''
        #                     date = move.date.strftime('%Y-%m-%d') if move.date else ''
        #                     sheet.write(row, 9, date, formatTabel)
        #                     sheet.write(row, 10, move.origin or '', formatTabel)
        #                     sheet.write(row, 11, move.lot_id.name or '', formatTabel)
        #                     sheet.write(row, 12, move.qty_done or '', formatTabel)
        #                     sheet.write(row, 13, move.picking_id.partner_id.no_izin_sarana or '', formatTabel)
        #                     sheet.write(row, 14, '', formatTabel)
        #                     sheet.write(row, 15, '', formatTabel)
        #                     row += 1
        #             elif datas.get('golongan_obat'):
        #                 if move.product_id.jenis_obat.id == datas.get('golongan_obat'):
        #                     if move.picking_id and move.picking_id.purchase_id and location.id == move.location_dest_id.id:
        #                         sheet.write(row, 0, move.product_id.nie or '', formatTabelLeft)
        #                         sheet.write(row, 1, move.product_id.name or '', formatTabelLeft)
        #                         ''' Pemasukan '''
        #                         date_done = move.picking_id.date_done.strftime('%Y-%m-%d') if move.picking_id.date_done else ''
        #                         sheet.write(row, 2, date_done, formatTabel)
        #                         sheet.write(row, 3, move.origin or '', formatTabel)
        #                         sheet.write(row, 4, move.product_id.industry_code or '', formatTabel)
        #                         sheet.write(row, 5, move.product_id.sku or '', formatTabel)
        #                         sheet.write(row, 6, move.qty_done or '', formatTabel)
        #                         sheet.write(row, 7, move.lot_id.name or '', formatTabel)
        #                         expiration_date = move.expiration_date.strftime('%Y-%m-%d') if move.expiration_date else ''
        #                         sheet.write(row, 8, expiration_date, formatTabel)
        #                         ''' Pengeluaran '''
        #                         sheet.write(row, 9, '', formatTabel)
        #                         sheet.write(row, 10, '', formatTabel)
        #                         sheet.write(row, 11, '', formatTabel)
        #                         sheet.write(row, 12, '', formatTabel)
        #                         sheet.write(row, 13, '', formatTabel)
        #                         sheet.write(row, 14, '', formatTabel)
        #                         sheet.write(row, 15, '', formatTabel)
        #                         row += 1
        #
        #                     elif move.picking_id and move.picking_id.sale_id and location.id == move.location_id.id:
        #                         sheet.write(row, 0, move.product_id.nie or '', formatTabelLeft)
        #                         sheet.write(row, 1, move.product_id.name or '', formatTabelLeft)
        #                         ''' Pemasukan '''
        #                         sheet.write(row, 2, '', formatTabel)
        #                         sheet.write(row, 3, '', formatTabel)
        #                         sheet.write(row, 4, '', formatTabel)
        #                         sheet.write(row, 5, '', formatTabel)
        #                         sheet.write(row, 6, '', formatTabel)
        #                         sheet.write(row, 7, '', formatTabel)
        #                         sheet.write(row, 8, '', formatTabel)
        #                         ''' Pengeluaran '''
        #                         date = move.date.strftime('%Y-%m-%d') if move.date else ''
        #                         sheet.write(row, 9, date, formatTabel)
        #                         sheet.write(row, 10, move.origin or '', formatTabel)
        #                         sheet.write(row, 11, move.lot_id.name or '', formatTabel)
        #                         sheet.write(row, 12, move.qty_done or '', formatTabel)
        #                         sheet.write(row, 13, move.picking_id.partner_id.no_izin_sarana or '', formatTabel)
        #                         sheet.write(row, 14, '', formatTabel)
        #                         sheet.write(row, 15, '', formatTabel)
        #                         row += 1


                

