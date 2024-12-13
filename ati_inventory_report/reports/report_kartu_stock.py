from odoo import fields, models, api, _
from odoo.exceptions import UserError

from datetime import datetime as dt, timedelta
import calendar

class KartuStockReportXlsx(models.AbstractModel):
    _name = 'report.ati_inventory_report.kartu_stock.xlsx'
    _inherit = 'report.report_xlsx.abstract'

    # get price_unit/standard_price
    def _get_price(self, purchase_line_id=False, product_id=False):
        price = 0
        if purchase_line_id:
            return purchase_line_id.price_unit
        elif product_id and product_id.standard_price > 0:
            return product_id.standard_price
        return price

    def _get_precision_decimal(self, value, decimals=4):
        multiplier = 10 ** decimals
        return round(value * multiplier) / multiplier

    def generate_xlsx_report(self, workbook, data, lines):
        formatHeader = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'center','bg_color':'#D3D3D3', 'color': 'black', 'bold': True})
        formatHeader_Judul = workbook.add_format({'font_size': 12, 'valign':'vcenter', 'align': 'center', 'color': 'black', 'bold': True})
        formatTabel = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'center', 'color': 'black', 'bold': False, 'border': 1})
        formatTabelLeft = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'left', 'color': 'black', 'bold': False})
        formatSubHeader = workbook.add_format({'font_size': 12, 'valign':'vcenter', 'align': 'left', 'color': 'black', 'bold': False})

        h_cell_format = {'font_name': 'Arial', 'font_size': 12, 'bold': True, 'valign': 'vcenter', 'align': 'center',
                         'border': 1, 'bg_color':'#D3D3D3'}
        h_style = workbook.add_format(h_cell_format)

        formatHeader.set_border(1)
        formatTabel.set_border(1)
        formatTabelLeft.set_border(1)
        formatHeader.set_text_wrap()
        formatTabel.set_text_wrap()
        formatTabelLeft.set_text_wrap()
        formatSubHeader.set_text_wrap()
        h_style.set_text_wrap()

        sheet = workbook.add_worksheet('Kartu Stock')
        sheet.freeze_panes(6, 0)

        start_date = data['form']['start_date']
        end_date = data['form']['end_date']

        start_date_dt = dt.strptime(start_date, "%Y-%m-%d %H:%M:%S")
        end_date_dt = dt.strptime(end_date, "%Y-%m-%d %H:%M:%S")

        row = 5

        sheet.set_column(row, 0, 17)
        sheet.set_column(row, 1, 17)
        sheet.set_column(row, 2, 29)
        sheet.set_column(row, 3, 15)
        sheet.set_column(row, 4, 15)
        sheet.set_column(row, 5, 13)
        sheet.set_column(row, 6, 13)
        sheet.set_column(row, 7, 13)
        sheet.set_column(row, 8, 13)
        sheet.set_column(row, 9, 13)

        sheet.merge_range(0, 0, 0, 9, 'Kartu Stok Barang', formatHeader_Judul)
        if start_date_dt != end_date_dt:
            sheet.merge_range(1, 0, 1, 9, '%s %s %s s.d %s %s %s' % (start_date_dt.day, calendar.month_name[start_date_dt.month], start_date_dt.year,
                                                                     end_date_dt.day, calendar.month_name[end_date_dt.month], end_date_dt.year), formatHeader_Judul)
        elif start_date_dt == end_date_dt:
            sheet.merge_range(1, 0, 1, 9, '%s %s %s' % ((start_date_dt.day, calendar.month_name[start_date_dt.month], start_date_dt.year) or (end_date_dt.day, calendar.month_name[end_date_dt.month], end_date_dt.year)), formatHeader_Judul)
        sheet.merge_range(2, 0, 2, 1, 'Barang: %s' % (data['form']['product_name']), formatSubHeader)
        sheet.merge_range(3, 0, 3, 1, 'Gudang: %s' % (data['form']['wh_name']), formatSubHeader)
        # sheet.merge_range(4, 0, 4, 1, 'Satuan: %s' % (data['form']['uom_name']), formatSubHeader)

        sheet.write(row, 0, 'Tanggal', h_style)
        sheet.write(row, 1, 'Nomor Ref', h_style)
        sheet.write(row, 2, 'Supplier / Pelanggan', h_style)
        sheet.write(row, 3, 'Batch No.', h_style)
        sheet.write(row, 4, 'Exp. Date', h_style)
        sheet.write(row, 5, 'Qty Awal', h_style)
        sheet.write(row, 6, 'Qty Masuk', h_style)
        sheet.write(row, 7, 'Qty Keluar', h_style)
        sheet.write(row, 8, 'Qty Akhir', h_style)
        sheet.write(row, 9, 'HPP Satuan', h_style)

        location_id = self.env['stock.warehouse'].search([('id', '=', data['form']['warehouse_id'])])

        row_of_content = row + 1

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
        product_id = data['form']['product_id']
        svl_obj = self.env['stock.valuation.layer'].search([('product_id', '=', product_id), ])
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

        # modified by ibad
        # sm = self.env['stock.move'].search(['|',
        #     ('location_id', 'in', location_id.lot_stock_id.ids),
        #     ('location_dest_id', 'in', location_id.lot_stock_id.ids),
        #     ('state', '=', 'done'),
        #     ('company_id', '=', lines.warehouse_id.company_id.id),
        #     ('product_id', '=', lines.product_id.id),
        #     ('date', '>=', start_date_dt),
        #     ('date', '<=', end_date_dt)
        # ], order='date asc, id asc')

        lot_stock_id = location_id.lot_stock_id.ids
        lot_stock_id.append(0)
        lot_stock_id.append(0)

        self._cr.execute("""
        select a.id
            from stock_move a
            join stock_location b on b.id = a.location_dest_id
            where 
            a.state='done'
            and a.company_id = {_company_id}
            and date(a.date) >= '{_date_from}'
            and date(a.date) <= '{_date_to}'
            and split_part(b.parent_path , '/', 2) = '{_origin_view}'
            and a.product_id = {_product_id}
            union
            select a.id  
            from stock_move a
            where 
            a.state='done'
            and a.company_id = {_company_id}
            and date(a.date) >= '{_date_from}'
            and date(a.date) <= '{_date_to}'
            and a.product_id = {_product_id}
            and (location_id in {_lot_ids} or location_dest_id in {_lot_ids})
        """.format(_company_id=lines.warehouse_id.company_id.id,
                   _date_from=start_date_dt,
                   _date_to=end_date_dt,
                   _product_id=lines.product_id.id,
                   _lot_ids=tuple(lot_stock_id),
                   _origin_view=str(lines.warehouse_id.view_location_id.id)))

        sm = self.env['stock.move'].sudo().browse([x[0] for x in self._cr.fetchall()])
        cost = self.env['product.product'].sudo().search([('id', '=', lines.product_id.id)], limit=1)

        initial_qty_stock = 0
        beginning_balance = self.env['stock.move'].search(['|',
            ('location_id', 'in', location_id.lot_stock_id.ids),
            ('location_dest_id', 'in', location_id.lot_stock_id.ids),
            ('state', '=', 'done'),
            ('company_id', '=', lines.warehouse_id.company_id.id),
            ('product_id', '=', lines.product_id.id),
            ('date', '<', start_date_dt)
        ], order='date asc, id asc')
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

        for sm_ in sm:
            if not sm_.lot_ids:
                #
                date = sm_.date + timedelta(hours=7)
                sheet.write(row_of_content, 0, date.strftime('%d %B %Y %H:%M:%S'), formatTabel)
                if not sm_.picking_id.origin:
                    sheet.write(row_of_content, 1, sm_.picking_id.name or sm_.reference, formatTabel)
                else:
                    sheet.write(row_of_content, 1, sm_.picking_id.name + ' (' +sm_.picking_id.origin + ') ' or sm_.reference, formatTabel)
                sheet.write(row_of_content, 2, sm_.picking_id.partner_id.name or '', formatTabel)
                sheet.write(row_of_content, 3, '-', formatTabel)
                sheet.write(row_of_content, 4, '-', formatTabel)
                sheet.write(row_of_content, 5, initial_qty_stock, formatTabel)

                if len(sm_.picking_type_id) > 0:
                    if sm_.location_dest_id.id == location_id.lot_stock_id.id:
                        in_qty = 0
                        for sml in sm_.move_line_ids:
                            in_qty += sml.qty_done

                        hitung_posisi_so =0
                        for hpp_on_list in list_hpp:
                            if date.strftime('%Y-%m-%d %H:%M:%S') == hpp_on_list['date']:
                                hitung_posisi_so += 1
                                hpp_satuan = hpp_on_list['hpp']

                        out_qty = 0
                        total_in_qty += in_qty
                        qty_akhir = (initial_qty_stock + in_qty) - out_qty
                        initial_qty_stock = qty_akhir
                        sheet.write(row_of_content, 6, in_qty, formatTabel)
                        sheet.write(row_of_content, 7, 0, formatTabel)
                        sheet.write(row_of_content, 8, qty_akhir, formatTabel)
                        # sheet.write(row_of_content, 9, hpp_satuan, formatTabel)
                        # sheet.write(row_of_content, 9, new_dict_data[sm_.id] if sm_.id in new_dict_data else 0, formatTabel)
                        sheet.write(row_of_content, 9, new_dict_data[sm_.id] if sm_.id in new_dict_data else cost.product_tmpl_id.standard_price, formatTabel)
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
                    sheet.write(row_of_content, 6, in_qty, formatTabel)
                    sheet.write(row_of_content, 7, 0, formatTabel)
                    sheet.write(row_of_content, 8, qty_akhir, formatTabel)
                    # sheet.write(row_of_content, 9, hpp_satuan, formatTabel)
                    # sheet.write(row_of_content, 9, new_dict_data[sm_.id] if sm_.id in new_dict_data else 0, formatTabel)
                    sheet.write(row_of_content, 9, new_dict_data[sm_.id] if sm_.id in new_dict_data else cost.product_tmpl_id.standard_price, formatTabel)

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
                    sheet.write(row_of_content, 6, 0, formatTabel)
                    sheet.write(row_of_content, 7, out_qty, formatTabel)
                    sheet.write(row_of_content, 8, qty_akhir, formatTabel)
                    # sheet.write(row_of_content, 9, hpp_satuan, formatTabel)
                    # sheet.write(row_of_content, 9, new_dict_data[sm_.id] if sm_.id in new_dict_data else 0, formatTabel)
                    sheet.write(row_of_content, 9, new_dict_data[sm_.id] if sm_.id in new_dict_data else cost.product_tmpl_id.standard_price, formatTabel)

                row_of_content += 1
                #

            elif sm_.lot_ids:
                for lot in sm_.lot_ids:
                    date = sm_.date + timedelta(hours=7)
                    sheet.write(row_of_content, 0, date.strftime('%d %B %Y %H:%M:%S'), formatTabel)
                    if not sm_.picking_id.origin:
                        sheet.write(row_of_content, 1, sm_.picking_id.name or sm_.reference, formatTabel)
                    else:
                        sheet.write(row_of_content, 1, sm_.picking_id.name + ' (' +sm_.picking_id.origin + ') ' or sm_.reference, formatTabel)
                    sheet.write(row_of_content, 2, sm_.picking_id.partner_id.name or '', formatTabel)

                    if not lot.name:
                        sheet.write(row_of_content, 3, '-', formatTabel)
                    else:
                        sheet.write(row_of_content, 3, lot.name, formatTabel)
                    if not lot.expiration_date:
                        sheet.write(row_of_content, 4, '-', formatTabel)
                    else:
                        exp_date = lot.expiration_date + timedelta(hours=7)
                        sheet.write(row_of_content, 4, exp_date.strftime('%d %B %Y %H:%M:%S'), formatTabel)
                    sheet.write(row_of_content, 5, initial_qty_stock, formatTabel)

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
                            sheet.write(row_of_content, 6, in_qty, formatTabel)
                            sheet.write(row_of_content, 7, 0, formatTabel)
                            sheet.write(row_of_content, 8, qty_akhir, formatTabel)
                            # sheet.write(row_of_content, 9, hpp_satuan, formatTabel)
                            # sheet.write(row_of_content, 9, new_dict_data[sm_.id] if sm_.id in new_dict_data else 0, formatTabel)
                            sheet.write(row_of_content, 9, new_dict_data[sm_.id] if sm_.id in new_dict_data else cost.product_tmpl_id.standard_price, formatTabel)
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
                        sheet.write(row_of_content, 6, in_qty, formatTabel)
                        sheet.write(row_of_content, 7, 0, formatTabel)
                        sheet.write(row_of_content, 8, qty_akhir, formatTabel)
                        # sheet.write(row_of_content, 9, hpp_satuan, formatTabel)
                        # sheet.write(row_of_content, 9, new_dict_data[sm_.id] if sm_.id in new_dict_data else 0, formatTabel)
                        sheet.write(row_of_content, 9, new_dict_data[sm_.id] if sm_.id in new_dict_data else cost.product_tmpl_id.standard_price, formatTabel)

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
                        sheet.write(row_of_content, 6, 0, formatTabel)
                        sheet.write(row_of_content, 7, out_qty, formatTabel)
                        sheet.write(row_of_content, 8, qty_akhir, formatTabel)
                        # sheet.write(row_of_content, 9, hpp_satuan, formatTabel)
                        # sheet.write(row_of_content, 9, new_dict_data[sm_.id] if sm_.id in new_dict_data else 0, formatTabel)
                        sheet.write(row_of_content, 9, new_dict_data[sm_.id] if sm_.id in new_dict_data else cost.product_tmpl_id.standard_price, formatTabel)

                    row_of_content += 1
                #
        else:
            row_of_total = row_of_content
            #
            sheet.merge_range(row_of_total, 0, row_of_total, 5, 'Jumlah', h_style)
            sheet.write(row_of_total, 6, total_in_qty, h_style)
            sheet.write(row_of_total, 7, total_out_qty, h_style)
            sheet.write(row_of_total, 8, ' ', h_style)
            sheet.write(row_of_total, 9, ' ', h_style)