from odoo import models, fields, _, api

class Koli(models.Model):
    _name = 'stock.picking.koli'
    _description = 'Koli'

    # koli
    product_name_koli = fields.Many2one('product.product', string='Product Name')
    nomor_koli = fields.Char('Nomor Koli')
    # picking_id = fields.Many2one('stock.picking', string='Nomor DO')
    # nomor_do = fields.Char(string='Nomor DO')
    jumlah_koli = fields.Integer('Jumlah Koli', related='picking_id.jumlah_koli')
    berat_koli = fields.Char('Berat Koli')
    jenis_koli = fields.Char('Jenis Koli')
    picking_id = fields.Many2one('stock.picking', string='Nomor DO')
    # picking_id = fields.Char(string='Nomor DO')
    batch_id = fields.Many2one(
        'stock.picking.batch', string='Batch Transfer',
        check_company=True,
        help='Batch associated to this transfer', copy=False)
