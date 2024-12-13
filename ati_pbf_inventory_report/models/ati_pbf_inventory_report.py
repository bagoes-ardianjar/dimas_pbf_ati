from odoo import models, fields, api, _
from datetime import date, datetime
from odoo.exceptions import ValidationError

class ati_pbf_inventory_report(models.TransientModel):
    _name = 'ati.pbf.inventory.report'

    def func_print(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/pbf_inventory_report/%s' % (self.id),
            'target': 'new',
        }

    name = fields.Char(string='Name', default='Laporan Triwulan E-Report Kemenkes')
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    golongan_obat = fields.Many2one('jenis.obat', string='Golongan Obat')
    pbf_inventory_report_ids = fields.One2many('ati.pbf.inventory.report.line', 'pbf_inventory_report_id',string='Ati Pbf Inventory Report Ids')

    def func_insert_data_prewiew(self):
        vals_header = {
            "name": 'Laporan Triwulan E-Report Kemenkes',
            "start_date": self.start_date,
            "end_date": self.end_date,
            "golongan_obat": self.golongan_obat.id
        }
        new_header = self.env['ati.pbf.inventory.report'].sudo().create(vals_header)
        if self.golongan_obat.id == False:
            self._cr.execute("""(
                                select 
                                    nilai.kode_obat as kode_obat,
                                    nilai.nama_obat as nama_obat,
                                    nilai.product_id as product_id,
                                    nilai.kemasan as kemasan,
                                    nilai.f_name as supplier_name,
                                    nilai.h_name as customer_name,
                                    coalesce(sum(nilai.masuk_if),0) as masuk_if,
                                    nilai.kode_if as kode_if,
                                    coalesce(sum(nilai.masuk_pbf),0) as masuk_pbf,
                                    nilai.kode_pbf as kode_pbf,
                                    coalesce(sum(nilai.masuk_lainnya),0) as masuk_lainnya,
                                    coalesce(sum(nilai.masuk_adjustment),0) as masuk_adjustment,
                                    coalesce(sum(nilai.return_pemasukan),0) as return_pemasukan,
                                    coalesce(sum(nilai.pbf),0) as pbf,
                                    nilai.code_pbf as code_pbf,
                                    coalesce(sum(nilai.rs),0) as rs,
                                    coalesce(sum(nilai.apotek),0) as apotek,
                                    coalesce(sum(nilai.sarana_pemerintah),0) as sarana_pemerintah,
                                    coalesce(sum(nilai.puskesmas),0) as puskesmas,
                                    coalesce(sum(nilai.klinik),0) as klinik,
                                    coalesce(sum(nilai.toko_obat),0) as toko_obat,
                                    coalesce(sum(nilai.return_delivery_order),0) as return_delivery_order,
                                    coalesce(sum(nilai.lain),0) as lain,
                                    coalesce(nilai.hjd,0) as hjd,
                                    coalesce(nilai.stock_awal,0) as stock_awal
                                    from
                                    (select
                                    c.nie as kode_obat,
                                    c.name as nama_obat,
                                    a.product_id as product_id,
                                    c.kemasan as kemasan,
                                    f.name as f_name,
                                    h.name as h_name,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where x.id=a.id and f.name='IF') as masuk_if,
                                    case
                                        when f.name = 'IF' then e.code_bmp
                                        else Null
                                    end kode_if,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where x.id=a.id and f.name='PBF') as masuk_pbf,
                                    case
                                        when f.name = 'PBF' then e.code_bmp
                                        else Null
                                    end kode_pbf,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where x.id=a.id and f.name is null and g.name='Receipts') as masuk_lainnya,
                                    a.location_id as location_id,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    join stock_location y on y.id = x.location_id
                                    where x.id = a.id and y.name = 'Inventory adjustment' 
                                    and x.product_id = a.product_id) as masuk_adjustment,
                                    (select coalesce(sum(x.product_uom_qty), 0) from stock_move x 
                                    where g.name = 'Returns' and g.sequence_code = 'OUT'
                                    and x.id = a.id and x.product_id = a.product_id) as return_pemasukan,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where h.name = 'PBF' and x.id = a.id
                                    and x.product_id = a.product_id) as pbf,
                                    case
                                        when h.name = 'PBF' then e.code_customer
                                        else Null
                                    end code_pbf,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where lower(h.name) in ('rs','rumah sakit') and x.id = a.id
                                    and x.product_id = a.product_id) as rs,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where lower(h.name) in ('apotek','apotek cabang') and x.id = a.id
                                    and x.product_id = a.product_id) as apotek,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where lower(h.name) = 'sarana pemerintah' and x.id = a.id
                                    and x.product_id = a.product_id) as sarana_pemerintah,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where lower(h.name) = 'puskesmas' and x.id = a.id
                                    and x.product_id = a.product_id) as puskesmas,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where lower(h.name) = 'klinik' and x.id = a.id
                                    and x.product_id = a.product_id) as klinik,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where lower(h.name) = 'toko obat' and x.id = a.id
                                    and x.product_id = a.product_id) as toko_obat,
                                    (select coalesce(sum(x.product_uom_qty), 0) from stock_move x 
                                    where g.name = 'Return:Delivery Orders' and g.sequence_code = 'IN'
                                    and x.id = a.id and x.product_id = a.product_id) as return_delivery_order,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where lower(h.name) not in ('toko obat','klinik','puskesmas','sarana pemerintah','apotek cabang','apotek','rs','pbf','rumah sakit') and x.id = a.id and g.name <> 'Return:Delivery Orders'
                                    and x.product_id = a.product_id) as lain,
                                    i.value_float as hjd,
                                    (select data.qty_adjustment +data.qty_po + data.qty_so_return - data.qty_so - data.qty_po_return as stock_awal
                                    from
                                        (select
                                            (select coalesce(sum(x.qty_done), 0) from stock_move_line x 
                                                                                join stock_picking y on y.id = x.picking_id 
                                                                                join stock_picking_type z on z.id = y.picking_type_id 
                                                                                where x.product_id = m.product_id and z.name = 'Receipts'  and x.state = 'done' and date(x.create_date) < '{_start_date}') as qty_po,
                                            (select coalesce(sum(x.qty_done), 0) from stock_move_line x 
                                                                                join stock_picking y on y.id = x.picking_id 
                                                                                join stock_picking_type z on z.id = y.picking_type_id 
                                                                                where x.product_id = m.product_id and z.name = 'Delivery Orders'  and x.state = 'done' and date(x.create_date) < '{_start_date}') as qty_so,
                                            (select coalesce(sum(x.qty_done), 0) from stock_move_line x 
                                                                                join stock_picking y on y.id = x.picking_id 
                                                                                join stock_picking_type z on z.id = y.picking_type_id 
                                                                                where x.product_id = m.product_id and z.name = 'Returns'  and x.state = 'done' and date(x.create_date) < '{_start_date}') as qty_po_return,
                                            (select coalesce(sum(x.qty_done), 0) from stock_move_line x 
                                                                                join stock_location y on y.id = x.location_id 
                                                                                where x.product_id = m.product_id and y.name = 'Inventory adjustment' and date(x.date) < '{_start_date}') as qty_adjustment,
                                            (select coalesce(sum(x.qty_done), 0) from stock_move_line x 
                                                                                join stock_picking y on y.id = x.picking_id 
                                                                                join stock_picking_type z on z.id = y.picking_type_id 
                                                                                where x.product_id = m.product_id and z.name = 'Return:Delivery Orders'  and x.state = 'done' and date(x.create_date) < '{_start_date}') as qty_so_return									
                                        from stock_move_line m 
                                        join stock_picking n on n.id = m.picking_id
                                        join stock_picking_type o on o.id = n.picking_type_id 
                                        where m.product_id = a.product_id 
                                        and date(m.create_date) < '{_start_date}'
                                        group by m.product_id) as data)
                                    from stock_move a
                                    join product_product b on b.id = a.product_id
                                    join product_template c on c.id = b.product_tmpl_id 
                                    left join stock_picking d on d.id = a.picking_id
                                    left join res_partner e on e.id = d.partner_id 
                                    left join supplier_type f on f.id = e.supplier_type_id
                                    left join stock_picking_type g on g.id = a.picking_type_id
                                    left join customer_type h on h.id = e.customer_type_id
                                    join ir_property i on substring(res_id,1,15) = 'product.product' and coalesce(cast(substring(res_id,17) as integer),0) = a.product_id
                                    where a.state = 'done'
                                    and date(a.create_date) >= '{_start_date}' 
                                    and date(a.create_date) <= '{_end_date}')
                                    as nilai 
                                    group by nilai.kode_obat, 
                                    nilai.nama_obat,
                                    nilai.kemasan, 
                                    nilai.kode_if, 
                                    nilai.kode_pbf, 
                                    nilai.f_name,
                                    nilai.h_name,
                                    nilai.code_pbf,
                                    nilai.hjd,
                                    nilai.stock_awal,
                                    nilai.product_id
                                )""".format(_start_date=str(self.start_date), _end_date=str(self.end_date)))
        else:
            self._cr.execute("""(
                                select 
                                    nilai.kode_obat as kode_obat,
                                    nilai.nama_obat as nama_obat,
                                    nilai.product_id as product_id,
                                    nilai.kemasan as kemasan,
                                    nilai.f_name as supplier_name,
                                    nilai.h_name as customer_name,
                                    coalesce(sum(nilai.masuk_if),0) as masuk_if,
                                    nilai.kode_if as kode_if,
                                    coalesce(sum(nilai.masuk_pbf),0) as masuk_pbf,
                                    nilai.kode_pbf as kode_pbf,
                                    coalesce(sum(nilai.masuk_lainnya),0) as masuk_lainnya,
                                    coalesce(sum(nilai.masuk_adjustment),0) as masuk_adjustment,
                                    coalesce(sum(nilai.return_pemasukan),0) as return_pemasukan,
                                    coalesce(sum(nilai.pbf),0) as pbf,
                                    nilai.code_pbf as code_pbf,
                                    coalesce(sum(nilai.rs),0) as rs,
                                    coalesce(sum(nilai.apotek),0) as apotek,
                                    coalesce(sum(nilai.sarana_pemerintah),0) as sarana_pemerintah,
                                    coalesce(sum(nilai.puskesmas),0) as puskesmas,
                                    coalesce(sum(nilai.klinik),0) as klinik,
                                    coalesce(sum(nilai.toko_obat),0) as toko_obat,
                                    coalesce(sum(nilai.return_delivery_order),0) as return_delivery_order,
                                    coalesce(sum(nilai.lain),0) as lain,
                                    coalesce(nilai.hjd,0) as hjd,
                                    coalesce(nilai.stock_awal,0) as stock_awal
                                    from
                                    (select
                                    c.nie as kode_obat,
                                    c.name as nama_obat,
                                    a.product_id as product_id,
                                    c.kemasan as kemasan,
                                    f.name as f_name,
                                    h.name as h_name,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where x.id=a.id and f.name='IF') as masuk_if,
                                    case
                                        when f.name = 'IF' then e.code_bmp
                                        else Null
                                    end kode_if,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where x.id=a.id and f.name='PBF') as masuk_pbf,
                                    case
                                        when f.name = 'PBF' then e.code_bmp
                                        else Null
                                    end kode_pbf,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where x.id=a.id and f.name is null and g.name='Receipts') as masuk_lainnya,
                                    a.location_id as location_id,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    join stock_location y on y.id = x.location_id
                                    where x.id = a.id and y.name = 'Inventory adjustment' 
                                    and x.product_id = a.product_id) as masuk_adjustment,
                                    (select coalesce(sum(x.product_uom_qty), 0) from stock_move x 
                                    where g.name = 'Returns' and g.sequence_code = 'OUT'
                                    and x.id = a.id and x.product_id = a.product_id) as return_pemasukan,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where h.name = 'PBF' and x.id = a.id
                                    and x.product_id = a.product_id) as pbf,
                                    case
                                        when h.name = 'PBF' then e.code_customer
                                        else Null
                                    end code_pbf,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where lower(h.name) in ('rs','rumah sakit') and x.id = a.id
                                    and x.product_id = a.product_id) as rs,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where lower(h.name) in ('apotek','apotek cabang') and x.id = a.id
                                    and x.product_id = a.product_id) as apotek,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where lower(h.name) = 'sarana pemerintah' and x.id = a.id
                                    and x.product_id = a.product_id) as sarana_pemerintah,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where lower(h.name) = 'puskesmas' and x.id = a.id
                                    and x.product_id = a.product_id) as puskesmas,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where lower(h.name) = 'klinik' and x.id = a.id
                                    and x.product_id = a.product_id) as klinik,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where lower(h.name) = 'toko obat' and x.id = a.id
                                    and x.product_id = a.product_id) as toko_obat,
                                    (select coalesce(sum(x.product_uom_qty), 0) from stock_move x 
                                    where g.name = 'Return:Delivery Orders' and g.sequence_code = 'IN'
                                    and x.id = a.id and x.product_id = a.product_id) as return_delivery_order,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where lower(h.name) not in ('toko obat','klinik','puskesmas','sarana pemerintah','apotek cabang','apotek','rs','pbf','rumah sakit') and x.id = a.id and g.name <> 'Return:Delivery Orders'
                                    and x.product_id = a.product_id) as lain,
                                    i.value_float as hjd,
                                    (select data.qty_adjustment +data.qty_po + data.qty_so_return - data.qty_so - data.qty_po_return as stock_awal
                                    from
                                        (select
                                            (select coalesce(sum(x.qty_done), 0) from stock_move_line x 
                                                                                join stock_picking y on y.id = x.picking_id 
                                                                                join stock_picking_type z on z.id = y.picking_type_id 
                                                                                where x.product_id = m.product_id and z.name = 'Receipts'  and x.state = 'done' and date(x.create_date) < '{_start_date}') as qty_po,
                                            (select coalesce(sum(x.qty_done), 0) from stock_move_line x 
                                                                                join stock_picking y on y.id = x.picking_id 
                                                                                join stock_picking_type z on z.id = y.picking_type_id 
                                                                                where x.product_id = m.product_id and z.name = 'Delivery Orders'  and x.state = 'done' and date(x.create_date) < '{_start_date}') as qty_so,
                                            (select coalesce(sum(x.qty_done), 0) from stock_move_line x 
                                                                                join stock_picking y on y.id = x.picking_id 
                                                                                join stock_picking_type z on z.id = y.picking_type_id 
                                                                                where x.product_id = m.product_id and z.name = 'Returns'  and x.state = 'done' and date(x.create_date) < '{_start_date}') as qty_po_return,
                                            (select coalesce(sum(x.qty_done), 0) from stock_move_line x 
                                                                                join stock_location y on y.id = x.location_id 
                                                                                where x.product_id = m.product_id and y.name = 'Inventory adjustment' and date(x.date) < '{_start_date}') as qty_adjustment,
                                            (select coalesce(sum(x.qty_done), 0) from stock_move_line x 
                                                                                join stock_picking y on y.id = x.picking_id 
                                                                                join stock_picking_type z on z.id = y.picking_type_id 
                                                                                where x.product_id = m.product_id and z.name = 'Return:Delivery Orders'  and x.state = 'done' and date(x.create_date) < '{_start_date}') as qty_so_return									
                                        from stock_move_line m 
                                        join stock_picking n on n.id = m.picking_id
                                        join stock_picking_type o on o.id = n.picking_type_id 
                                        where m.product_id = a.product_id 
                                        and date(m.create_date) < '{_start_date}'
                                        group by m.product_id) as data)
                                    from stock_move a
                                    join product_product b on b.id = a.product_id
                                    join product_template c on c.id = b.product_tmpl_id 
                                    left join stock_picking d on d.id = a.picking_id
                                    left join res_partner e on e.id = d.partner_id 
                                    left join supplier_type f on f.id = e.supplier_type_id
                                    left join stock_picking_type g on g.id = a.picking_type_id
                                    left join customer_type h on h.id = e.customer_type_id
                                    join ir_property i on substring(res_id,1,15) = 'product.product' and coalesce(cast(substring(res_id,17) as integer),0) = a.product_id
                                    where a.state = 'done'
                                    and date(a.create_date) >= '{_start_date}' 
                                    and date(a.create_date) <= '{_end_date}' and b.jenis_obat = {_golongan_obat})
                                    as nilai 
                                    group by nilai.kode_obat, 
                                    nilai.nama_obat,
                                    nilai.kemasan, 
                                    nilai.kode_if, 
                                    nilai.kode_pbf, 
                                    nilai.f_name,
                                    nilai.h_name,
                                    nilai.code_pbf,
                                    nilai.hjd,
                                    nilai.stock_awal,
                                    nilai.product_id
                    )""".format(_start_date=str(self.start_date), _end_date=str(self.end_date), _golongan_obat=self.golongan_obat.id))
        data_preview = self._cr.dictfetchall()
        if len(data_preview) > 0:
            uid = self._uid
            ins_values = ",".join(["('{}',{},'{}',{},'{}',{},'{}',{},{},{},{},'{}',{},{},{},{},{},{},{},{},{},{},{},{})".format(
                data['kode_obat'] or '',
                data['product_id'] or '',
                data['kemasan'] or '',
                round(data['masuk_if'] or 0, 2),
                data['kode_if'] or '',
                round(data['masuk_pbf'] or 0, 2),
                data['kode_pbf'] or '',
                round(data['masuk_lainnya'] or 0, 2),
                round(data['masuk_adjustment'] or 0, 2),
                round(data['return_pemasukan'] or 0, 2),
                round(data['pbf'] or 0, 2),
                data['code_pbf'] or '',
                round(data['rs'] or 0, 2),
                round(data['apotek'] or 0, 2),
                round(data['sarana_pemerintah'] or 0, 2),
                round(data['puskesmas'] or 0, 2),
                round(data['klinik'] or 0, 2),
                round(data['toko_obat'] or 0, 2),
                round(data['return_delivery_order'] or 0, 2),
                round(data['lain'] or 0, 2),
                round(data['hjd'] or 0, 2),
                round(data['stock_awal'] or 0, 2),
                uid,
                new_header.id
                # data['company_id'] or '',
                # data['picking_type_id'] or '',
                # data['warehouse_id'] or '',
                # data['product_category_id'] or ''
            ) for data in data_preview])
            ins_query = "insert into ati_pbf_inventory_report_line (kode_obat,product_id, kemasan," \
                        "masuk_if,kode_if,masuk_pbf,kode_pbf,masuk_lainnya,masuk_adjustment,return_pemasukan,pbf,code_pbf,rs," \
                        "apotek,sarana_pemerintah,puskesmas,klinik,toko_obat,return_delivery_order,lain,hjd,stock_awal," \
                        "create_uid,pbf_inventory_report_id) values {_values}".format(_values=ins_values)
            self._cr.execute(ins_query)
            self._cr.commit()

        form_view_id = self.env['ir.model.data']._xmlid_to_res_id('ati_pbf_inventory_report.ati_pbf_inventory_form_view_id')
        return {
            'name': new_header.name,
            'view_type': 'form',
            'view_mode': 'form',
            'type': 'ir.actions.act_window',
            'res_model': 'ati.pbf.inventory.report',
            'views': [[form_view_id, 'form']],
            'res_id': new_header.id
        }



    def func_cancel(self):
        form_view_id = self.env['ir.model.data']._xmlid_to_res_id('ati_pbf_inventory_report.ati_pbf_inventory_report_wizard_view_id')
        return {
            'name': 'Laporan Triwulan E-Report Kemenkes',
            'view_type': 'form',
            'view_mode': 'form',
            'type': 'ir.actions.act_window',
            'res_model': 'ati.pbf.inventory.report',
            'views': [[form_view_id, 'form']],
            'target': 'new',
        }

    def func_print(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/pbf_inventory_report/%s' % (self.id),
            'target': 'new',
        }

    name = fields.Char(string='Name', default='Laporan Triwulan E-Report Kemenkes')
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    golongan_obat = fields.Many2one('jenis.obat', string='Golongan Obat')
    pbf_inventory_report_ids = fields.One2many('ati.pbf.inventory.report.line', 'pbf_inventory_report_id',
                                               string='Ati Pbf Inventory Report Ids')

    def func_print_excel(self):
        vals_header = {
            "name": 'Laporan Triwulan E-Report Kemenkes',
            "start_date": self.start_date,
            "end_date": self.end_date,
            "golongan_obat": self.golongan_obat.id
        }
        new_header = self.env['ati.pbf.inventory.report'].sudo().create(vals_header)
        if self.golongan_obat.id == False:
            self._cr.execute("""(
                            select 
                                    nilai.kode_obat as kode_obat,
                                    nilai.nama_obat as nama_obat,
                                    nilai.product_id as product_id,
                                    nilai.kemasan as kemasan,
                                    nilai.f_name as supplier_name,
                                    nilai.h_name as customer_name,
                                    coalesce(sum(nilai.masuk_if),0) as masuk_if,
                                    nilai.kode_if as kode_if,
                                    coalesce(sum(nilai.masuk_pbf),0) as masuk_pbf,
                                    nilai.kode_pbf as kode_pbf,
                                    coalesce(sum(nilai.masuk_lainnya),0) as masuk_lainnya,
                                    coalesce(sum(nilai.masuk_adjustment),0) as masuk_adjustment,
                                    coalesce(sum(nilai.return_pemasukan),0) as return_pemasukan,
                                    coalesce(sum(nilai.pbf),0) as pbf,
                                    nilai.code_pbf as code_pbf,
                                    coalesce(sum(nilai.rs),0) as rs,
                                    coalesce(sum(nilai.apotek),0) as apotek,
                                    coalesce(sum(nilai.sarana_pemerintah),0) as sarana_pemerintah,
                                    coalesce(sum(nilai.puskesmas),0) as puskesmas,
                                    coalesce(sum(nilai.klinik),0) as klinik,
                                    coalesce(sum(nilai.toko_obat),0) as toko_obat,
                                    coalesce(sum(nilai.return_delivery_order),0) as return_delivery_order,
                                    coalesce(sum(nilai.lain),0) as lain,
                                    coalesce(nilai.hjd,0) as hjd,
                                    coalesce(nilai.stock_awal,0) as stock_awal
                                    from
                                    (select
                                    c.nie as kode_obat,
                                    c.name as nama_obat,
                                    a.product_id as product_id,
                                    c.kemasan as kemasan,
                                    f.name as f_name,
                                    h.name as h_name,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where x.id=a.id and f.name='IF') as masuk_if,
                                    case
                                        when f.name = 'IF' then e.code_bmp
                                        else Null
                                    end kode_if,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where x.id=a.id and f.name='PBF') as masuk_pbf,
                                    case
                                        when f.name = 'PBF' then e.code_bmp
                                        else Null
                                    end kode_pbf,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where x.id=a.id and f.name is null and g.name='Receipts') as masuk_lainnya,
                                    a.location_id as location_id,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    join stock_location y on y.id = x.location_id
                                    where x.id = a.id and y.name = 'Inventory adjustment' 
                                    and x.product_id = a.product_id) as masuk_adjustment,
                                    (select coalesce(sum(x.product_uom_qty), 0) from stock_move x 
                                    where g.name = 'Returns' and g.sequence_code = 'OUT'
                                    and x.id = a.id and x.product_id = a.product_id) as return_pemasukan,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where h.name = 'PBF' and x.id = a.id
                                    and x.product_id = a.product_id) as pbf,
                                    case
                                        when h.name = 'PBF' then e.code_customer
                                        else Null
                                    end code_pbf,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where lower(h.name) in ('rs','rumah sakit') and x.id = a.id
                                    and x.product_id = a.product_id) as rs,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where lower(h.name) in ('apotek','apotek cabang') and x.id = a.id
                                    and x.product_id = a.product_id) as apotek,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where lower(h.name) = 'sarana pemerintah' and x.id = a.id
                                    and x.product_id = a.product_id) as sarana_pemerintah,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where lower(h.name) = 'puskesmas' and x.id = a.id
                                    and x.product_id = a.product_id) as puskesmas,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where lower(h.name) = 'klinik' and x.id = a.id
                                    and x.product_id = a.product_id) as klinik,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where lower(h.name) = 'toko obat' and x.id = a.id
                                    and x.product_id = a.product_id) as toko_obat,
                                    (select coalesce(sum(x.product_uom_qty), 0) from stock_move x 
                                    where g.name = 'Return:Delivery Orders' and g.sequence_code = 'IN'
                                    and x.id = a.id and x.product_id = a.product_id) as return_delivery_order,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where lower(h.name) not in ('toko obat','klinik','puskesmas','sarana pemerintah','apotek cabang','apotek','rs','pbf','rumah sakit') and x.id = a.id and g.name <> 'Return:Delivery Orders'
                                    and x.product_id = a.product_id) as lain,
                                    i.value_float as hjd,
                                    (select data.qty_adjustment +data.qty_po + data.qty_so_return - data.qty_so - data.qty_po_return as stock_awal
                                    from
                                        (select
                                            (select coalesce(sum(x.qty_done), 0) from stock_move_line x 
                                                                                join stock_picking y on y.id = x.picking_id 
                                                                                join stock_picking_type z on z.id = y.picking_type_id 
                                                                                where x.product_id = m.product_id and z.name = 'Receipts'  and x.state = 'done' and date(x.create_date) < '{_start_date}') as qty_po,
                                            (select coalesce(sum(x.qty_done), 0) from stock_move_line x 
                                                                                join stock_picking y on y.id = x.picking_id 
                                                                                join stock_picking_type z on z.id = y.picking_type_id 
                                                                                where x.product_id = m.product_id and z.name = 'Delivery Orders'  and x.state = 'done' and date(x.create_date) < '{_start_date}') as qty_so,
                                            (select coalesce(sum(x.qty_done), 0) from stock_move_line x 
                                                                                join stock_picking y on y.id = x.picking_id 
                                                                                join stock_picking_type z on z.id = y.picking_type_id 
                                                                                where x.product_id = m.product_id and z.name = 'Returns'  and x.state = 'done' and date(x.create_date) < '{_start_date}') as qty_po_return,
                                            (select coalesce(sum(x.qty_done), 0) from stock_move_line x 
                                                                                join stock_location y on y.id = x.location_id 
                                                                                where x.product_id = m.product_id and y.name = 'Inventory adjustment' and date(x.date) < '{_start_date}') as qty_adjustment,
                                            (select coalesce(sum(x.qty_done), 0) from stock_move_line x 
                                                                                join stock_picking y on y.id = x.picking_id 
                                                                                join stock_picking_type z on z.id = y.picking_type_id 
                                                                                where x.product_id = m.product_id and z.name = 'Return:Delivery Orders'  and x.state = 'done' and date(x.create_date) < '{_start_date}') as qty_so_return									
                                        from stock_move_line m 
                                        join stock_picking n on n.id = m.picking_id
                                        join stock_picking_type o on o.id = n.picking_type_id 
                                        where m.product_id = a.product_id 
                                        and date(m.create_date) < '{_start_date}'
                                        group by m.product_id) as data)
                                    from stock_move a
                                    join product_product b on b.id = a.product_id
                                    join product_template c on c.id = b.product_tmpl_id 
                                    left join stock_picking d on d.id = a.picking_id
                                    left join res_partner e on e.id = d.partner_id 
                                    left join supplier_type f on f.id = e.supplier_type_id
                                    left join stock_picking_type g on g.id = a.picking_type_id
                                    left join customer_type h on h.id = e.customer_type_id
                                    join ir_property i on substring(res_id,1,15) = 'product.product' and coalesce(cast(substring(res_id,17) as integer),0) = a.product_id
                                    where a.state = 'done'
                                    and date(a.create_date) >= '{_start_date}' 
                                    and date(a.create_date) <= '{_end_date}')
                                    as nilai 
                                    group by nilai.kode_obat, 
                                    nilai.nama_obat,
                                    nilai.kemasan, 
                                    nilai.kode_if, 
                                    nilai.kode_pbf, 
                                    nilai.f_name,
                                    nilai.h_name,
                                    nilai.code_pbf,
                                    nilai.hjd,
                                    nilai.stock_awal,
                                    nilai.product_id
                                        )""".format(_start_date=str(self.start_date), _end_date=str(self.end_date)))
        else:
            self._cr.execute("""(
                                select 
                                    nilai.kode_obat as kode_obat,
                                    nilai.nama_obat as nama_obat,
                                    nilai.product_id as product_id,
                                    nilai.kemasan as kemasan,
                                    nilai.f_name as supplier_name,
                                    nilai.h_name as customer_name,
                                    coalesce(sum(nilai.masuk_if),0) as masuk_if,
                                    nilai.kode_if as kode_if,
                                    coalesce(sum(nilai.masuk_pbf),0) as masuk_pbf,
                                    nilai.kode_pbf as kode_pbf,
                                    coalesce(sum(nilai.masuk_lainnya),0) as masuk_lainnya,
                                    coalesce(sum(nilai.masuk_adjustment),0) as masuk_adjustment,
                                    coalesce(sum(nilai.return_pemasukan),0) as return_pemasukan,
                                    coalesce(sum(nilai.pbf),0) as pbf,
                                    nilai.code_pbf as code_pbf,
                                    coalesce(sum(nilai.rs),0) as rs,
                                    coalesce(sum(nilai.apotek),0) as apotek,
                                    coalesce(sum(nilai.sarana_pemerintah),0) as sarana_pemerintah,
                                    coalesce(sum(nilai.puskesmas),0) as puskesmas,
                                    coalesce(sum(nilai.klinik),0) as klinik,
                                    coalesce(sum(nilai.toko_obat),0) as toko_obat,
                                    coalesce(sum(nilai.return_delivery_order),0) as return_delivery_order,
                                    coalesce(sum(nilai.lain),0) as lain,
                                    coalesce(nilai.hjd,0) as hjd,
                                    coalesce(nilai.stock_awal,0) as stock_awal
                                    from
                                    (select
                                    c.nie as kode_obat,
                                    c.name as nama_obat,
                                    a.product_id as product_id,
                                    c.kemasan as kemasan,
                                    f.name as f_name,
                                    h.name as h_name,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where x.id=a.id and f.name='IF') as masuk_if,
                                    case
                                        when f.name = 'IF' then e.code_bmp
                                        else Null
                                    end kode_if,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where x.id=a.id and f.name='PBF') as masuk_pbf,
                                    case
                                        when f.name = 'PBF' then e.code_bmp
                                        else Null
                                    end kode_pbf,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where x.id=a.id and f.name is null and g.name='Receipts') as masuk_lainnya,
                                    a.location_id as location_id,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    join stock_location y on y.id = x.location_id
                                    where x.id = a.id and y.name = 'Inventory adjustment' 
                                    and x.product_id = a.product_id) as masuk_adjustment,
                                    (select coalesce(sum(x.product_uom_qty), 0) from stock_move x 
                                    where g.name = 'Returns' and g.sequence_code = 'OUT'
                                    and x.id = a.id and x.product_id = a.product_id) as return_pemasukan,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where h.name = 'PBF' and x.id = a.id
                                    and x.product_id = a.product_id) as pbf,
                                    case
                                        when h.name = 'PBF' then e.code_customer
                                        else Null
                                    end code_pbf,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where lower(h.name) in ('rs','rumah sakit') and x.id = a.id
                                    and x.product_id = a.product_id) as rs,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where lower(h.name) in ('apotek','apotek cabang') and x.id = a.id
                                    and x.product_id = a.product_id) as apotek,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where lower(h.name) = 'sarana pemerintah' and x.id = a.id
                                    and x.product_id = a.product_id) as sarana_pemerintah,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where lower(h.name) = 'puskesmas' and x.id = a.id
                                    and x.product_id = a.product_id) as puskesmas,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where lower(h.name) = 'klinik' and x.id = a.id
                                    and x.product_id = a.product_id) as klinik,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where lower(h.name) = 'toko obat' and x.id = a.id
                                    and x.product_id = a.product_id) as toko_obat,
                                    (select coalesce(sum(x.product_uom_qty), 0) from stock_move x 
                                    where g.name = 'Return:Delivery Orders' and g.sequence_code = 'IN'
                                    and x.id = a.id and x.product_id = a.product_id) as return_delivery_order,
                                    (select coalesce(sum(x.product_uom_qty),0) from stock_move x
                                    where lower(h.name) not in ('toko obat','klinik','puskesmas','sarana pemerintah','apotek cabang','apotek','rs','pbf','rumah sakit') and x.id = a.id and g.name <> 'Return:Delivery Orders'
                                    and x.product_id = a.product_id) as lain,
                                    i.value_float as hjd,
                                    (select data.qty_adjustment +data.qty_po + data.qty_so_return - data.qty_so - data.qty_po_return as stock_awal
                                    from
                                        (select
                                            (select coalesce(sum(x.qty_done), 0) from stock_move_line x 
                                                                                join stock_picking y on y.id = x.picking_id 
                                                                                join stock_picking_type z on z.id = y.picking_type_id 
                                                                                where x.product_id = m.product_id and z.name = 'Receipts'  and x.state = 'done' and date(x.create_date) < '{_start_date}') as qty_po,
                                            (select coalesce(sum(x.qty_done), 0) from stock_move_line x 
                                                                                join stock_picking y on y.id = x.picking_id 
                                                                                join stock_picking_type z on z.id = y.picking_type_id 
                                                                                where x.product_id = m.product_id and z.name = 'Delivery Orders'  and x.state = 'done' and date(x.create_date) < '{_start_date}') as qty_so,
                                            (select coalesce(sum(x.qty_done), 0) from stock_move_line x 
                                                                                join stock_picking y on y.id = x.picking_id 
                                                                                join stock_picking_type z on z.id = y.picking_type_id 
                                                                                where x.product_id = m.product_id and z.name = 'Returns'  and x.state = 'done' and date(x.create_date) < '{_start_date}') as qty_po_return,
                                            (select coalesce(sum(x.qty_done), 0) from stock_move_line x 
                                                                                join stock_location y on y.id = x.location_id 
                                                                                where x.product_id = m.product_id and y.name = 'Inventory adjustment' and date(x.date) < '{_start_date}') as qty_adjustment,
                                            (select coalesce(sum(x.qty_done), 0) from stock_move_line x 
                                                                                join stock_picking y on y.id = x.picking_id 
                                                                                join stock_picking_type z on z.id = y.picking_type_id 
                                                                                where x.product_id = m.product_id and z.name = 'Return:Delivery Orders'  and x.state = 'done' and date(x.create_date) < '{_start_date}') as qty_so_return									
                                        from stock_move_line m 
                                        join stock_picking n on n.id = m.picking_id
                                        join stock_picking_type o on o.id = n.picking_type_id 
                                        where m.product_id = a.product_id 
                                        and date(m.create_date) < '{_start_date}'
                                        group by m.product_id) as data)
                                    from stock_move a
                                    join product_product b on b.id = a.product_id
                                    join product_template c on c.id = b.product_tmpl_id 
                                    left join stock_picking d on d.id = a.picking_id
                                    left join res_partner e on e.id = d.partner_id 
                                    left join supplier_type f on f.id = e.supplier_type_id
                                    left join stock_picking_type g on g.id = a.picking_type_id
                                    left join customer_type h on h.id = e.customer_type_id
                                    join ir_property i on substring(res_id,1,15) = 'product.product' and coalesce(cast(substring(res_id,17) as integer),0) = a.product_id
                                    where a.state = 'done'
                                    and date(a.create_date) >= '{_start_date}' 
                                    and date(a.create_date) <= '{_end_date}' and b.jenis_obat = {_golongan_obat})
                                    as nilai 
                                    group by nilai.kode_obat, 
                                    nilai.nama_obat,
                                    nilai.kemasan, 
                                    nilai.kode_if, 
                                    nilai.kode_pbf, 
                                    nilai.f_name,
                                    nilai.h_name,
                                    nilai.code_pbf,
                                    nilai.hjd,
                                    nilai.stock_awal,
                                    nilai.product_id
                            )""".format(_start_date=str(self.start_date), _end_date=str(self.end_date),
                                        _golongan_obat=self.golongan_obat.id))
        data_preview = self._cr.dictfetchall()
        if len(data_preview) > 0:
            uid = self._uid
            ins_values = ",".join(
                ["('{}',{},'{}',{},'{}',{},'{}',{},{},{},{},'{}',{},{},{},{},{},{},{},{},{},{},{},{})".format(
                    data['kode_obat'] or '',
                    data['product_id'] or '',
                    data['kemasan'] or '',
                    round(data['masuk_if'] or 0, 2),
                    data['kode_if'] or '',
                    round(data['masuk_pbf'] or 0, 2),
                    data['kode_pbf'] or '',
                    round(data['masuk_lainnya'] or 0, 2),
                    round(data['masuk_adjustment'] or 0, 2),
                    round(data['return_pemasukan'] or 0, 2),
                    round(data['pbf'] or 0, 2),
                    data['code_pbf'] or '',
                    round(data['rs'] or 0, 2),
                    round(data['apotek'] or 0, 2),
                    round(data['sarana_pemerintah'] or 0, 2),
                    round(data['puskesmas'] or 0, 2),
                    round(data['klinik'] or 0, 2),
                    round(data['toko_obat'] or 0, 2),
                    round(data['return_delivery_order'] or 0, 2),
                    round(data['lain'] or 0, 2),
                    round(data['hjd'] or 0, 2),
                    round(data['stock_awal'] or 0, 2),
                    uid,
                    new_header.id
                ) for data in data_preview])
            ins_query = "insert into ati_pbf_inventory_report_line (kode_obat,product_id, kemasan," \
                        "masuk_if,kode_if,masuk_pbf,kode_pbf,masuk_lainnya,masuk_adjustment,return_pemasukan,pbf,code_pbf,rs," \
                        "apotek,sarana_pemerintah,puskesmas,klinik,toko_obat,return_delivery_order,lain,hjd,stock_awal," \
                        "create_uid,pbf_inventory_report_id) values {_values}".format(
                _values=ins_values)
            self._cr.execute(ins_query)
            self._cr.commit()
        return {
            'type': 'ir.actions.act_url',
            'url': '/pbf_inventory_report/%s' % (new_header.id),
            'target': 'new',
        }


class ati_pbf_inventory_report_line(models.TransientModel):
    _name = 'ati.pbf.inventory.report.line'

    # def get_stock_awal(self):
    #     for this in self:
    #         company = "{" + str(this.company_id.id) + "}"
    #         product = "{" + str(this.product_id.id) + "}"
    #         category = "{" + str(this.product_category_id.id) + "}"
    #         warehouse = "{" + str(this.warehouse_id.id) + "}"
    #         start_date = "{" + str(this.start_date) + "}"
    #         end_date = "{" + str(this.end_date) + "}"
    #         if this.company_id.id != False and this.product_id.id != False and this.product_category_id.id != False and this.warehouse_id.id != False and this.start_date != False and this.end_date != False:
    #             query = """
    #                         Select coalesce(sum(opening_stock),0) from get_products_stock_movements('%s','%s','%s','%s','%s','%s')
    #                     """ % (company, product, category, warehouse, start_date, end_date)
    #             self._cr.execute(query)
    #             stock_awal = [x[0] for x in self._cr.fetchall()]
    #             if len(stock_awal) > 0:
    #                 this.stock_awal = stock_awal[0]
    #             else:
    #                 this.stock_awal = 0
    #         else:
    #             this.stock_awal = 0


    pbf_inventory_report_id = fields.Many2one('ati.pbf.inventory.report', string='Ati Pbf Inventory Report Id')
    kode_obat = fields.Char(string='Kode Obat (NIE)')
    product_id = fields.Many2one('product.product', string='Product Id')
    company_id = fields.Many2one('res.company')
    picking_type_id = fields.Many2one('stock.picking.type')
    warehouse_id = fields.Many2one('stock.warehouse')
    product_category_id = fields.Many2one('product.category')
    start_date = fields.Date(related='pbf_inventory_report_id.start_date')
    end_date = fields.Date(related='pbf_inventory_report_id.end_date')
    nama_obat = fields.Char(string='Nama Obat',related='product_id.name')
    kemasan = fields.Char(string='Kemasan')
    # stock_awal = fields.Float(string='Stock Awal', compute=get_stock_awal)
    stock_awal = fields.Float(string='Stock Awal')
    masuk_if = fields.Float(string='Masuk IF', default=0.0)
    kode_if = fields.Char(string='Kode IF')
    masuk_pbf = fields.Float(string='Masuk PBF', default=0.0)
    kode_pbf = fields.Char(string='Kode PBF')
    masuk_lainnya = fields.Float(string='Masuk Lainnya', default=0.0)
    masuk_adjustment = fields.Float(string='Masuk Lainnya', default=0.0)
    return_pemasukan = fields.Float(string='Retur', default=0.0)
    pbf = fields.Float(string='Keluar PBF')
    code_pbf = fields.Char(string='Kode PBF')
    rs = fields.Float(string='RS')
    apotek = fields.Float(string='Apotek')
    sarana_pemerintah = fields.Float(string='Sarana Pemerintah')
    puskesmas = fields.Float(string='Puskesmas')
    klinik = fields.Float(string='Klinik')
    toko_obat = fields.Float(string='Toko Obat')
    return_delivery_order = fields.Float(string='Retur')
    lain = fields.Float(string='Lainnya')
    hjd = fields.Float(string='HJDS')



# class ati_pbf_inventory_preview(models.Model):
#     _name = 'ati.pbf.inventory.preview'
#
#     def func_print(self):
#         pass
#
#     name = fields.Char(string='Name', default='Laporan Triwulan E-Report Kemenkes')
#     start_date = fields.Date(string='Start Date')
#     end_date = fields.Date(string='End Date')
#     inventory_preview_ids = fields.One2many('ati.pbf.inventory.preview.line', 'inventory_preview_id', string='Inventory Preview Ids' )
#
#
# class ati_pbf_inventory_preview_line(models.Model):
#     _name = 'ati.pbf.inventory.preview.line'
#
#     inventory_preview_id = fields.Many2one('ati.pbf.inventory.preview', string='Inventory Preview Id')
#     kode_obat = fields.Char(string='Kode Obat (NIE)')
#     nama_obat = fields.Char(string='Nama Obat')
#     kemasan = fields.Char(string='Kemasan')
#     stock_awal = fields.Float(string='Stock Awal', default=0.0)
#     masuk_if = fields.Float(string='Masuk IF', default=0.0)
#     kode_if = fields.Char(string='Kode IF')
#     masuk_pbf = fields.Float(string='Masuk PBF', default=0.0)
#     kode_pbf = fields.Char(string='Kode PBF')
#     returns = fields.Float(string='Retur', default=0.0)
#     pbf = fields.Float(string='Keluar PBF')
#     code_pbf = fields.Char(string='Kode PBF')
#     rs = fields.Char(string='RS')
#     apotek = fields.Float(string='Apotek')
#     sarana_pemerintah = fields.Float(string='Sarana Pemerintah')
#     puskesmas = fields.Float(string='Puskesmas')
#     klinik = fields.Float(string='Klinik')
#     toko_obat = fields.Float(string='Toko Obat')
#     return_delivery_order = fields.Float(string='Retur')
#     lain = fields.Char(string='Lainnya')
