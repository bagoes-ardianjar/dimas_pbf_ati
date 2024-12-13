import logging
from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError, AccessError

_logger = logging.getLogger(__name__)

class margin_product(models.Model):
    _name = 'margin.product'
    _description = 'Margin Product'

    name = fields.Float('Margin')

    def write(self, vals):
        res = super(margin_product, self).write(vals)
        if 'name' in vals:
            for this in self:
                product_template = self.env['product.template'].sudo().search([('margin', '=', this.id)])
                so_line = self.env['sale.order.line'].sudo().search([('product_id.product_tmpl_id', 'in', product_template.ids)])
                for l in so_line:
                    if l.order_id.state == 'draft':
                        if l.is_lock_price != True:
                            if not l.order_id.partner_id.margin_ids or l.order_id.is_pasien == True:
                                if not this.margin:
                                    l.product_margin_percent = '0%'
                                else:
                                    l.product_margin_percent = str(this.margin.name) + '%'
                            else:
                                margin_from_customer = 0
                                for m_margin in l.order_id.partner_id.margin_ids:
                                    margin_from_customer += m_margin.value
                                    l.product_margin_percent = str(margin_from_customer) + '%'
                        else:
                            pass
                    else:
                        pass
        return res
    
    def unlink(self):
        return super(margin_product, self).unlink()