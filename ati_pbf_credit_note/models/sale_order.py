from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Sale(models.Model):
    _inherit = 'sale.order'


    # sales reference, global discount
    def _create_invoices(self, grouped=False, final=False, date=None):
        res = super(Sale, self)._create_invoices(grouped, final, date)
        
        if self._context.get('active_model') == 'sale.order':
            ids = self.env['sale.order'].browse(self._context.get('active_ids', []))
            global_discount = 0

            if ids:
                ref = []
                for i in ids:
                    ref.append(i.name)
                    global_discount += i.global_discount
                    res.sales_person = i.sales_person.id

                res.global_order_discount = global_discount
                res.sales_reference = ', '.join(ref)
                res.is_from_so = True
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        res.update({
            'discount': self.discount,
            'additional_margin': self.additional_margin,
            'discount_amount': self.discount_amount,
            'product_margin_percent': self.product_margin_percent,
            'product_margin_amount': self.product_margin_amount,
            'harga_satuan': self.harga_satuan_baru or 0,
            'ati_price_unit': self.price_unit
        })
        return res