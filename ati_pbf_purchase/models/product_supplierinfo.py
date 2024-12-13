from odoo import models, fields, _, api

class product_supplierinfo(models.Model):
    _inherit = 'product.supplierinfo'
    _description = 'product supplier info'

    @api.depends('price')
    def _compute_price_incl_ppn(self):
        for seller_ids in self:
            seller_ids.price_include_ppn = seller_ids.price * 1.11

    # added by ibad ...
    discount_1 = fields.Integer('Discount 1 (%)')
    discount_2 = fields.Integer('Discount 2 (%)')
    discount_3 = fields.Integer('Discount 3')
    discount_4 = fields.Integer('Discount 4')
    effective_date = fields.Datetime('Effective Date')
    price_include_ppn = fields.Float('Price (Include PPN)', compute='_compute_price_incl_ppn', readonly=False)
    hna = fields.Char(compute='_get_hna', string='HNA')

    def _get_hna(self):
        for prd in self.product_tmpl_id:
            self.hna = prd.hna
