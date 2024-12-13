from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.translate import _

from datetime import datetime
from odoo.exceptions import ValidationError, UserError

import logging

_logger = logging.getLogger(__name__)



class ManageCompanySalesPriceWiz(models.TransientModel):
    _name = "company.sale.price.wiz"
    _description = "Manage Company Sales Price"


    @api.model
    def default_name(self):
        return "You will make the selling price for the company %s" %(self.env.company.name or "")


    name = fields.Char(string='Name',default=default_name)
    sales_price_ids = fields.One2many('company.sale.price.line.wiz','sale_price_id', string='Sales Price') 


    @api.model
    def default_get(self,fields):
        Products = self.env['product.product'].sudo().browse(self.env.context.get('active_ids',[]))
        result = super(ManageCompanySalesPriceWiz, self).default_get(fields)
        result['sales_price_ids'] = [(0,0,{'product_id': line.id,'company_id':self.env.company.id}) for line in Products]
        return result

    def set_company_sales_price(self):
        CompanySalesPrice = self.env['company.sale.price'].sudo()
        for rec in self:
            for line in rec.sales_price_ids:
                if not line.product_id.company_sales_price_ids.filtered(lambda r: r.company_id.id == line.company_id.id and r.is_active):
                    CompanySalesPrice |= CompanySalesPrice.create({
                        'product_id': line.product_id.id,
                        'company_id': line.company_id.id,
                        'is_active': True
                    }) 


class ManageCompanySalesPriceDetailWiz(models.TransientModel):
    _name = "company.sale.price.line.wiz"
    _description = "Manage Company Sales Price Detail"


    sale_price_id = fields.Many2one('company.sale.price.wiz', string='Company Sales Price Detail', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product')
    company_id = fields.Many2one('res.company', string='Company')
    # currency_id = fields.Many2one(related='company_id.currency_id', string='Currency')
    # lst_price = fields.Float('Sales Price',digits='Product Price', compute='', inverse='',help="The sale price is managed from the product. Click on the 'Configure Variants' button to set the company sales prices.")
