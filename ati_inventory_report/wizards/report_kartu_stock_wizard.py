from odoo import fields, models, api, _
from odoo.exceptions import UserError

from datetime import datetime as dt, timedelta

class ReportKartuStock(models.TransientModel):
    _name = 'report.kartu.stock'
    _description = 'Report Kartu Stock'

    start_date = fields.Datetime(string='Start date')
    end_date = fields.Datetime(string='End date')
    warehouse_id = fields.Many2one('stock.warehouse', string='From Warehouse')
    product_id = fields.Many2one('product.product', domain="[('activate_product', '=', True)]")
    user_id = fields.Many2one('res.users', string='User', readonly=True, change_default=True, index=True, default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string='Company', readonly=True, change_default=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, default=lambda self: self.env.company.currency_id.id)

    def download_report(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'report.kartu.stock'
        datas['form'] = self.read()[0]
        datas['form']['display_name'] = 'Report Kartu Stock'
        if 'product_name' not in datas['form']:
            datas['form']['product_name'] = self.product_id.name
        if 'wh_name' not in datas['form']:
            datas['form']['wh_name'] = self.warehouse_id.name
        if 'uom_name' not in datas['form']:
            datas['form']['uom_name'] = self.product_id.uom_name
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        return self.env.ref('ati_inventory_report.kartu_stock').report_action(self, data=datas)

    def view_report_pdf(self):
        return self.env['ir.actions.report'].search([('name', '=', 'Report HTML Kartu Stock')], limit=1).report_action(self)

    def _get_report_kartu_stock(self):
        qty_akhir = 0
        location_id = self.warehouse_id
        start_date_dt = dt.strptime(str(self.start_date), "%Y-%m-%d %H:%M:%S")
        end_date_dt = dt.strptime(str(self.end_date), "%Y-%m-%d %H:%M:%S")
        total_in_qty = 0
        total_out_qty = 0
        
        hpp = 0
        hpp_satuan = 0
        hpp_satuan_so = 0
        line_sub_total = 0
        product_qty = 0

        list_hpp = []

        # svl_obj = self.env['stock.valuation.layer'].search([('product_id', 'in', self.product_id.ids),
        #                                                     ('stock_move_id.purchase_line_id', '!=', False),
        #                                                     ('stock_move_id.sale_line_id', '=', False)])

        svl_obj = self.env['stock.valuation.layer'].search([('product_id', 'in', self.product_id.ids),])
        # for svl in svl_obj:
        #     line_sub_total += svl.value
        #     product_qty += svl.quantity
        #     hpp = line_sub_total / product_qty
        #     print('hpp',hpp)
        #     date = svl.create_date + timedelta(hours=7)
        #     create_date = date.strftime('%Y-%m-%d %H:%M:%S')
        #     list_hpp.append({
        #         'date': create_date,
        #         'hpp': hpp if hpp != 0 else svl.product_id.product_tmpl_id.harga_awal_ga
        #     })

        new_dict_data = {}
        for svl in svl_obj:
            if (svl.stock_move_id.purchase_line_id.id != False and svl.stock_move_id.sale_line_id.id == False) or (svl.stock_move_id.purchase_line_id.id == False and svl.stock_move_id.sale_line_id.id != False):
                line_sub_total += svl.value
                product_qty += svl.quantity
                # hpp = line_sub_total / product_qty
                hpp = svl.product_id.product_tmpl_id.standard_price
                date = svl.create_date + timedelta(hours=7)
                create_date = date.strftime('%Y-%m-%d %H:%M:%S')
                list_hpp.append({
                    'date': create_date,
                    'hpp': hpp if hpp != 0 else svl.product_id.product_tmpl_id.harga_awal_ga
                })
                if svl.stock_move_id.id not in new_dict_data:
                    new_dict_data[svl.stock_move_id.id] = hpp if hpp != 0 else svl.product_id.product_tmpl_id.harga_awal_ga
            else:
                date = svl.create_date + timedelta(hours=7)
                create_date = date.strftime('%Y-%m-%d %H:%M:%S')
                list_hpp.append({
                    'date': create_date,
                    'hpp': svl.product_id.product_tmpl_id.harga_awal_ga
                })
                if svl.stock_move_id.id not in new_dict_data:
                    new_dict_data[svl.stock_move_id.id] = svl.product_id.product_tmpl_id.harga_awal_ga

        # sm = self.env['stock.move'].search(['|',
        #     ('location_id', 'in', location_id.lot_stock_id.ids),
        #     ('location_dest_id', 'in', location_id.lot_stock_id.ids),
        #     ('state', '=', 'done'),
        #     ('company_id', '=', self.company_id.id),
        #     ('product_id', '=', self.product_id.id),
        #     ('date', '>=', start_date_dt),
        #     ('date', '<=', end_date_dt)
        # ], order='date asc, id asc')
        lot_stock_id = location_id.lot_stock_id.ids
        lot_stock_id.append(0)
        lot_stock_id.append(0)

        self._cr.execute("""
                select a.id as id, a.date as date
                    from stock_move a
                    join stock_location b on b.id = a.location_dest_id
                    where 
                    a.state='done'
                    and a.company_id = {_company_id}
                    and a.date >= '{_date_from}'
                    and a.date <= '{_date_to}'
                    and split_part(b.parent_path , '/', 2) = '{_origin_view}'
                    and a.product_id = {_product_id}
                    union
                    select a.id as id, a.date as date 
                    from stock_move a
                    where 
                    a.state='done'
                    and a.company_id = {_company_id}
                    and a.date >= '{_date_from}'
                    and a.date <= '{_date_to}'
                    and a.product_id = {_product_id}
                    and (location_id in {_lot_ids} or location_dest_id in {_lot_ids})
                    order by date
                """.format(_company_id=self.company_id.id,
                           _date_from=start_date_dt,
                           _date_to=end_date_dt,
                           _product_id=self.product_id.id,
                           _lot_ids=tuple(lot_stock_id),
                           _origin_view=str(location_id.view_location_id.id)))
        feth_sm = self.env.cr.dictfetchall()
        feth_id = []
        for x in feth_sm:
            feth_id.append(x.get('id'))
        sm = self.env['stock.move'].sudo().search([('id', 'in', feth_id)], order='date asc')
        # sm = self.env['stock.move'].sudo().browse([x[0] for x in self._cr.fetchall()])


        initial_qty_stock = 0
        beginning_balance = self.env['stock.move'].search(['|',
            ('location_id', 'in', location_id.lot_stock_id.ids),
            ('location_dest_id', 'in', location_id.lot_stock_id.ids),
            ('state', '=', 'done'),
            ('company_id', '=', self.company_id.id),
            ('product_id', '=', self.product_id.id),
            ('date', '<', start_date_dt)
        ], order='date asc')

        out_qty = 0
        in_qty = 0
        for bb_ in beginning_balance:
            if bb_.location_dest_id.id == location_id.lot_stock_id.id:
                in_qty = 0
                for sml in bb_.move_line_ids:
                    in_qty += sml.qty_done

                out_qty = 0
                qty_akhir = (initial_qty_stock + in_qty) - out_qty
                initial_qty_stock = qty_akhir

            if bb_.location_id.id == location_id.lot_stock_id.id:
                in_qty = 0
                out_qty = 0
                for sml in bb_.move_line_ids:
                    out_qty += sml.qty_done

                qty_akhir = (initial_qty_stock + in_qty) - out_qty
                initial_qty_stock = qty_akhir

        res = []
        hitung_posisi_so = 0
        for sm_ in sm:
            if not sm_.lot_ids:
                date = sm_.date + timedelta(hours=7)
                if not sm_.picking_id.origin:
                    nomor_ref = sm_.picking_id.name or sm_.reference
                else:
                    nomor_ref = sm_.picking_id.name + ' (' +sm_.picking_id.origin + ') ' or sm_.reference
                qty_awal = initial_qty_stock
                if len(sm_.picking_type_id) > 0:
                    if sm_.location_dest_id.id == location_id.lot_stock_id.id:
                        in_qty = 0
                        for sml in sm_.move_line_ids:
                            in_qty += sml.qty_done

                        hitung_posisi_so = 0
                        for hpp_on_list in list_hpp:
                            if date.strftime('%Y-%m-%d %H:%M:%S') == hpp_on_list['date']:
                                hitung_posisi_so += 1
                                hpp_satuan = hpp_on_list['hpp']

                        out_qty = 0
                        total_in_qty += in_qty
                        qty_akhir = (initial_qty_stock + in_qty) - out_qty
                        initial_qty_stock = qty_akhir
                else:
                    in_qty = 0
                    for sml in sm_.move_line_ids:
                        in_qty += sml.qty_done

                    hitung_posisi_so = 0
                    for hpp_on_list in list_hpp:
                        if date.strftime('%Y-%m-%d %H:%M:%S') == hpp_on_list['date']:
                            hitung_posisi_so += 1
                            hpp_satuan = hpp_on_list['hpp']

                    out_qty = 0
                    total_in_qty += in_qty
                    qty_akhir = (initial_qty_stock + in_qty) - out_qty
                    initial_qty_stock = qty_akhir

                if sm_.location_id.id == location_id.lot_stock_id.id:
                    date_so = sm_.date + timedelta(hours=7)
                    for hpp_on_list in list_hpp:
                        if hpp_on_list['date'] < date.strftime('%Y-%m-%d %H:%M:%S'):
                            hpp_satuan_so = hpp_on_list['hpp']

                    hpp_satuan = hpp_satuan_so
                    in_qty = 0
                    out_qty = 0
                    for sml in sm_.move_line_ids:
                        out_qty += sml.qty_done

                    total_out_qty += out_qty
                    qty_akhir = (initial_qty_stock + in_qty) - out_qty
                    initial_qty_stock = qty_akhir

                cost = self.env['product.product'].sudo().search([('id', '=', self.product_id.id)], limit=1)

                res.append({
                    'tanggal': date.strftime('%d %B %Y %H:%M:%S'),
                    'nomor_ref': nomor_ref,
                    'supplier_pelanggan': sm_.picking_id.partner_id.name or '',
                    'batch_no': '-',
                    'exp_date': '-',
                    'qty_awal': qty_awal,
                    'qty_masuk': in_qty,
                    'qty_keluar': out_qty,
                    'qty_akhir': qty_akhir,
                    # 'hpp_satuan': self.currency_id.symbol + ' ' + str(f'{round(hpp_satuan, 2):,}')
                    # 'hpp_satuan': self.currency_id.symbol + ' ' + str(f'{round(new_dict_data[sm_.id] if sm_.id in new_dict_data else 0, 2):,}')
                    'hpp_satuan': self.currency_id.symbol + ' ' + str(
                        f'{round(new_dict_data[sm_.id] if sm_.id in new_dict_data else cost.product_tmpl_id.standard_price, 2):,}')
                })
            elif sm_.lot_ids:
                for lot in sm_.lot_ids:
                    date = sm_.date + timedelta(hours=7)
                    if not sm_.picking_id.origin:
                        nomor_ref = sm_.picking_id.name or sm_.reference
                    else:
                        nomor_ref = sm_.picking_id.name + ' (' +sm_.picking_id.origin + ') ' or sm_.reference
                    if not lot.name:
                        batch_no = '-'
                    else:
                        batch_no = lot.name
                    if not lot.expiration_date:
                        exp_date = '-'
                    else:
                        exp_date = lot.expiration_date + timedelta(hours=7)
                    qty_awal = initial_qty_stock

                    if len(sm_.picking_type_id) > 0:
                        if sm_.location_dest_id.id == location_id.lot_stock_id.id:
                            in_qty = 0
                            hpp = 0
                            line_sub_total = 0
                            product_qty = 0
                            for sml in sm_.move_line_ids:
                                if sml.lot_id.id == lot.id:
                                    in_qty += sml.qty_done
                            hitung_posisi_so = 0
                            for hpp_on_list in list_hpp:
                                if date.strftime('%Y-%m-%d %H:%M:%S') == hpp_on_list['date']:
                                    hitung_posisi_so += 1
                                    hpp_satuan = hpp_on_list['hpp']

                            out_qty = 0
                            total_in_qty += in_qty
                            qty_akhir = (initial_qty_stock + in_qty) - out_qty
                            initial_qty_stock = qty_akhir
                    else:
                        in_qty = 0
                        hpp = 0
                        line_sub_total = 0
                        product_qty = 0
                        for sml in sm_.move_line_ids:
                            if sml.lot_id.id == lot.id:
                                in_qty += sml.qty_done
                        hitung_posisi_so = 0
                        for hpp_on_list in list_hpp:
                            if date.strftime('%Y-%m-%d %H:%M:%S') == hpp_on_list['date']:
                                hitung_posisi_so += 1
                                hpp_satuan = hpp_on_list['hpp']

                        out_qty = 0
                        total_in_qty += in_qty
                        qty_akhir = (initial_qty_stock + in_qty) - out_qty
                        initial_qty_stock = qty_akhir

                    if sm_.location_id.id == location_id.lot_stock_id.id:
                        date_so = sm_.date + timedelta(hours=7)
                        for hpp_on_list in list_hpp:
                            if hpp_on_list['date'] < date.strftime('%Y-%m-%d %H:%M:%S'):
                                hpp_satuan_so = hpp_on_list['hpp']

                        hpp_satuan = hpp_satuan_so
                        in_qty = 0
                        out_qty = 0
                        for sml in sm_.move_line_ids:
                            if sml.lot_id.id == lot.id:
                                out_qty += sml.qty_done

                        total_out_qty += out_qty
                        qty_akhir = (initial_qty_stock + in_qty) - out_qty
                        initial_qty_stock = qty_akhir

                    cost = self.env['product.product'].sudo().search([('id', '=', self.product_id.id)], limit=1)

                    res.append({
                        'tanggal': date.strftime('%d %B %Y %H:%M:%S'),
                        'nomor_ref': nomor_ref,
                        'supplier_pelanggan': sm_.picking_id.partner_id.name or '',
                        'batch_no': batch_no,
                        'exp_date': exp_date,
                        'qty_awal': qty_awal,
                        'qty_masuk': in_qty,
                        'qty_keluar': out_qty,
                        'qty_akhir': qty_akhir,
                        # 'hpp_satuan': self.currency_id.symbol + ' ' + str(f'{round(hpp_satuan, 2):,}')
                        # 'hpp_satuan': self.currency_id.symbol + ' ' + str(f'{round(new_dict_data[sm_.id] if sm_.id in new_dict_data else 0, 2):,}')
                        'hpp_satuan': self.currency_id.symbol + ' ' + str(
                            f'{round(new_dict_data[sm_.id] if sm_.id in new_dict_data else cost.product_tmpl_id.standard_price, 2):,}')
                    })

        return res