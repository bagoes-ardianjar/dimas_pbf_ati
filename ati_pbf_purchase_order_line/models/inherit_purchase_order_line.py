# -*- coding: utf-8 -*-

from odoo import models, fields, api


class InheritPurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # def _get_data_peritem(self):
    #     for this in self :
    #         ati_harga_beli = this.ati_price_unit
    #         diskon = (this.discount_1 + this.discount_2 + this.discount_3 + this.discount_4) * this.ati_price_unit
    #         subtotal_pembelian = (ati_harga_beli - diskon) * self.env['stock.move.line'].sudo().search([('move_id.purchase_line_id','=',this.id)],limit=1).qty_done or 0
    #         this.ati_harga_beli = ati_harga_beli
    #         this.diskon = diskon
    #         this.subtotal_pembelian = subtotal_pembelian


    # modified by ibad
    discount_1 = fields.Float('(Percent) Discount 1')
    discount_2 = fields.Float('(Percent) Discount 2')
    discount_3 = fields.Float('Discount 3 (Fixed Amount)')
    discount_4 = fields.Float('Discount 4 (Fixed Amount)')
    #
    # outstanding_qty = fields.Integer('Outstanding QTY')
    outstanding_qty = fields.Float('Outstanding Qty', compute='_compute_outstanding_qty')
    hna = fields.Float('HNA')
    description_product = fields.Char('Description')

    # ati_harga_beli = fields.Float(string = "Harga Beli", compute='_get_data_peritem')
    # diskon = fields.Float(string="Diskon", compute='_get_data_peritem')
    # subtotal_pembelian = fields.Float(string="Jumlah Pembelian", compute='_get_data_peritem')


    @api.model
    def create(self, vals):
        if 'product_id' in vals:
            product_id = self.env['product.product'].sudo().search([('id', '=', vals['product_id'])])
            if product_id:
                vals['hna'] = product_id.product_tmpl_id.hna
                # vals['ati_price_unit'] = product_id.product_tmpl_id.hna if product_id.product_tmpl_id.hna > 0 else 0
        po_line = super(InheritPurchaseOrderLine, self).create(vals)
        return po_line

    def write(self, vals):
        res = super(InheritPurchaseOrderLine, self).write(vals)
        if 'product_id' in vals:
            product_id = self.env['product.product'].sudo().search([('id', '=', vals['product_id'])])
            if product_id:
                vals['hna'] = product_id.product_tmpl_id.hna
        return res

    def _compute_outstanding_qty(self):
        for line in self:
            line.outstanding_qty = line.product_uom_qty - (line.qty_received or 0)

    @api.onchange('product_id')
    def onchange_hna(self):
        for rec in self:
            if rec.product_id.product_tmpl_id.hna:
                rec.hna = rec.product_id.product_tmpl_id.hna
            elif rec.product_id.hna:
                rec.hna = rec.product_id.hna
            else:
                rec.hna = False
            if self._origin.id != False:
                update_data = "update purchase_order_line set hna = {_hna}" \
                              "where id = {_id}".format(_hna=rec.hna,_id=rec._origin.id)
                self._cr.execute(update_data)

            if rec.product_id.description:
                rec.description_product = rec.product_id.description
            else:
                rec.description_product = ''

    # @api.onchange('discount_1')
    # def onchange_subtotal(self):
    #     for rec in self:
    #         rec.line_sub_total = rec.discount_1

    @api.depends('qty_received_method', 'qty_received_manual')
    def _compute_qty_received(self):
        res = super()._compute_qty_received()
        for line in self:
            if line.move_ids:
                for move in line.move_ids:
                    if move.picking_id:
                        for picking in move.picking_id:
                            if picking.is_return == True:
                                if picking.state == 'done':
                                    line.qty_received = line.product_qty - move.product_uom_qty
        return res


class InheritProductTemplate(models.Model):
    _inherit = 'product.template'

    description = fields.Text(
        'Description', translate=True)

class InheritProductProduct(models.Model):
    _inherit = 'product.product'

    price_include_ppn = fields.Float('Price Include', related='seller_ids.price_include_ppn')
    price = fields.Float('Price Exclude', related='seller_ids.price')
    discount_1 = fields.Integer('Diskon 1', related='seller_ids.discount_1')
    discount_2 = fields.Integer('Diskon 2', related='seller_ids.discount_2')
    discount_3 = fields.Integer('Diskon 3', related='seller_ids.discount_3')
    discount_4 = fields.Integer('Diskon 4', related='seller_ids.discount_4')
    # hna = fields.Char('HNA')
    # activate_product = fields.Boolean('Active', default=False, related='product_tmpl_id.activate_product')
