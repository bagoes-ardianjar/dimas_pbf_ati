from odoo import models, fields, api, exceptions, _

class report_pembelian(models.TransientModel):
    _name = 'report.pembelian'

    report_type = fields.Selection(selection=[
            ('Harian', 'Harian'),
            ('Harian (XLSX)', 'Harian (XLSX)'),
            ('Supplier', 'Supplier'),
            ('Supplier (XLSX)', 'Supplier (XLSX)'),
            ('Per Item', 'Per Item'),
            ('Per Item (XLSX)', 'Per Item (XLSX)'),
            ('Per Barang', 'Per Barang'),
            ('Per Barang (XLSX)', 'Per Barang (XLSX)'),
            ('Per Faktur', 'Per Faktur'),
            ('Per Faktur (XLSX)', 'Per Faktur (XLSX)'),
            ('ppn', 'PPN'),
            ('ppn_xlsx', 'PPN (XLSX)'),
            ('nonppn', 'Non PPN'),
            ('nonppn_xlsx', 'Non PPN (XLSX)'),
        ], string='Report Type')
    company_id = fields.Many2one('res.company', 'Company')
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    partner_id = fields.Many2one('res.partner', 'Supplier')
    product_ids = fields.Many2many("product.product", string="Product")
    pabrik_id = fields.Many2one('pabrik.product', 'Pabrik')

    def action_print_report_pembelian(self):
        # print("All")
        if self.report_type == 'Per Barang':
            barang_id = self.env['report.pembelian.perbarang'].create({
                'start_date': self.start_date,
                'end_date': self.end_date,
                'partner_id': self.partner_id.id if self.partner_id else None,
                'product_ids': self.product_ids.ids,
                'pabrik_id': self.pabrik_id.id if self.pabrik_id else None
            })
            if barang_id:
                return barang_id.action_print_report_pembelian_perbarang()
        elif self.report_type == 'Per Barang (XLSX)':
            barang_id = self.env['report.pembelian.perbarang'].create({
                'start_date': self.start_date,
                'end_date': self.end_date,
                'partner_id': self.partner_id.id if self.partner_id else None,
                'product_ids': self.product_ids.ids,
                'pabrik_id': self.pabrik_id.id if self.pabrik_id else None
            })
            if barang_id:
                return barang_id.action_print_report_pembelian_perbarang_xlsx()
        elif self.report_type == 'Per Faktur':
            faktur_id = self.env['report.pembelian.perfakturr'].create({
                'start_date': self.start_date,
                'end_date': self.end_date
            })
            if faktur_id:
                return faktur_id.action_print_report_pembelian_perfaktur()
        elif self.report_type == 'Per Faktur (XLSX)':
            faktur_id = self.env['report.pembelian.perfakturr'].create({
                'start_date': self.start_date,
                'end_date': self.end_date
            })
            if faktur_id:
                return faktur_id.action_print_report_pembelian_perfaktur_xlsx()
        elif self.report_type == 'ppn':
            ppn_id = self.env['report.pembelian.ppn'].create({
                'start_date': self.start_date,
                'end_date': self.end_date
            })
            if ppn_id:
                return ppn_id.action_print_report_pembelian_ppn()
        elif self.report_type == 'ppn_xlsx':
            ppn_id = self.env['report.pembelian.ppn'].create({
                'start_date': self.start_date,
                'end_date': self.end_date
            })
            if ppn_id:
                return ppn_id.action_print_report_pembelian_ppn_xlsx()
        elif self.report_type == 'nonppn':
            nonppn_id = self.env['report.pembelian.nonppn'].create({
                'start_date': self.start_date,
                'end_date': self.end_date
            })
            if nonppn_id:
                return nonppn_id.action_print_report_pembelian_nonppn()
        elif self.report_type == 'nonppn_xlsx':
            nonppn_id = self.env['report.pembelian.nonppn'].create({
                'start_date': self.start_date,
                'end_date': self.end_date
            })
            if nonppn_id:
                return nonppn_id.action_print_report_pembelian_nonppn_xlsx()
        elif self.report_type == 'Harian (XLSX)':
            daily_id = self.env['wizard.report.purchase.daily'].create({
                'start_date': self.start_date,
                'end_date': self.end_date
            })
            if daily_id:
                return daily_id.button_generate_excel()
        elif self.report_type == 'Harian':
            daily_id = self.env['wizard.report.purchase.daily'].create({
                'start_date': self.start_date,
                'end_date': self.end_date
            })
            if daily_id:
                return daily_id.button_generate_preview()
        elif self.report_type == 'Supplier (XLSX)':
            supp_id = self.env['wizard.vendor.purchase'].create({
                'start_date': self.start_date,
                'end_date': self.end_date,
                'partner_id': self.partner_id.id if self.partner_id else None
            })
            if supp_id:
                return supp_id.button_generate_excel()
        elif self.report_type == 'Supplier':
            supp_id = self.env['wizard.vendor.purchase'].create({
                'start_date': self.start_date,
                'end_date': self.end_date,
                'partner_id': self.partner_id.id if self.partner_id else None
            })
            if supp_id:
                return supp_id.button_generate_preview()
        elif self.report_type == 'Per Item':
            item_id = self.env['x.report.pembelian.po'].create({
                'start_date': self.start_date,
                'end_date': self.end_date,
                'company_id': self.company_id.id
            })
            if item_id:
                return item_id.action_print_report_po()
        elif self.report_type == 'Per Item (XLSX)':
            item_id = self.env['x.report.pembelian.po'].create({
                'start_date': self.start_date,
                'end_date': self.end_date,
                'company_id': self.company_id.id
            })
            if item_id:
                return item_id.action_print_report_po_xlsx()
        return True