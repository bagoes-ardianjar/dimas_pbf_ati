from odoo import models, fields, api, exceptions, _

class report_penjualan(models.TransientModel):
    _name = 'report.penjualan'

    report_type = fields.Selection(selection=[
            ('Harian', 'Harian'),
            ('Harian (XLSX)', 'Harian (XLSX)'),
            ('Customer', 'Customer'),
            ('Customer (XLSX)', 'Customer (XLSX)'),
            ('Per Item', 'Per Item'),
            ('Per Item (XLSX)', 'Per Item (XLSX)'),
            ('Per Barang', 'Per Barang'),
            ('Per Barang (XLSX)', 'Per Barang (XLSX)'),
            ('Per Faktur', 'Per Faktur'),
            ('Per Faktur (XLSX)', 'Per Faktur (XLSX)'),
        ], string='Report Type')
    company_id = fields.Many2one('res.company', 'Company')
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    partner_id = fields.Many2one('res.partner', 'Customer')
    product_ids = fields.Many2many("product.product", string="Product")
    pabrik_id = fields.Many2one('pabrik.product', 'Pabrik')
    product_id = fields.Many2one('product.product', string="Product")
    sales_person = fields.Many2one('hr.employee', string='Sales Person')
    is_pasien = fields.Boolean(string='Is Panel')

    def action_print_report_penjualan(self):
        if self.report_type == 'Per Barang':
            barang_id = self.env['report.penjualan.perbarang'].create({
                'start_date': self.start_date,
                'end_date': self.end_date,
                'partner_id': self.partner_id.id if self.partner_id else None,
                'product_ids': self.product_ids.ids,
                'pabrik_id': self.pabrik_id.id if self.pabrik_id else None
            })
            if barang_id:
                return barang_id.action_print_report_penjualan_perbarang()
            # return self.env['report.penjualan.perbarang'].with_context(start_date=self.start_date, end_date=self.end_date).action_print_report_penjualan_perbarang()
        elif self.report_type == 'Per Barang (XLSX)':
            barang_id = self.env['report.penjualan.perbarang'].create({
                'start_date': self.start_date,
                'end_date': self.end_date,
                'partner_id': self.partner_id.id if self.partner_id else None,
                'product_ids': self.product_ids.ids,
                'pabrik_id': self.pabrik_id.id if self.pabrik_id else None
            })
            if barang_id:
                return barang_id.action_print_report_penjualan_perbarang_xlsx()
        elif self.report_type == 'Per Faktur':
            faktur_id = self.env['report.penjualan.perfakturr'].create({
                'start_date': self.start_date,
                'end_date': self.end_date,
                'partner_id': self.partner_id.id
            })
            if faktur_id:
                return faktur_id.action_print_report_penjualan_perfaktur()
        elif self.report_type == 'Per Faktur (XLSX)':
            faktur_id = self.env['report.penjualan.perfakturr'].create({
                'start_date': self.start_date,
                'end_date': self.end_date,
                'partner_id': self.partner_id.id
            })
            if faktur_id:
                return faktur_id.action_print_report_penjualan_perfaktur_xlsx()
        elif self.report_type == 'Harian':
            daily_id = self.env['wizard.report.sale.daily'].create({
                'start_date': self.start_date,
                'end_date': self.end_date
            })
            if daily_id:
                return daily_id.button_generate_preview()
            # return self.env['wizard.report.sale.daily'].with_context(start_date=self.start_date, end_date=self.end_date).button_generate_excel()
        elif self.report_type == 'Harian (XLSX)':
            daily_id = self.env['wizard.report.sale.daily'].create({
                'start_date': self.start_date,
                'end_date': self.end_date
            })
            if daily_id:
                return daily_id.button_generate_excel()
        elif self.report_type == 'Customer (XLSX)':
            cust_id = self.env['wizard.customer.sale'].create({
                'start_date': self.start_date,
                'end_date': self.end_date,
                'is_pasien': self.is_pasien,
                'partner_id': self.partner_id.id if self.partner_id else None
            })
            if cust_id:
                return cust_id.button_generate_excel()
        elif self.report_type == 'Customer':
            cust_id = self.env['wizard.customer.sale'].create({
                'start_date': self.start_date,
                'end_date': self.end_date,
                'is_pasien': self.is_pasien,
                'partner_id': self.partner_id.id if self.partner_id else None
            })
            if cust_id:
                return cust_id.button_generate_preview()
        elif self.report_type == 'Per Item':
            item_id = self.env['x.report.penjualan.so'].create({
                'start_date': self.start_date,
                'end_date': self.end_date,
                'company_id': self.company_id.id,
                'product_id': self.product_id.id,
                'partner_id': self.partner_id.id,
                'sales_person': self.sales_person.id
            })
            if item_id:
                return item_id.action_print_report()
        elif self.report_type == 'Per Item (XLSX)':
            item_id = self.env['x.report.penjualan.so'].create({
                'start_date': self.start_date,
                'end_date': self.end_date,
                'company_id': self.company_id.id,
                'product_id': self.product_id.id,
                'partner_id': self.partner_id.id,
                'sales_person': self.sales_person.id
            })
            if item_id:
                return item_id.action_print_report_xlsx()
        return True