from odoo import models, fields, _, api
from odoo.tools import format_amount

class product(models.Model):
    _inherit = 'product.template'
    _description = 'Product Template'

    # def _construct_tax_string(self, price):
    #     currency = self.currency_id
    #     res = self.taxes_id.compute_all(price, product=self, partner=self.env['res.partner'])
    #
    #     joined = []
    #     included = res['total_included']
    #     if currency.compare_amounts(included, price):
    #         joined.append(_('%s Incl. Taxes', format_amount(self.env, included, currency)))
    #     excluded = res['total_excluded']
    #     if currency.compare_amounts(excluded, price):
    #         joined.append(_('%s Excl. Taxes', format_amount(self.env, excluded, currency)))
    #
    #     if not self.margin:
    #         if not self.taxes_id:
    #             self.write({'list_price': self.standard_price})
    #         elif self.taxes_id:
    #             tax = self.standard_price * self.taxes_id.amount / 100
    #             sell_price = self.standard_price + tax
    #             self.write({'list_price': sell_price - tax})
    #
    #     elif self.margin:
    #         if not self.taxes_id:
    #             margin = self.standard_price*self.margin.name/100
    #             sell_price = self.standard_price + margin
    #
    #             self.write({'list_price': sell_price})
    #         elif self.taxes_id:
    #             margin = (self.standard_price * self.margin.name / 100)
    #             tax = self.standard_price*self.taxes_id.amount/100
    #
    #             sell_price = self.standard_price + margin + tax
    #
    #             self.write({'list_price': sell_price - tax})
    #     if joined:
    #         tax_string = f"(= {', '.join(joined)})"
    #     else:
    #         tax_string = " "
    #
    #     return tax_string

    # added by ibad
    # @api.onchange('standard_price','margin','taxes_id')
    # def change_sell_price(self):
    #     if not self.margin:
    #         if not self.taxes_id:
    #             self.write({'list_price': self.standard_price})
    #         elif self.taxes_id:
    #             tax = self.standard_price * self.taxes_id.amount / 100
    #             sell_price = self.standard_price + tax
    #             self.write({'list_price': sell_price - tax})
    #
    #     elif self.margin:
    #         if not self.taxes_id:
    #             margin = self.standard_price*self.margin.name/100
    #             sell_price = self.standard_price + margin
    #
    #             self.write({'list_price': sell_price})
    #         elif self.taxes_id:
    #             margin = (self.standard_price * self.margin.name / 100)
    #             tax = self.standard_price*self.taxes_id.amount/100
    #
    #             sell_price = self.standard_price + margin + tax
    #
    #             self.write({'list_price': sell_price - tax})


    def name_get(self):
        # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
        self.browse(self.ids).read(['name', 'pabrik_reference'])
        return [(template.id, '%s%s' % (template.pabrik_reference and '[%s] ' % template.pabrik_reference or '', template.name))
                for template in self]

    def _get_mapped_attribute_names(self, parent_combination=None):
        """ The name of every attribute values based on their id,
        used to explain in the interface why that combination is not available
        (e.g: Not available with Color: Black).

        It contains both attribute value names from this product and from
        the parent combination if provided.
        """
        self.ensure_one()
        all_product_attribute_values = self.valid_product_template_attribute_line_ids.product_template_value_ids

        if parent_combination:
            all_product_attribute_values |= parent_combination

        return {
            attribute_value.id: attribute_value.display_name
            for attribute_value in all_product_attribute_values
        }

class product_product(models.Model):
    _inherit = 'product.product'
    _description = 'Product'

    def name_get(self):
        # TDE: this could be cleaned a bit I think

        def _name_get(d):
            name = d.get('name', '')
            code = self._context.get('display_default_code', True) and d.get('pabrik_reference', False) or False
            if code:
                name = '[%s] %s' % (code, name)
            return (d['id'], name)

        partner_id = self._context.get('partner_id')
        if partner_id:
            partner_ids = [partner_id, self.env['res.partner'].browse(partner_id).commercial_partner_id.id]
        else:
            partner_ids = []
        company_id = self.env.context.get('company_id')

        # all user don't have access to seller and partner
        # check access and use superuser
        self.check_access_rights("read")
        self.check_access_rule("read")

        result = []

        # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
        # Use `load=False` to not call `name_get` for the `product_tmpl_id`
        self.sudo().read(['name', 'pabrik_reference', 'product_tmpl_id'], load=False)

        product_template_ids = self.sudo().mapped('product_tmpl_id').ids

        if partner_ids:
            supplier_info = self.env['product.supplierinfo'].sudo().search([
                ('product_tmpl_id', 'in', product_template_ids),
                ('name', 'in', partner_ids),
            ])
            # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
            # Use `load=False` to not call `name_get` for the `product_tmpl_id` and `product_id`
            supplier_info.sudo().read(['product_tmpl_id', 'product_id', 'product_name', 'product_code'], load=False)
            supplier_info_by_template = {}
            for r in supplier_info:
                supplier_info_by_template.setdefault(r.product_tmpl_id, []).append(r)
        for product in self.sudo():
            variant = product.product_template_attribute_value_ids._get_combination_name()

            name = variant and "%s (%s)" % (product.name, variant) or product.name
            sellers = self.env['product.supplierinfo'].sudo().browse(self.env.context.get('seller_id')) or []
            if not sellers and partner_ids:
                product_supplier_info = supplier_info_by_template.get(product.product_tmpl_id, [])
                sellers = [x for x in product_supplier_info if x.product_id and x.product_id == product]
                if not sellers:
                    sellers = [x for x in product_supplier_info if not x.product_id]
                # Filter out sellers based on the company. This is done afterwards for a better
                # code readability. At this point, only a few sellers should remain, so it should
                # not be a performance issue.
                if company_id:
                    sellers = [x for x in sellers if x.company_id.id in [company_id, False]]
            if sellers:
                for s in sellers:
                    seller_variant = s.product_name and (
                            variant and "%s (%s)" % (s.product_name, variant) or s.product_name
                    ) or False
                    mydict = {
                        'id': product.id,
                        'name': seller_variant or name,
                        'pabrik_reference': s.product_code or product.pabrik_reference,
                    }
                    temp = _name_get(mydict)
                    if temp not in result:
                        result.append(temp)
            else:
                mydict = {
                    'id': product.id,
                    'name': name,
                    'pabrik_reference': product.product_tmpl_id.pabrik_reference # product.default_code,
                }
                result.append(_name_get(mydict))
        return result