from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.addons import decimal_precision as dp


class SaleOrderAdl(models.Model):
    _inherit = 'sale.order'
    _description = 'Sales Order'

    @api.model
    def create(self, vals):
        if 'company_id' in vals:
            self = self.with_company(vals['company_id'])
        # if 'product_id' in vals:
        #     self = self.product_id(vals['product_id'])
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            if 'date_order' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
            vals['name'] = self.env['ir.sequence'].next_by_code('x.self.so', sequence_date=seq_date) or _('New')

        # Makes sure partner_invoice_id', 'partner_shipping_id' and 'pricelist_id' are defined
        if any(f not in vals for f in ['partner_invoice_id', 'partner_shipping_id', 'pricelist_id']):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            addr = partner.address_get(['delivery', 'invoice'])
            vals['partner_invoice_id'] = vals.setdefault('partner_invoice_id', addr['invoice'])
            vals['partner_shipping_id'] = vals.setdefault('partner_shipping_id', addr['delivery'])
            vals['pricelist_id'] = vals.setdefault('pricelist_id', partner.property_product_pricelist.id)
        result = super(SaleOrderAdl, self).create(vals)
        return result