from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta
import math

header_title = ['Kode PLU', 'Barcode', 'Nama Barang', 'Satuan', 'Qty', 'Harga Rata - Rata', 'Total Penjualan Inc Tax']

class report_penjualan_perbarang(models.TransientModel):
    _name = 'report.penjualan.perbarang'

    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    partner_id = fields.Many2one('res.partner', 'Customer')
    product_ids = fields.Many2many("product.product", string="Product")
    pabrik_id = fields.Many2one('pabrik.product', 'Pabrik')

    def action_print_report_penjualan_perbarang(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'partner_id': self.partner_id.id if self.partner_id else None,
                'product_ids': self.product_ids.ids,
                'pabrik_id': self.pabrik_id.id if self.pabrik_id else None
            },
        }
        # data = {'start_date': self.start_date, 'end_date': self.end_date}
        return self.env.ref('ati_report_penjualan.action_report_penjualan_perbarang').report_action(self, data=data)

    def action_print_report_penjualan_perbarang_xlsx(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'partner_id': self.partner_id.id if self.partner_id else None,
                'product_ids': self.product_ids.ids,
                'pabrik_id': self.pabrik_id.id if self.pabrik_id else None
            },
        }
        # data = {'start_date': self.start_date, 'end_date': self.end_date}
        return self.env.ref('ati_report_penjualan.action_report_penjualan_perbarang_xlsx').report_action(self, data=data)

class so_barang_template(models.AbstractModel):
    _name = 'report.ati_report_penjualan.so_barang_template'

    def _get_report_values(self, docids, data=None):
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        partner_id = data['form']['partner_id']
        product_ids = data['form']['product_ids']
        pabrik_id = data['form']['pabrik_id']
        docs = []

        _where = ""
        if start_date and end_date :
            _where = "where DATE(am.invoice_date) between '{_start}' and '{_end}' ".format(_start=start_date, _end=end_date)
        if partner_id:
            _where += 'and am.partner_id = {}'.format(partner_id)
        if pabrik_id:
            _where += 'and pt.pabrik = {}'.format(pabrik_id)
        if product_ids:
            product = []
            for rec in product_ids:
                product.append(rec)
            if len(product) == 1:
                products = str(tuple(list(set(product))))
                product = products.replace(',)', ')')
                if product:
                    _where += 'and pp.id = {}'.format(product)
            elif len(product) > 1:
                products = str(tuple(list(set(product))))
                if products:
                    _where += 'and pp.id IN {}'.format(products)

        _query = """
                SELECT
                    x.sku,
                    x.name,
                    x.uom_name,
                    sum(x.price_subtotal) as price_subtotal,
                    sum(x.global_discount_line) as global_discount_line,
                    count(x.so_name) as so_count,
                    sum(x.product_uom_qty) as product_uom_qty,
                    sum(x.price_unit) as price_unit,
                    sum(product_margin_amount) as product_margin_amount,
                    sum(price_total) as price_total,
                    sum(x.total_tax) as total_tax,
                    ROUND(((sum(price_unit))/sum(x.product_uom_qty))::numeric, 2) as average,
                    ROUND((((sum(price_unit))/sum(x.product_uom_qty)) * sum(x.product_uom_qty))::numeric, 2) as total_penjualan 
                FROM
                (
                    SELECT
                        pt.sku,
                        pt.name,
                        pu.name as uom_name,
                        am.name as so_name,
                        COALESCE(sum(aml.price_subtotal),0) as price_subtotal,
                        COALESCE(sum(aml.quantity),0) as product_uom_qty,
                        COALESCE(sum(aml.harga_satuan),0) * COALESCE(sum(aml.quantity),0) as price_unit,
                        COALESCE(sum(aml.product_margin_amount),0) as product_margin_amount,
                        coalesce(sum((coalesce((am.global_order_discount),0)/(select count(z.id) from account_move_line z where z.move_id = am.id and z.exclude_from_invoice_tab = false and z.ati_price_unit <>0))),0) as global_discount_line,
                        coalesce(sum(aml.total_tax),0) as total_tax,
                        COALESCE(sum(((aml.harga_satuan - aml.discount_amount) * aml.quantity)),0) as price_total
                    FROM
                        account_move am
                        join account_move_line aml on aml.move_id = am.id
                        join product_product pp on aml.product_id = pp.id
                        join product_template pt on pp.product_tmpl_id = pt.id
                        join uom_uom pu on pt.uom_id = pu.id
                    {_where}
                    and aml.ati_price_unit <> 0
                    and am.state in ('draft','approval','posted')
                    and am.move_type = 'out_invoice'
                    and am.source_document is not Null
                    and aml.exclude_from_invoice_tab = 'false'
                    group by
                        pt.sku,
                        pt.name,
                        pu.name,
                        am.name
                    order by
                        sku
                ) x
                GROUP BY
                    x.sku,
                    x.name,
                    x.uom_name
            """.format(_where=_where)
        self._cr.execute(_query)
        res_penjualan_barang = self._cr.dictfetchall()
        data = {}
        penjualan_barang_list = []
        total_qty = 0
        total_penjualan_all = 0
        if res_penjualan_barang:
            for rec in res_penjualan_barang:
                # total_penjualan = harga_satuan_baru * rec.get('product_uom_qty')

                global_diskon = rec.get('global_discount_line')
                # ppn = (rec.get('price_total') - global_diskon) * 11 / 100
                ppn = rec.get('total_tax')
                total_penjualan = (rec.get('price_total') - global_diskon) + ppn
                harga_satuan_baru = total_penjualan / rec.get('product_uom_qty')
                penjualan_barang_list.append({
                    'sku': rec.get('sku'),
                    'name': rec.get('name'),
                    'uom_name': rec.get('uom_name'),
                    'product_uom_qty': rec.get('product_uom_qty'),
                    # 'average': rec.get('average'),
                    'average': harga_satuan_baru,
                    # 'total_penjualan': rec.get('total_penjualan'),
                    'total_penjualan': total_penjualan
                })
                total_qty += rec.get('product_uom_qty')
                # total_penjualan_all += rec.get('total_penjualan')
                total_penjualan_all += total_penjualan

        if penjualan_barang_list:
            docs = penjualan_barang_list


        result = {
            # 'doc_ids': data['ids'],
            # 'doc_model': data['model'],
            'start_date': start_date,
            'end_date': end_date,
            'docs': docs,
            'total_qty': total_qty,
            'total_penjualan_all': total_penjualan_all
        }
        return result

class so_barang_template_xlsx(models.AbstractModel):
    _name = 'report.ati_report_penjualan.so_barang_template_xlsx'
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

        title = 'Laporan Rekap Penjualan Per Barang'
        sheet = workbook.add_worksheet(title)

        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 20)
        sheet.set_column(3, 3, 20)
        sheet.set_column(4, 4, 20)
        sheet.set_column(5, 5, 20)
        sheet.set_column(6, 6, 20)

        start_date = datetime.strptime(data['form']['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['form']['end_date'], '%Y-%m-%d').date()
        periode = start_date.strftime("%d %B %Y") if start_date == end_date else f'{start_date.strftime("%d %B %Y")} - {end_date.strftime("%d %B %Y")}'

        sheet.merge_range(1, 0, 1, 6, 'Laporan Rekap Penjualan Per Barang', formatHeaderCompany)
        sheet.merge_range(2, 0, 2, 6, f'Periode {periode}', formatSubHeaderCompanyBold)
        sheet.merge_range(3, 0, 3, 6, '(Dalam Rupiah)', formatSubHeaderCompany)

        row =  5
        column = 0
        for header in header_title:
            sheet.write(row, column, header, formatHeaderTable)
            column += 1


        #### DATA REPORT ####
        partner_id = data['form']['partner_id']
        product_ids = data['form']['product_ids']
        pabrik_id = data['form']['pabrik_id']

        _where = ""
        if start_date and end_date :
            _where = "where DATE(am.invoice_date) between '{_start}' and '{_end}' ".format(_start=start_date, _end=end_date)
        if partner_id:
            _where += 'and am.partner_id = {}'.format(partner_id)
        if pabrik_id:
            _where += 'and pt.pabrik = {}'.format(pabrik_id)
        if product_ids:
            product = []
            for rec in product_ids:
                product.append(rec)
            if len(product) == 1:
                products = str(tuple(list(set(product))))
                product = products.replace(',)', ')')
                if product:
                    _where += 'and pp.id = {}'.format(product)
            elif len(product) > 1:
                products = str(tuple(list(set(product))))
                if products:
                    _where += 'and pp.id IN {}'.format(products)

        _query = """
                SELECT
                    x.sku,
                    x.name,
                    x.uom_name,
                    sum(x.price_subtotal) as price_subtotal,
                    sum(x.global_discount_line) as global_discount_line,
                    count(x.so_name) as so_count,
                    sum(x.product_uom_qty) as product_uom_qty,
                    sum(x.price_unit) as price_unit,
                    sum(product_margin_amount) as product_margin_amount,
                    sum(price_total) as price_total,
                    sum(x.total_tax) as total_tax,
                    ROUND(((sum(price_unit))/sum(x.product_uom_qty))::numeric, 2) as average,
                    ROUND((((sum(price_unit))/sum(x.product_uom_qty)) * sum(x.product_uom_qty))::numeric, 2) as total_penjualan 
                FROM
                (
                    SELECT
                        pt.sku,
                        pt.name,
                        pu.name as uom_name,
                        am.name as so_name,
                        COALESCE(sum(aml.price_subtotal),0) as price_subtotal,
                        COALESCE(sum(aml.quantity),0) as product_uom_qty,
                        COALESCE(sum(aml.harga_satuan),0) * COALESCE(sum(aml.quantity),0) as price_unit,
                        COALESCE(sum(aml.product_margin_amount),0) as product_margin_amount,
                        coalesce(sum((coalesce((am.global_order_discount),0)/(select count(z.id) from account_move_line z where z.move_id = am.id and z.exclude_from_invoice_tab = false and z.ati_price_unit <>0))),0) as global_discount_line,
                        COALESCE(sum(((aml.harga_satuan - aml.discount_amount) * aml.quantity)),0) as price_total,
                        coalesce(sum(aml.total_tax),0) as total_tax
                    FROM
                        account_move am
                        join account_move_line aml on aml.move_id = am.id
                        join product_product pp on aml.product_id = pp.id
                        join product_template pt on pp.product_tmpl_id = pt.id
                        join uom_uom pu on pt.uom_id = pu.id
                    {_where}
                    and aml.ati_price_unit <> 0
                    and am.state in ('draft','approval','posted')
                    and am.move_type = 'out_invoice'
                    and am.source_document is not Null
                    and aml.exclude_from_invoice_tab = 'false'
                    group by
                        pt.sku,
                        pt.name,
                        pu.name,
                        am.name
                    order by
                        sku
                ) x
                GROUP BY
                    x.sku,
                    x.name,
                    x.uom_name
            """.format(_where=_where)
        self._cr.execute(_query)
        res_penjualan_barang = self._cr.dictfetchall()
        data = {}
        pembelian_barang_list = []
        total_qty = 0
        total_penjualan_all = 0
        row += 1
        row_start = row + 1
        if res_penjualan_barang:
            for rec in res_penjualan_barang:
                global_diskon = rec.get('global_discount_line')
                # ppn = (rec.get('price_total') - global_diskon) * 11 / 100
                ppn = rec.get('total_tax')

                total_penjualan = (rec.get('price_subtotal') - global_diskon) + ppn
                harga_satuan_baru = total_penjualan / rec.get('product_uom_qty')
                sheet.write(row, 0, rec.get('sku'), formatDetailTable)
                sheet.write(row, 1, '', formatDetailTable)
                sheet.write(row, 2, rec.get('name'), formatDetailTable)
                sheet.write(row, 3, rec.get('uom_name'), formatDetailTable)
                sheet.write(row, 4, rec.get('product_uom_qty'), formatDetailTable)
                # sheet.write(row, 5, rec.get('average'), formatDetailCurrencyTable)
                sheet.write(row, 5, harga_satuan_baru, formatDetailCurrencyTable)
                # sheet.write(row, 6, rec.get('total_penjualan'), formatDetailCurrencyTable)
                sheet.write(row, 6, total_penjualan, formatDetailCurrencyTable)
                row += 1
                total_qty += rec.get('product_uom_qty')
                # total_penjualan_all += rec.get('total_penjualan')
                total_penjualan_all += total_penjualan

            row_end = row
            column_end = row_end + 1
            sheet.merge_range(row, 0, row, 3, 'Total', formatHeaderTable)
            sheet.write(row, 4, total_qty, formatHeaderTable)
            sheet.write(row, 5, '', formatHeaderTable)
            sheet.write(row, 6, total_penjualan_all, formatHeaderCurrencyTable)
