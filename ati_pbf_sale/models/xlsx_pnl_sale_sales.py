from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

class pnl_sales_report_preview(models.Model):
    _name = 'pnl.sales.report.preview'

    def func_print(self):
        return {
            'type': 'ir.actions.act_url',
            'url' : '/pnl_sale_sales_report/%s' % (self.id),
            'target' : 'new',
        }

    def func_cancel(self):
        form_view_id = self.env['ir.model.data']._xmlid_to_res_id('ati_pbf_sale.wizard_pnl_sale_sales_form')
        return {
            'name': 'Laporan Laba/Rugi Penjualan Per Sales Produk',
            'view_type': 'form',
            'view_mode': 'form',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.pnl.sale.sales',
            'views': [[form_view_id, 'form']],
            'target': 'new',
        }

    name = fields.Char(string='Name', default='Laporan Laba/Rugi Penjualan Per Sales Produk')
    sales_person = fields.Many2one('hr.employee', string='Sales Person', index=True, tracking=1)
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    sales = fields.Char(string='Sales Person')
    pnl_sales_preview_ids = fields.One2many('pnl.sales.report.preview.line', 'pnl_sales_preview_id', string='Pnl Sales Preview Ids' )


class pnl_sales_report_preview_line(models.Model):
    _name = 'pnl.sales.report.preview.line'

    pnl_sales_preview_id = fields.Many2one('pnl.sales.report.preview', string='Pnl Sales Preview Id')
    tanggal = fields.Date(string='Tanggal')
    so_id = fields.Many2one('sale.order', string='So Id')
    no_penjualan = fields.Char(string='No. Penjualan')
    no_order = fields.Char(string='No. Order')
    pelanggan = fields.Many2one('res.partner', string='Pelanggan')
    sales_person = fields.Char(string='Sales Person')
    product_id = fields.Many2one('product.product', string='Barang')
    uom_id = fields.Many2one('uom.uom', string='Satuan')
    qty = fields.Float(string='QTY', default=0.0)
    harga_beli = fields.Float(string='Harga Beli', default=0.0)
    harga_jual = fields.Float(string='Harga Jual')
    total_beli = fields.Float(string='Total Beli')
    total_jual = fields.Float(string='Total Jual')
    profit = fields.Float(string='Profit')
    persentase = fields.Float(string='Persentase')

class pnl_profit_report_preview(models.Model):
    _name = 'pnl.profit.report.preview'

    def func_print(self):
        return {
            'type': 'ir.actions.act_url',
            'url' : '/pnl_profit_sales_report/%s' % (self.id),
            'target' : 'new',
        }

    def func_cancel(self):
        form_view_id = self.env['ir.model.data']._xmlid_to_res_id('ati_pbf_sale.wizard_pnl_profit_sales_form')
        return {
            'name': 'Rekap Penjualan Profit Sales',
            'view_type': 'form',
            'view_mode': 'form',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.pnl.profit.sales',
            'views': [[form_view_id, 'form']],
            'target': 'new',
        }

    name = fields.Char(string='Name', default='Laporan Laba/Rugi Penjualan Per Sales Produk')
    sales_person = fields.Many2one('hr.employee', string='Sales Person', index=True, tracking=1)
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    sales = fields.Char(string='Sales Person')
    pnl_profit_preview_ids = fields.One2many('pnl.profit.report.preview.line', 'pnl_profit_preview_id', string='Pnl Profit Preview Ids' )


class pnl_profit_report_preview_line(models.Model):
    _name = 'pnl.profit.report.preview.line'

    pnl_profit_preview_id = fields.Many2one('pnl.profit.report.preview', string='Pnl Profit Preview Id')
    sales_person = fields.Char(string='Sales Person')
    total_beli = fields.Float(string='Total Beli')
    total_jual = fields.Float(string='Total Jual')
    profit = fields.Float(string='Profit')
    persentase = fields.Float(string='Persentase')