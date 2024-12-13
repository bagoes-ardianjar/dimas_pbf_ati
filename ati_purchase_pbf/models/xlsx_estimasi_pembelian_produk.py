from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

header_title = ['SKU', 'New SKU', 'Purchase Category', 'Nama Barang', 'Stock Akhir', 'Satuan', 'Lead Time', 'Qty Sales/Periode', 'Rata-rata qty Sales/bulan', 'Buffer', 'Estimasi PO', 'Kriteria']
class EstimasiPembelianProduk(models.Model):
    _name = 'report.ati_purchase_pbf.estimasi_pembelian_produk.xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objs):
        context = self._context.copy()
        company_ids = context.get('allowed_company_ids', [0])
        company_ids.append(0)
        company_ids.append(0)
        formatHeaderCompany = workbook.add_format({'font_size': 14, 'valign':'vcenter', 'align': 'center', 'bold': True})
        formatSubHeaderCompanyBold = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'center', 'bold': True})
        formatSubHeaderCompany = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'center'})
        formatHeaderTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'bold': True, 'bg_color':'#4ead2f', 'color':'white', 'text_wrap': True, 'border': 1})
        formatHeaderCurrencyTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'bold': True, 'bg_color':'#4ead2f', 'color':'white', 'num_format': '_-"Rp"* #,##0.00_-;-"Rp"* #,##0.00_-;_-"Rp"* "-"_-;_-@_-', 'text_wrap': True, 'border': 1})
        formatDetailTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre','text_wrap': True, 'border': 1})
        formatDetailCurrencyTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'num_format': '_-"Rp"* #,##0.00_-;-"Rp"* #,##0.00_-;_-"Rp"* "-"_-;_-@_-', 'text_wrap': True, 'border': 1})

        title = 'Report Estimasi Pembelian Produk'
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

        purchase_category_id = data['form']['purchase_category_id']
        start_date = datetime.strptime(data['form']['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['form']['end_date'], '%Y-%m-%d').date()
        n_date = (end_date - start_date).days
        n_month = (end_date.month - start_date.month) + 1
        periode = start_date.strftime("%d %B %Y") if start_date == end_date else f'{start_date.strftime("%d %B %Y")} - {end_date.strftime("%d %B %Y")}'

        list_of_date = [start_date + timedelta(days=n) for n in range(n_date+1)]
        sheet.merge_range(1, 0, 1, len(header_title) - 1, 'Report Estimasi Pembelian Produk', formatHeaderCompany)
        sheet.merge_range(2, 0, 2, 11, f'Periode {periode}', formatSubHeaderCompanyBold)
        # sheet.merge_range(3, 0, 3, 7, '(Dalam Rupiah)', formatSubHeaderCompany)

        row = 4
        column = 0
        for header in header_title:
            sheet.write(row, column, header, formatHeaderTable)
            column += 1
        
        lead_time = data['form']['lead_time']
        diff_date = end_date - start_date
        hari = diff_date.days + 1
        # product_ids = self.env['product.product'].sudo().search([
        #     ('active', '=', True),
        #     ('detailed_type', '=', 'product'),
        #     ('product_tmpl_id.purchase_category_id', '=', purchase_category_id)
        # ])
        # sale_order_ids = self.env['sale.order'].sudo().search([('state', 'in', ['sale', 'done']), ('date_order', '>=', start_date), ('date_order', '<=', end_date)], order='date_order asc')
        #
        # row += 1
        # for product in product_ids:
        #     qty_sale_periode = sum(line.product_uom_qty if line.product_id == product else 0 for line in sale_order_ids.mapped('order_line'))
        #     average_qty_sale_month = qty_sale_periode / n_month
        #     buffer = average_qty_sale_month / int(lead_time)
        #     po_estimation = product.qty_available - buffer
        #     criteria = 'Barang Kosong'
        #     if product.qty_available < buffer:
        #         criteria = 'Perlu PO'
        #     elif product.qty_available > buffer * 6:
        #         criteria = 'Kelebihan'
        #     elif product.qty_available < buffer * 6:
        #         criteria = 'Aman'
        #
        #     sheet.write(row, 0, product.sku or '', formatDetailTable)
        #     sheet.write(row, 1, product.new_sku or '', formatDetailTable)
        #     sheet.write(row, 2, self.env['ati.purchase.category'].sudo().browse(purchase_category_id).name, formatDetailTable)
        #     sheet.write(row, 3, product.display_name, formatDetailTable)
        #     sheet.write(row, 4, product.qty_available, formatDetailTable)
        #     sheet.write(row, 5, product.uom_id.name or '', formatDetailTable)
        #     sheet.write(row, 6, lead_time, formatDetailTable)
        #     sheet.write(row, 7, qty_sale_periode, formatDetailTable)
        #     sheet.write(row, 8, average_qty_sale_month, formatDetailTable)
        #     sheet.write(row, 9, buffer, formatDetailTable)
        #     sheet.write(row, 10, po_estimation, formatDetailTable)
        #     sheet.write(row, 11, criteria, formatDetailTable)
        #     row += 1

        self._cr.execute("""(
            select
                *,
                ceil(data.qty_sales / {_hari}) as qty_sales_perhari,
                ceil(data.qty_sales / {_hari}) / {_lead_time} as buffer,
                data.stock_akhir - (ceil(data.qty_sales / {_hari}) / {_lead_time}) as estimasi_po,
                case
                    when data.stock_akhir = 0 and ceil(data.qty_sales / {_hari}) / {_lead_time} > 0 then 'Barang Kosong'
                    when data.stock_akhir < ceil(data.qty_sales / {_hari}) / {_lead_time} then 'Perlu PO'
                    when data.stock_akhir > (ceil(data.qty_sales / {_hari}) / {_lead_time} * 6) then 'Kelebihan'
                    when data.stock_akhir < (ceil(data.qty_sales / {_hari}) / {_lead_time} * 6) then 'Aman'
                    else 'Barang Kosong'
                end as kriteria
            from
            (select
                b.sku as sku,
                b.new_sku as new_sku,
                (select o.name from ati_purchase_category o where o.id = b.purchase_category_id) as purchase_category,
                b.name as nama_barang,
                (select coalesce(sum(q.quantity), 0) from stock_quant q where q.product_id = a.id
                    and date(q.write_date) <= '{_end_date}' and q.company_id in {_company} and q.quantity > 0) as stock_akhir,
                (select u.name from uom_uom u where u.id = b.uom_id) as uom,
                {_lead_time} as lead_time,
                (select coalesce(sum(x.product_uom_qty), 0) from sale_order_line x
                    join sale_order y on y.id = x.order_id
                    where y.state in ('sale','done')
                    and date(y.date_order) >= '{_start_date}' and date(y.date_order) <= '{_end_date}'
                    and x.product_id = a.id) as qty_sales
                from product_product a
                join product_template b on b.id = a.product_tmpl_id
                where b.purchase_category_id = {_purchase_category}) data
        )""".format(
            _hari=hari,
            _lead_time=lead_time,
            _end_date=str(end_date),
            _company=tuple(company_ids),
            _start_date=str(start_date),
            _purchase_category=purchase_category_id,
        ))
        fet_data = self._cr.dictfetchall()
        row += 1
        buffer = 0
        estimasi_po = 0
        sales_perbulan = 0
        bulan = (hari - 1) // 31 + 1
        kriteria = ''
        for p in fet_data:
            buffer = p['qty_sales'] * p['lead_time']
            if bulan :
                sales_perbulan = p['qty_sales'] / bulan
            estimasi_po = p['stock_akhir'] - buffer
            sales_6hari = p['qty_sales_perhari'] * 6
            if p['stock_akhir'] == 0 and buffer > 0:
                kriteria = 'Barang Kosong'
            elif p['stock_akhir'] >= 1 and p['stock_akhir'] < buffer:
                kriteria = 'Perlu PO'
            elif p['stock_akhir'] > sales_6hari and p['stock_akhir'] > buffer:
                kriteria = 'Kelebihan'
            else:
                kriteria = 'Aman'
            sheet.write(row, 0, p['sku'] or '', formatDetailTable)
            sheet.write(row, 1, p['new_sku'] or '', formatDetailTable)
            sheet.write(row, 2, p['purchase_category'], formatDetailTable)
            sheet.write(row, 3, p['nama_barang'], formatDetailTable)
            sheet.write(row, 4, p['stock_akhir'], formatDetailTable)
            sheet.write(row, 5, p['uom'] or '', formatDetailTable)
            sheet.write(row, 6, p['lead_time'], formatDetailTable)
            sheet.write(row, 7, p['qty_sales'], formatDetailTable)
            # sheet.write(row, 8, p['qty_sales_perhari'], formatDetailTable)
            sheet.write(row, 8, round(sales_perbulan,2), formatDetailTable)
            # sheet.write(row, 9, p['buffer'], formatDetailTable)
            sheet.write(row, 9, buffer, formatDetailTable)
            # sheet.write(row, 10, p['estimasi_po'], formatDetailTable)
            sheet.write(row, 10, estimasi_po, formatDetailTable)
            # sheet.write(row, 11, p['kriteria'], formatDetailTable)
            sheet.write(row, 11, kriteria, formatDetailTable)
            row += 1
