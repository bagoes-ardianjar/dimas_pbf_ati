from email.policy import default
from odoo import models, fields, _, api
from dateutil.relativedelta import relativedelta
from datetime import datetime, time, timedelta

class X_price_changes_line(models.Model):
    _name = 'price.changes.line'

    po_id = fields.Many2one("purchase.order","PO", default=lambda self: self.env.user)
    product_id= fields.Many2one("product.product","Product", default=lambda self: self.env.user)
    old_price= fields.Float(string='Old Price')
    new_price= fields.Float(string='New price')
    user_id= fields.Many2one("res.users","User", default=lambda self: self.env.user)
    tanggal=fields.Datetime(string='Date')

class x_po_inherit_price(models.Model):
    _inherit='purchase.order'

    price_history_ids = fields.One2many("price.changes.line","po_id",string ="Price History", compute="_compute_history", store=True)
    
    @api.depends('order_line')
    def _compute_history(self):
        for rec in self:
            if rec.order_line:
                for order in rec.order_line:
                    domain= ['&',
                                            ('po_id', '=', rec.id),
                                            ('product_id', '=', order.product_id.id),
                                        ]
                    history_obj = self.env['price.changes.line'].search(domain, limit=1, order='id desc')
                    
                    if not history_obj:
                        history = [(0,0,{
                                'product_id' : order.product_id.id,
                                'old_price' : 0,
                                'new_price': order.price_unit,
                                'tanggal': datetime.now() + relativedelta(hours=7)
                                })]
                        rec.sudo().write({'price_history_ids': history})
                    
                    if history_obj:
                        if history_obj.new_price != order.price_unit:
                            history = [(0,0,{
                                'product_id' : order.product_id.id,
                                'old_price' : history_obj.new_price,
                                'new_price': order.price_unit,
                                'tanggal': datetime.now() + relativedelta(hours=7)
                                })]
                            rec.sudo().write({'price_history_ids': history})
