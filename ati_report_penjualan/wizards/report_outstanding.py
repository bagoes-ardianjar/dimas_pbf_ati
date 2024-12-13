from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta

header_title = ['No', 'Nama Produk', 'Quantity', 'Harga Satuan', 'No. SO', 'Tanggal SO', 'Nama Customer', 'Pemesan']

class report_outstanding_penjualan(models.TransientModel):
    _name = 'report.outstanding.penjualan'

    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")

    def action_print_report_outstanding_penjualan(self):
        # return True
        context = self._context
        # print("context", context, self.ids)
        datas = {'ids': self.ids}
        datas['model'] = 'report.outstanding.penjualan'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        # print("action_print_report_outstanding_penjualan", datas)
        return self.env.ref('ati_report_penjualan.action_report_outstanding_penjualan').report_action(self, data=datas)

class ReportOutstandingPenjualanXlsx(models.AbstractModel):
    _name = 'report.ati_report_penjualan.report_outstanding_penjualan_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objs):
        # print("generate xlsx penjualan")
        for obj in objs:
            # print("obj penjualan", obj)

            # style #
            formatHeaderCompany = workbook.add_format({'font_size': 14, 'valign':'vcenter', 'align': 'center', 'bold': True})
            formatSubHeaderCompanyBold = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'center', 'bold': True})
            formatSubHeaderCompany = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'center'})
            formatHeaderTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'bold': True, 'bg_color':'#4ead2f', 'color':'white', 'text_wrap': True, 'border': 1})
            formatDetailTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre','text_wrap': True, 'border': 1})
            formatDetailCurrencyTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'num_format': '_-"Rp"* #,##0.00_-;-"Rp"* #,##0.00_-;_-"Rp"* "-"_-;_-@_-', 'text_wrap': True, 'border': 1})
            formatHeaderCurrencyTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'bold': True, 'bg_color':'#4ead2f', 'color':'white', 'num_format': '_-"Rp"* #,##0.00_-;-"Rp"* #,##0.00_-;_-"Rp"* "-"_-;_-@_-', 'text_wrap': True, 'border': 1})

            # buat worksheet #
            title = 'Laporan Outstanding Penjualan'
            sheet = workbook.add_worksheet(title)
            # set lebar kolom #
            sheet.set_column(0, 0, 3)
            sheet.set_column(1, 1, 25)
            sheet.set_column(2, 2, 10)
            sheet.set_column(3, 3, 15)
            sheet.set_column(4, 4, 20)
            sheet.set_column(5, 5, 15)
            sheet.set_column(6, 6, 25)
            sheet.set_column(7, 7, 20)

            start_date = datetime.strptime(data['form']['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(data['form']['end_date'], '%Y-%m-%d').date()
            n_date = (end_date - start_date).days
            periode = start_date.strftime("%d %B %Y") if start_date == end_date else f'{start_date.strftime("%d %B %Y")} - {end_date.strftime("%d %B %Y")}'

            sheet.merge_range(1, 0, 1, 7, 'Laporan Outstanding Penjualan', formatHeaderCompany)
            sheet.merge_range(2, 0, 2, 7, f'Periode {periode}', formatSubHeaderCompanyBold)
            sheet.merge_range(3, 0, 3, 7, '(Dalam Rupiah)', formatSubHeaderCompany)

            row = 5
            column = 0
            for header in header_title:
                sheet.write(row, column, header, formatHeaderTable)
                column += 1

            sale_order_ids = self.env['sale.order'].search([('state', 'in', ('sale','done')), ('date_order', '>=', start_date), ('date_order', '<=', end_date)], order='date_order asc, id asc')
            # print("sale_order_ids", sale_order_ids)

            i = 0
            total = 0
            row += 1
            row_start = row + 1
            _query = """
                        select
                            g.name as product_name,
                            --(select sum(y.product_uom_qty)as qty
                            --from stock_move_line y where y.id = d.id group by y.product_id),
                            d.product_uom_qty as qty,
                            b.id as soline_id,
                            a.name as so_name,
                            date(a.date_order) as date_order,
                            (select name from res_partner where id= a.partner_id) as partner_id,
                            (select name from res_partner where id = i.partner_id) as user_id
                        from sale_order a
                            join sale_order_line b on b.order_id = a.id 
                            join stock_move c on c.sale_line_id = b.id 
                            join stock_move_line d on d.move_id = c.id 
                            join stock_picking e on e.id = c.picking_id 
                            join product_product f on f.id = d.product_id 
                            join product_template g on g.id = f.product_tmpl_id 
                            join stock_location h on h.id = c.location_dest_id 
                            join res_users i on i.id = a.user_id 
                        where date(a.date_order) >= '{_start_date}' 
                            and date(a.date_order) <= '{_end_date}'
                            and a.state in ('sale','done')
                            and c.state not in ('done','cancel')
                            and h.usage = 'customer'
                            order by a.date_order asc,
                            a.id asc
                    """.format(_start_date=start_date, _end_date=end_date)
            self._cr.execute(_query)
            check_data = self._cr.dictfetchall()
            for rec in check_data:
                i += 1
                qty = rec.get('qty')
                sheet.write(row, 0, i, formatDetailTable)
                sheet.write(row, 1, rec.get('product_name') or '', formatDetailTable)
                sheet.write_number(row, 2, qty, formatDetailTable)
                sale_order_id = self.env['sale.order.line'].search([('id', '=', rec.get('soline_id'))])
                sheet.write(row, 3, sale_order_id.harga_satuan_baru, formatDetailCurrencyTable)
                sheet.write(row, 4, rec.get('so_name'), formatDetailTable)
                sheet.write(row, 5, rec.get('date_order').strftime("%d-%m-%Y"), formatDetailTable)
                sheet.write(row, 6, rec.get('partner_id'), formatDetailTable)
                sheet.write(row, 7, rec.get('user_id'), formatDetailTable)
                row += 1
                total += qty

            # for so in sale_order_ids:
            #     for line in so.order_line:
            #         # outs_qty = line.product_uom_qty - (line.qty_received or 0)
            #         outs_qty = line.outstanding_qty or 0
            #         move_ids = self.env['stock.move'].search([('sale_line_id', '=', line.id),('state', 'not in', ('done', 'cancel')),('location_dest_id.usage','=','customer')])
            #         outs_qty = 0
            #         for moves in move_ids:
            #             # print("moves", po.name, line.product_id.name, moves.picking_id.name, moves.picking_id.picking_type_id.code, moves.state)
            #             outs_qty += moves.product_uom_qty
            #         if outs_qty > 0:
            #             i+=1
            #             # print("data", i, line.product_id.name, line.product_uom_qty, outs_qty,  line.price_unit, so.name, so.date_order, so.partner_id.name, so.user_id.name)
            #             sheet.write(row, 0, i, formatDetailTable)
            #             sheet.write(row, 1, line.product_id.name, formatDetailTable)
            #             sheet.write_number(row, 2, outs_qty, formatDetailTable)
            #             sheet.write(row, 3, line.harga_satuan_baru, formatDetailCurrencyTable)
            #             sheet.write(row, 4, so.name, formatDetailTable)
            #             sheet.write(row, 5, so.date_order.strftime("%d-%m-%Y"), formatDetailTable)
            #             sheet.write(row, 6, so.partner_id.name, formatDetailTable)
            #             sheet.write(row, 7, so.user_id.name, formatDetailTable)
            #             row += 1
            #             total += outs_qty
            row_end = row
            column_end = row_end + 1
            # sheet.write(row, 0, 'Total', formatHeaderTable)
            sheet.merge_range(row, 0, row, 1, 'Total', formatHeaderTable)
            sheet.write(row, 2, total, formatHeaderTable)
            sheet.write(row, 3, '', formatHeaderTable)
            sheet.write(row, 4, '', formatHeaderTable)
            sheet.write(row, 5, '', formatHeaderTable)
            sheet.write(row, 6, '', formatHeaderTable)
            sheet.write(row, 7, '', formatHeaderTable)