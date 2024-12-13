from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

header_title = ['SKU', 'New SKU', 'Nama Produk', 'Satuan', 'Qty Jual', 'Jumlah HPP', 'Qty Retur', 'Jumlah Retur (Rp)', 'Penjualan Bersih', 'Harga Rata-rata', 'Jumlah Laba/Rugi', 'Rasio L/R (%)']
class PnlSaleProduct(models.Model):
    _name = 'report.ati_pbf_sale.pnl_sale_product.xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objs):
        formatHeaderCompany = workbook.add_format({'font_size': 14, 'valign':'vcenter', 'align': 'center', 'bold': True})
        formatSubHeaderCompanyBold = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'center', 'bold': True})
        formatSubHeaderCompany = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'center'})
        formatHeaderTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'bold': True, 'bg_color':'#4ead2f', 'color':'white', 'text_wrap': True, 'border': 1})
        formatHeaderCurrencyTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'bold': True, 'bg_color':'#4ead2f', 'color':'white', 'num_format': '_-"Rp"* #,##0.00_-;-"Rp"* #,##0.00_-;_-"Rp"* "-"_-;_-@_-', 'text_wrap': True, 'border': 1})
        formatDetailTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre','text_wrap': True, 'border': 1})
        formatDetailCurrencyTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'num_format': '_-"Rp"* #,##0.00_-;-"Rp"* #,##0.00_-;_-"Rp"* "-"_-;_-@_-', 'text_wrap': True, 'border': 1})

        title = 'Laporan Laba/Rugi Penjualan Per Produk'
        sheet = workbook.add_worksheet(title)

        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 1, 15)
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

        start_date = datetime.strptime(data['form']['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['form']['end_date'], '%Y-%m-%d').date()
        n_date = (end_date - start_date).days
        n_month = (end_date.month - start_date.month) + 1
        periode = start_date.strftime("%d %B %Y") if start_date == end_date else f'{start_date.strftime("%d %B %Y")} - {end_date.strftime("%d %B %Y")}'

        list_of_date = [start_date + timedelta(days=n) for n in range(n_date+1)]
        sheet.merge_range(1, 0, 1, len(header_title) - 1, 'Laporan Laba/Rugi Penjualan Per Produk', formatHeaderCompany)
        sheet.merge_range(2, 0, 2, len(header_title) - 1, f'Periode {periode}', formatSubHeaderCompanyBold)
        sheet.merge_range(3, 0, 3, len(header_title) - 1, '(Dalam Rupiah)', formatSubHeaderCompany)

        row =  5
        column = 0
        for header in header_title:
            sheet.write(row, column, header, formatHeaderTable)
            column += 1
        
        customer_margin = data['form']['margin_id']
        produk_umum = data['form']['produk_umum']
        product_type = data['form']['product_type']
        sales_person = data['form']['sales_person']

        if product_type == 'active':
            product_ids = self.env['product.product'].sudo().search([('active', '=', True), ('detailed_type', '=', 'product')])
        elif product_type == 'all':
            product_ids = self.env['product.product'].sudo().search([('detailed_type', '=', 'product')])
        elif product_type == 'is_transaction':
            product_ids = self.env['product.product'].sudo().search([('detailed_type', '=', 'product')])
        else:
            raise UserError('Filter Produk belum di pilih')


        row += 1
        total_penjualan = 0
        global_diskon_total = 0
        product_dic = {}
        global_diskon_perline = 0
        sale_order_line_ids=()
        credit_note_ids=()
        aml_ids = ()
        # for product in product_ids:
        #     if customer_margin != False and produk_umum != True:
        #         sale_order_line_ids = self.env['sale.order.line'].sudo().search([
        #             ('order_partner_id.margin_ids', 'in', customer_margin), ('product_id', '=', product.id),('price_unit', '>', 0),
        #             ('order_id.state', 'in', ['sale', 'done']),  ('order_id.date_order', '>=', start_date), ('order_id.date_order', '<=', end_date)
        #         ])
        #         # credit_note_ids = self.env['account.move.line'].sudo().search([
        #         #     ('partner_id.margin_ids', 'in', customer_margin), ('product_id', '=', product.id), ('exclude_from_invoice_tab', '!=', True),
        #         #     ('move_id.move_type', '=', 'out_refund'), ('move_id.state', '=', 'posted'), ('move_id.payment_state', 'in', ['paid', 'in_payment', 'partial']), ('move_id.invoice_date', '>=', start_date), ('move_id.invoice_date', '<=', end_date, ('harga_satuan', '!=', 0))
        #         # ])
        #
        #         credit_note_ids = self.env['account.move.line'].sudo().search([
        #             ('partner_id.margin_ids', 'in', customer_margin), ('product_id', '=', product.id),
        #             ('exclude_from_invoice_tab', '!=', True),
        #             ('move_id.move_type', '=', 'out_refund'), ('move_id.state', '=', 'posted'),
        #             ('move_id.invoice_date', '>=', start_date), ('move_id.invoice_date', '<=', end_date),('harga_satuan', '!=', 0)
        #         ])
        #
        #     if not customer_margin and produk_umum != False:
        #         sale_order_line_ids = self.env['sale.order.line'].sudo().search([
        #             ('order_partner_id.margin_ids', '=', False), ('product_id', '=', product.id),('price_unit', '>', 0),
        #             ('order_id.state', 'in', ['sale', 'done']),  ('order_id.date_order', '>=', start_date), ('order_id.date_order', '<=', end_date)
        #         ])
        #         credit_note_ids = self.env['account.move.line'].sudo().search([
        #             ('partner_id.margin_ids', '=', False), ('product_id', '=', product.id),
        #             ('exclude_from_invoice_tab', '!=', True),
        #             ('move_id.move_type', '=', 'out_refund'), ('move_id.state', '=', 'posted'),
        #             ('move_id.invoice_date', '>=', start_date), ('move_id.invoice_date', '<=', end_date)
        #         ])
        #     if product_type in ['active', 'all'] or sale_order_line_ids or credit_note_ids:
        #         qty_sale = sum(line.product_uom_qty for line in sale_order_line_ids if line.harga_satuan_baru != 0)
        #         data_global = []
        #         global_diskon = 0
        #         for line in sale_order_line_ids:
        #             global_diskon = line.order_id.global_discount / len(line.order_id.order_line.filtered(lambda x: x.price_unit > 0))
        #             if line.product_id.id not in product_dic:
        #                 product_dic[line.product_id.id] = global_diskon
        #             else:
        #                 product_dic[line.product_id.id] += global_diskon
        #         if product.id in product_dic:
        #             global_diskon_perline = product_dic[product.id]
        #         # jumlah_hpp = product.standard_price * qty_sale if jumlah_penjualan > 0 else 0
        #         # jumlah_penjualan = sum(line.harga_satuan_baru * line.product_uom_qty for line in sale_order_line_ids if line.harga_satuan_baru != 0)
        #         jumlah_hpp = sum((line.price_unit * line.product_uom_qty) for line in sale_order_line_ids if line.harga_satuan_baru != 0)
        #         qty_retur = sum(aml.quantity for aml in credit_note_ids if aml.harga_satuan != 0)
        #         jumlah_penjualan = sum((line.price_subtotal) for line in sale_order_line_ids if line.harga_satuan_baru != 0)
        #         total_penjualan = jumlah_penjualan - global_diskon_perline
        #         jumlah_retur = sum(aml.quantity * aml.harga_satuan for aml in credit_note_ids if aml.harga_satuan != 0)
        #         penjualan_bersih = total_penjualan - jumlah_retur
        #         average_price = penjualan_bersih / qty_sale if qty_sale > 0 else 0
        #         jumlah_pnl = penjualan_bersih - jumlah_hpp
        #         rasio_pnl = round((jumlah_pnl / penjualan_bersih) * 100, 2) if penjualan_bersih > 0 else 0

        for product in product_ids:
            if customer_margin != False and produk_umum != True and not sales_person:
                aml_ids = self.env['account.move.line'].sudo().search([
                    ('partner_id.margin_ids', 'in', customer_margin), ('product_id', '=', product.id),
                    ('exclude_from_invoice_tab', '!=', True),
                    ('move_id.move_type', '=', 'out_invoice'), ('move_id.state', 'in', ['posted','draft','approval']),
                    ('move_id.invoice_date', '>=', start_date), ('move_id.invoice_date', '<=', end_date)
                ])

                credit_note_ids = self.env['account.move.line'].sudo().search([
                    ('partner_id.margin_ids', 'in', customer_margin), ('product_id', '=', product.id),
                    ('exclude_from_invoice_tab', '!=', True),
                    ('move_id.move_type', '=', 'out_refund'), ('move_id.state', 'in', ['posted','draft','approval']),
                    ('move_id.invoice_date', '>=', start_date), ('move_id.invoice_date', '<=', end_date),
                    ('harga_satuan', '!=', 0)
                ])

            if not customer_margin and produk_umum != False and not sales_person:
                aml_ids = self.env['account.move.line'].sudo().search([
                    ('partner_id.margin_ids', '=', False), ('product_id', '=', product.id),
                    ('exclude_from_invoice_tab', '!=', True),
                    ('move_id.move_type', '=', 'out_invoice'), ('move_id.state', 'in', ['posted','draft','approval']),
                    ('move_id.invoice_date', '>=', start_date), ('move_id.invoice_date', '<=', end_date)
                ])
                credit_note_ids = self.env['account.move.line'].sudo().search([
                    ('partner_id.margin_ids', '=', False), ('product_id', '=', product.id),
                    ('exclude_from_invoice_tab', '!=', True),
                    ('move_id.move_type', '=', 'out_refund'), ('move_id.state', 'in', ['posted','draft','approval']),
                    ('move_id.invoice_date', '>=', start_date), ('move_id.invoice_date', '<=', end_date)
                ])

            if customer_margin != False and produk_umum != True and sales_person:
                aml_ids = self.env['account.move.line'].sudo().search([
                    ('partner_id.margin_ids', 'in', customer_margin), ('product_id', '=', product.id),
                    ('exclude_from_invoice_tab', '!=', True),
                    ('move_id.sales_person', '=', sales_person),
                    ('move_id.move_type', '=', 'out_invoice'), ('move_id.state', 'in', ['posted','draft','approval']),
                    ('move_id.invoice_date', '>=', start_date), ('move_id.invoice_date', '<=', end_date)
                ])

                credit_note_ids = self.env['account.move.line'].sudo().search([
                    ('partner_id.margin_ids', 'in', customer_margin), ('product_id', '=', product.id),
                    ('exclude_from_invoice_tab', '!=', True),
                    ('move_id.sales_person', '=', sales_person),
                    ('move_id.move_type', '=', 'out_refund'), ('move_id.state', 'in', ['posted','draft','approval']),
                    ('move_id.invoice_date', '>=', start_date), ('move_id.invoice_date', '<=', end_date),
                    ('harga_satuan', '!=', 0)
                ])

            if not customer_margin and produk_umum != False and sales_person:
                aml_ids = self.env['account.move.line'].sudo().search([
                    ('partner_id.margin_ids', '=', False), ('product_id', '=', product.id),
                    ('exclude_from_invoice_tab', '!=', True),
                    ('move_id.sales_person', '=', sales_person),
                    ('move_id.move_type', '=', 'out_invoice'), ('move_id.state', 'in', ['posted','draft','approval']),
                    ('move_id.invoice_date', '>=', start_date), ('move_id.invoice_date', '<=', end_date)
                ])
                credit_note_ids = self.env['account.move.line'].sudo().search([
                    ('partner_id.margin_ids', '=', False), ('product_id', '=', product.id),
                    ('exclude_from_invoice_tab', '!=', True),
                    ('move_id.sales_person', '=', sales_person),
                    ('move_id.move_type', '=', 'out_refund'), ('move_id.state', 'in', ['posted','draft','approval']),
                    ('move_id.invoice_date', '>=', start_date), ('move_id.invoice_date', '<=', end_date)
                ])
            if product_type in ['active', 'all'] or aml_ids or credit_note_ids:
                qty_sale = sum(line.quantity for line in aml_ids if line.harga_satuan != 0)
                data_global = []
                global_diskon = 0
                for line in aml_ids:
                    global_diskon = line.move_id.global_order_discount / len(line.move_id.line_ids.filtered(lambda x: x.ati_price_unit > 0 and x.exclude_from_invoice_tab == False))
                    if line.product_id.id not in product_dic:
                        product_dic[line.product_id.id] = global_diskon
                    else:
                        product_dic[line.product_id.id] += global_diskon
                if product.id in product_dic:
                    global_diskon_perline = product_dic[product.id]
                # jumlah_hpp = product.standard_price * qty_sale if jumlah_penjualan > 0 else 0
                # jumlah_penjualan = sum(line.harga_satuan_baru * line.product_uom_qty for line in sale_order_line_ids if line.harga_satuan_baru != 0)
                jumlah_hpp = sum((line.ati_price_unit * line.quantity) for line in aml_ids if line.harga_satuan != 0)
                qty_retur = sum(aml.quantity for aml in credit_note_ids if aml.harga_satuan != 0)
                jumlah_penjualan = sum((line.quantity * line.harga_satuan) for line in aml_ids if line.harga_satuan != 0)
                total_penjualan = jumlah_penjualan - global_diskon_perline
                jumlah_retur = sum(aml.quantity * aml.harga_satuan for aml in credit_note_ids if aml.harga_satuan != 0)
                penjualan_bersih = total_penjualan - jumlah_retur
                average_price = penjualan_bersih / qty_sale if qty_sale > 0 else 0
                jumlah_pnl = penjualan_bersih - jumlah_hpp
                rasio_pnl = round((jumlah_pnl / penjualan_bersih) * 100, 2) if penjualan_bersih > 0 else 0

                sheet.write(row, 0, product.sku or '', formatDetailTable)
                sheet.write(row, 1, product.new_sku or '', formatDetailTable)
                sheet.write(row, 2, product.display_name, formatDetailTable)
                sheet.write(row, 3, product.uom_id.name or '', formatDetailTable)
                sheet.write(row, 4, qty_sale, formatDetailTable)
                sheet.write(row, 5, jumlah_hpp, formatDetailCurrencyTable)
                sheet.write(row, 6, qty_retur, formatDetailTable)
                sheet.write(row, 7, jumlah_retur, formatDetailCurrencyTable)
                sheet.write(row, 8, penjualan_bersih, formatDetailCurrencyTable)
                sheet.write(row, 9, average_price, formatDetailCurrencyTable)
                sheet.write(row, 10, jumlah_pnl, formatDetailCurrencyTable)
                sheet.write(row, 11, rasio_pnl, formatDetailTable)
                row += 1

