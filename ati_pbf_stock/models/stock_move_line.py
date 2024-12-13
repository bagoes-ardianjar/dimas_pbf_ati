from odoo import models, fields, _, api, exceptions
from datetime import datetime, timedelta
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError, ValidationError, Warning, RedirectWarning
import math



# batch_on_location_id = None

class StockMoveLineIb(models.Model):
    _inherit = 'stock.move.line'
    _description = 'Product Moves (Stock Move Line)'

    def _update_batch_expiration_date(self):
        self._cr.execute("""(
            select 
                a.product_id as product_id,
                a.lot_id as lot_id, 
                a.expiration_date as expiration_date
            from stock_move_line a
                join stock_picking b on b.id = a.picking_id 
            where lower(b.picking_type_id_name) = 'internal transfers'
            order by a.id asc
        )""")
        data_move_line=self._cr.dictfetchall()
        for data in data_move_line:
            expiration_date = data.get('expiration_date')

            if expiration_date and isinstance(expiration_date, datetime):
                expiration_date_new = expiration_date.date()

            product_id = data.get('product_id')
            lot_id = data.get('lot_id')
            # update_data = "update stock_production_lot set expiration_date = {_expiration_date} " \
            #               "where product_id = {_product_id} and id = {_lot_id}".format(_expiration_date=expiration_date_new,_product_id=product_id,_lot_id=lot_id)
            # self._cr.execute(update_data)
            # self._cr.commit()
            update_data = """
                       UPDATE stock_production_lot
                       SET expiration_date = %s
                       WHERE product_id = %s AND id = %s
                   """
            self._cr.execute(update_data, (expiration_date, product_id, lot_id))
            self._cr.commit()
        return True

    # @api.depends('move_id.sale_line_id.harga_satuan_baru')
    # def get_harga_satuan(self):
    #     for this in self:
    #         this.harga_satuan = this.move_id.sale_line_id.harga_satuan_baru

    def get_harga_satuan(self):
        for this in self:
            harga_satuan_lama = 0
            harga_satuan = 0
            if this.move_id.id != False:
                if this.move_id.sale_line_id.id != False:
                    # harga_satuan = (this.move_id.sale_line_id.price_unit + this.move_id.sale_line_id.product_margin_amount + ((this.move_id.sale_line_id.price_unit + this.move_id.sale_line_id.product_margin_amount)*this.move_id.sale_line_id.additional_margin))
                    harga_satuan_lama = ((round(this.move_id.sale_line_id.price_unit, 2)) + (
                        round(this.move_id.sale_line_id.product_margin_amount, 2))) + (((round(
                        this.move_id.sale_line_id.price_unit, 2)) + (round(
                        this.move_id.sale_line_id.product_margin_amount,
                        2))) * this.move_id.sale_line_id.additional_margin)
                    pecahan = harga_satuan_lama % 1
                    satuan = harga_satuan_lama - pecahan

                    if pecahan > 0 or satuan > 0:
                        harga_satuan = math.ceil(harga_satuan_lama / 50) * 50
                        this.harga_satuan = harga_satuan
                    else:
                        harga_satuan = harga_satuan_lama
                        this.harga_satuan = harga_satuan
                elif this.move_id.purchase_line_id.id != False:
                    harga_satuan = this.move_id.purchase_line_id.ati_price_unit
                this.harga_satuan = harga_satuan

    def get_discount_amount(self):
        for this in self:
            discount_amount = 0
            if this.move_id.id != False:
                if this.move_id.sale_line_id.id != False:
                    discount_amount = this.move_id.sale_line_id.discount_amount
                elif this.move_id.purchase_line_id.id != False:
                    ati_harga_unit = this.move_id.purchase_line_id.ati_price_unit
                    line_discount_1 = ati_harga_unit * this.move_id.purchase_line_id.discount_1 / 100.0 if this.move_id.purchase_line_id.discount_1 else 0.0
                    ati_harga_unit = ati_harga_unit - line_discount_1
                    line_discount_2 = ati_harga_unit * this.move_id.purchase_line_id.discount_2 / 100.0 if this.move_id.purchase_line_id.discount_2 else 0.0
                    ati_harga_unit = ati_harga_unit - line_discount_2
                    line_discount_3 = this.move_id.purchase_line_id.discount_3 if this.move_id.purchase_line_id.discount_3 else 0.0
                    ati_harga_unit = ati_harga_unit - line_discount_3
                    line_discount_4 = this.move_id.purchase_line_id.discount_4 if this.move_id.purchase_line_id.discount_4 else 0.0
                    ati_harga_unit = ati_harga_unit - line_discount_4
                    discount_amount = (line_discount_1 + line_discount_2 + line_discount_3 + line_discount_4)
            this.discount_amount = discount_amount


    # def get_discount_amount(self):
    #     for this in self:
    #         discount_amount = 0
    #         if this.move_id.id != False:
    #             if this.move_id.sale_line_id.id != False:
    #                 discount_amount = this.move_id.sale_line_id.discount_amount
    #         this.discount_amount = discount_amount

    def get_price_subtotal(self):
        price_subtotal = 0
        for this in self:
            if this.move_id.id != False:
                if this.move_id.sale_line_id.id != False:
                    price_subtotal = (round(this.harga_satuan,6) - round(this.discount_amount,6)) * this.qty_done
                elif this.move_id.purchase_line_id.id != False:
                    price_subtotal = (round(this.harga_satuan,6) - round(this.discount_amount,6)) * this.qty_done
            this.price_subtotal = price_subtotal

    def get_tax(self):
        for this in self:
            tax = 0
            if this.move_id.id != False:
                if this.move_id.sale_line_id.id != False:
                    tax = this.move_id.sale_line_id.tax_id.amount
            this.tax = tax

    def get_tax_ids(self):
        for this in self:
            tax = 0
            if this.move_id.id != False:
                if this.move_id.sale_line_id.id != False:
                    tax = this.move_id.sale_line_id.tax_id
                elif this.move_id.purchase_line_id.id != False:
                    tax = this.move_id.purchase_line_id.taxes_id
                else:
                    tax = False
            else:
                tax = False
            this.tax_ids = tax

    def get_global_diskon_line(self):
        total_line = []
        for this in self:
            sml = self.env['stock.move.line'].sudo().search([('id', '=', this.id)])
            for line in sml:
                if line.price_subtotal > 0:
                    total_line.append(line.id)
        for this in self:
            if this.move_id.sale_line_id.id != False:
                if this.move_id.sale_line_id.order_id.global_discount > 0 and len(total_line) > 0:
                    global_diskon_line = this.move_id.sale_line_id.order_id.global_discount / len(total_line)
                else:
                    global_diskon_line = 0
            elif this.move_id.purchase_line_id.id != False:
                if this.move_id.purchase_line_id.order_id.total_global_discount > 0 and len(total_line) > 0:
                    global_diskon_line = this.move_id.purchase_line_id.order_id.total_global_discount / len(total_line)
                else:
                    global_diskon_line = 0
            else:
                global_diskon_line = 0
            this.global_diskon_line = global_diskon_line

    def _compute_tax_line(self):
        for this in self:
            tax_ids = []
            total_tax_perline = 0
            for tax in this.tax_ids:
                if tax.id not in tax_ids:
                    tax_per_line = (this.price_subtotal - this.global_diskon_line) * tax.amount / 100
                    total_tax_perline += tax_per_line
                    tax_ids.append(tax.id)
            this.total_tax = round(total_tax_perline,6)

    harga_satuan = fields.Float(string="Harga Satuan", compute=get_harga_satuan)
    discount_amount = fields.Float(string="Discount Amount", compute=get_discount_amount)
    price_subtotal = fields.Float(string="Net Total", compute=get_price_subtotal)
    tax = fields.Float(string="Tax", compute=get_tax)
    tax_ids = fields.Many2many('account.tax', string='Taxes', compute=get_tax_ids)
    global_diskon_line = fields.Float(string="Global Diskon Line", compute=get_global_diskon_line)
    total_tax = fields.Float(string='Total Tax', compute=_compute_tax_line)

    # @api.constrains('product_uom_qty')
    # def _check_reserved_done_quantity(self):
    #     for move_line in self:
    #         print("xxxxxxxx", float_is_zero(move_line.product_uom_qty, precision_digits=self.env['decimal.precision'].precision_get('Product Unit of Measure')))
    #         if move_line.state == 'done' and not float_is_zero(move_line.product_uom_qty, precision_digits=self.env['decimal.precision'].precision_get('Product Unit of Measure')):
    #             raise ValidationError(_('A done move line should never have a reserved quantity.'))

    @api.depends('picking_id.picking_type_id.is_receipt')
    def _dynamic_domain_of_product(self):
        if 'params' in self._context:
            if self._context['params']['model'] == 'stock.picking':
                if 'id' in self._context['params']:
                    sml = self.search([('picking_id', '=', self._context['params']['id'])])
                    for sml_ in sml:
                        for picking_id in sml_.picking_id:
                            for picking_type_id in picking_id.picking_type_id:
                                if not picking_type_id.is_receipt:
                                    return "[('type', '!=', 'service'), '|', ('company_id', '=', False), ('company_id', '=', company_id), ('id', '=', product_on_location_id)]"
                                elif picking_type_id.is_receipt:
                                    return "[('type', '!=', 'service'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]"

    @api.depends('picking_id.picking_type_id.is_receipt')
    def _dynamic_domain_of_lot_id(self):
        if 'params' in self._context:
            if self._context['params']['model'] == 'stock.picking':
                if 'id' in self._context['params']:
                    sm = self.search([('picking_id', '=', self._context['params']['id'])])
                    for sm_ in sm:
                        for picking_id in sm_.picking_id:
                            for picking_type_id in picking_id.picking_type_id:
                                if not picking_type_id.is_receipt:
                                    return "[('product_id', '=', product_id), ('company_id', '=', company_id), ('id', '=', batch_on_location_id)]"
                                elif picking_type_id.is_receipt:
                                    return "[('product_id', '=', product_id), ('company_id', '=', company_id)]"


    def get_lot_helper_ids(self):
        for this in self:
            if this.product_id:
                lot = self.env['stock.production.lot'].sudo().search([('product_id', '=', this.product_id.id)])
                this.lot_helper_ids = [(6,0,lot.ids)]
            else:
                this.lot_helper_ids = None


    @api.model
    def get_user(self):
        return self.env.user.id

    @api.onchange('user_helper_id')
    def func_onchange_user_helper_id(self):
        self.get_lot_helper_ids()

    @api.onchange('product_id')
    def func_onchange_product_id_other(self):
        self.get_lot_helper_ids()


    product_on_location_id = fields.Many2many('product.product', 'product_on_location_id_rel_move_line',
                                              compute='_compute_product_batch_on_location_id', string='product_on_location_id', readonly=False)
    batch_on_location_id = fields.Many2many('stock.production.lot', 'batch_on_location_id_rel_move_line',
                                            compute='_compute_product_batch_on_location_id', string='batch_on_location_id', readonly=False, store=True)
    product_id = fields.Many2one('product.product', 'Product', ondelete="cascade", check_company=True, domain=_dynamic_domain_of_product)
    # lot_id = fields.Many2one(
    #     'stock.production.lot', 'Batch',
    #     domain=_dynamic_domain_of_lot_id, check_company=True)
    lot_id = fields.Many2one('stock.production.lot', 'Batch', check_company=True)
    user_helper_id = fields.Many2one('res.users', default=get_user)
    lot_helper_ids = fields.Many2many('stock.production.lot', 'stock_move_line_production_lot_helper_rel', 'stock_move_line_id', 'lot_id',
                                      compute=get_lot_helper_ids)

    @api.depends('picking_id.location_id')
    def _compute_product_batch_on_location_id(self):
        for this in self:
            stock_location = []
            for picking in self.picking_id:
                stock_location.append([location_id.id for location_id in picking.location_id])

            if stock_location:
                self.product_on_location_id = self.env['stock.location'].search([
                    ('id', 'in', stock_location[0])
                ]).quant_ids.product_id
                get_data = self.env['stock.location'].search([
                    ('id', 'in', stock_location[0]),
                    ('company_id', '=', self.env.company.id)
                ]).quant_ids.lot_id.ids
                # ins_values = ",".join(["({},{})".format(
                #     this.id,
                #     data
                # ) for data in get_data])
                # if len(ins_values) > 0:
                #     delete = "delete from batch_on_location_id_rel_move_line where stock_move_line_id = {_sm}".format(_sm=this.id)
                #     self._cr.execute(delete)
                #     query = "insert into batch_on_location_id_rel_move_line (stock_move_line_id, stock_production_lot_id) values {_vals}".format(_vals=ins_values)
                #     self._cr.execute(query)
                # else:
                #     self.batch_on_location_id = None
                # self.batch_on_location_id = self.env['stock.location'].search([
                #     ('id', 'in', stock_location[0]),
                #     ('company_id', '=', self.env.company.id)
                # ]).quant_ids.lot_id
                if this._origin.id == False:
                    self.batch_on_location_id = self.env['stock.location'].search([
                        ('id', 'in', stock_location[0]),
                        ('company_id', '=', self.env.company.id)
                    ]).quant_ids.lot_id
                else:
                    self._cr.execute("""(select id from stock_move_line where id = {_id} and product_uom_qty > 0)""".format(_id=this._origin.id))
                    fet = [x[0] for x in self._cr.fetchall()]
                    if len(fet) > 0:
                        self.batch_on_location_id = self.env['stock.location'].search([
                            ('id', 'in', stock_location[0]),
                            ('company_id', '=', self.env.company.id)
                        ]).quant_ids.lot_id

