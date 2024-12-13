from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta

header_title = ['Kode PLU', 'Barcode', 'Nama Barang', 'Satuan', 'Qty', 'Harga Rata - Rata', 'Total Pembelian Inc Tax']

class report_pembelian_perbarang(models.TransientModel):
    _name = 'report.pembelian.perbarang'

    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    partner_id = fields.Many2one('res.partner', 'Supplier')
    product_ids = fields.Many2many("product.product", string="Product")
    pabrik_id = fields.Many2one('pabrik.product', 'Pabrik')

    def action_print_report_pembelian_perbarang(self):
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
        return self.env.ref('ati_report_pembelian.action_report_pembelian_perbarang').report_action(self, data=data)

    def action_print_report_pembelian_perbarang_xlsx(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'report.pembelian.perbarang'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        return self.env.ref('ati_report_pembelian.action_report_pembelian_perbarang_xlsx').report_action(self, data=datas)

class po_barang_template(models.AbstractModel):
    _name = 'report.ati_report_pembelian.po_barang_template'

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
                # print(products)
                product = products.replace(',)', ')')
                # print(product)
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
                        count(x.so_name) as po_count,
                        sum(x.product_uom_qty) as product_uom_qty,
                        sum(price_total) as price_total,
                        sum(x.total_global_discount) as total_global_discount,
                        sum(x.total_tax) as total_tax
                    FROM
                    (
                        SELECT
                            pt.sku,
                            pt.name,
                            pu.name as uom_name,
                            am.name as so_name,
                            COALESCE(sum(aml.quantity),0) as product_uom_qty,
                            coalesce(sum(aml.global_diskon_line),0) as total_global_discount,
                            coalesce(sum(price_subtotal),0) as price_total,
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
                        and am.move_type = 'in_invoice'
                        and am.source_document is not null
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
        res_pembelian_barang = self._cr.dictfetchall()
        data = {}
        pembelian_barang_list = []
        total_qty = 0
        jumlah_pembelian_inc_ppn = 0
        total_pembelian = 0
        total_pembelian_all = 0
        if res_pembelian_barang:
            for rec in res_pembelian_barang:
                global_diskon = rec.get('total_global_discount')
                # ppn = (rec.get('price_total') - global_diskon) * 11 / 100
                ppn = rec.get('total_tax')
                jumlah_pembelian_inc_ppn = (rec.get('price_total') - global_diskon) + ppn
                total_pembelian = jumlah_pembelian_inc_ppn
                harga_satuan_baru = total_pembelian / rec.get('product_uom_qty')
                pembelian_barang_list.append({
                    'sku': rec.get('sku'),
                    'name': rec.get('name'),
                    'uom_name': rec.get('uom_name'),
                    'product_uom_qty': rec.get('product_uom_qty'),
                    'average': harga_satuan_baru,
                    'total_pembelian': total_pembelian
                })
                total_qty += rec.get('product_uom_qty')
                total_pembelian_all += total_pembelian

        if pembelian_barang_list:
            docs = pembelian_barang_list


        result = {
            # 'doc_ids': data['ids'],
            # 'doc_model': data['model'],
            'start_date': start_date,
            'end_date': end_date,
            'docs': docs,
            'total_qty': total_qty,
            'total_pembelian_all': total_pembelian_all
        }
        return result

class po_barang_template_xlsx(models.AbstractModel):
    _name = 'report.ati_report_pembelian.po_barang_template_xlsx'
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

        title = 'Laporan Pembelian Per Barang'
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

        sheet.merge_range(1, 0, 1, 6, 'Laporan Pembelian Per Barang', formatHeaderCompany)
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
                # print(products)
                product = products.replace(',)', ')')
                # print(product)
                if product:
                    _where += 'and pp.id = {}'.format(product)
            elif len(product) > 1:
                products = str(tuple(list(set(product))))
                if products:
                    _where += 'and pp.id IN {}'.format(products)

        _query= """
                SELECT
                        x.sku,
                        x.name,
                        x.uom_name,
                        count(x.so_name) as po_count,
                        sum(x.product_uom_qty) as product_uom_qty,
                        sum(price_total) as price_total,
                        sum(x.total_global_discount) as total_global_discount,
                        sum(x.total_tax) as total_tax
                    FROM
                    (
                        SELECT
                            pt.sku,
                            pt.name,
                            pu.name as uom_name,
                            am.name as so_name,
                            COALESCE(sum(aml.quantity),0) as product_uom_qty,
                            coalesce(sum(aml.global_diskon_line),0) as total_global_discount,
                            coalesce(sum(price_subtotal),0) as price_total,
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
                        and am.move_type = 'in_invoice'
                        and aml.exclude_from_invoice_tab = 'false'
                        and am.source_document is not null
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
        res_pembelian_barang = self._cr.dictfetchall()
        data = {}
        pembelian_barang_list = []
        total_qty = 0
        jumlah_pembelian_inc_ppn = 0
        total_pembelian = 0
        total_pembelian_all = 0
        row += 1
        row_start = row + 1
        if res_pembelian_barang:
            for rec in res_pembelian_barang:
                global_diskon = rec.get('total_global_discount')
                # ppn = (rec.get('price_total') - global_diskon) * 11 / 100
                ppn = rec.get('total_tax')
                jumlah_pembelian_inc_ppn = (rec.get('price_total') - global_diskon) + ppn
                total_pembelian = jumlah_pembelian_inc_ppn
                harga_satuan_baru = total_pembelian / rec.get('product_uom_qty')
                sheet.write(row, 0, rec.get('sku'), formatDetailTable)
                sheet.write(row, 1, '', formatDetailTable)
                sheet.write(row, 2, rec.get('name'), formatDetailTable)
                sheet.write(row, 3, rec.get('uom_name'), formatDetailTable)
                sheet.write(row, 4, rec.get('product_uom_qty'), formatDetailTable)
                sheet.write(row, 5, harga_satuan_baru, formatDetailCurrencyTable)
                sheet.write(row, 6, total_pembelian, formatDetailCurrencyTable)
                row += 1
                total_qty += rec.get('product_uom_qty')
                total_pembelian_all += total_pembelian

            row_end = row
            column_end = row_end + 1
            sheet.merge_range(row, 0, row, 3, 'Total', formatHeaderTable)
            sheet.write(row, 4, total_qty, formatHeaderTable)
            sheet.write(row, 5, '', formatHeaderTable)
            sheet.write(row, 6, total_pembelian_all, formatHeaderCurrencyTable)
