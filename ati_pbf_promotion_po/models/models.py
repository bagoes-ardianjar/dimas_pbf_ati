# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime
from datetime import datetime


class ati_pbf_promotion_po(models.Model):
    _name = 'po.promotion'
    _description = 'ati_pbf_promotion_po.ati_pbf_promotion_po'

    name = fields.Char(required=True, translate=True)
    active = fields.Boolean('Active', default=True, help="A program is available for the customers when active")
    rule_id = fields.Many2one('coupon.rule', string="Coupon Rule", ondelete='restrict', required=False)
    reward_id = fields.Many2one('coupon.reward', string="Reward", ondelete='restrict', required=False, copy=False)
    sequence = fields.Integer(copy=False,
        help="Coupon program will be applied based on given sequence if multiple programs are " +
        "defined on same condition(For minimum amount)")
    maximum_use_number = fields.Integer(help="Maximum number of sales orders in which reward can be provided")
    program_type = fields.Selection([
        ('promotion_program', 'Promotional Program'),
        ('coupon_program', 'Coupon Program'),
        ],
        help="""A promotional program can be either a limited promotional offer without code (applied automatically)
                or with a code (displayed on a magazine for example) that may generate a discount on the current
                order or create a coupon for a next order.

                A coupon program generates coupons with a code that can be used to generate a discount on the current
                order or create a coupon for a next order.""")
    promo_code_usage = fields.Selection([
        ('no_code_needed', 'Automatically Applied'),
        ('code_needed', 'Use a code')],
        help="Automatically Applied - No code is required, if the program rules are met, the reward is applied (Except the global discount or the free shipping rewards which are not cumulative)\n" +
             "Use a code - If the program rules are met, a valid code is mandatory for the reward to be applied\n")
    promo_code = fields.Char('Promotion Code', copy=False,
        help="A promotion code is a code that is associated with a marketing discount. For example, a retailer might tell frequent customers to enter the promotion code 'THX001' to receive a 10%% discount on their whole order.")
    promo_applicability = fields.Selection([
        ('on_current_order', 'Apply On Current Order'),
        ('on_next_order', 'Send a Coupon')],
        default='on_current_order', string="Applicability")
    coupon_ids = fields.One2many('coupon.coupon', 'program_id', string="Generated Coupons", copy=False)
    coupon_count = fields.Integer("Coupon count")
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(string="Currency", related='company_id.currency_id', readonly=True)
    validity_duration = fields.Integer(default=30,
        help="Validity duration for a coupon after its generation")
    total_order_count = fields.Integer("Total Order Count")
    rule_products_domain = fields.Char(string="Based on Products", default=[['sale_ok', '=', True]],
                                       help="On Purchase of selected product, reward will be given")

    rule_min_quantity = fields.Integer(string="Minimum Quantity", default=1,
                                       help="Minimum required product quantity to get the reward")
    rule_minimum_amount = fields.Float(default=0.0, help="Minimum required amount to get the reward")
    rule_minimum_amount_tax_inclusion = fields.Selection([
        ('tax_included', 'Tax Included'),
        ('tax_excluded', 'Tax Excluded')], default="tax_excluded")
    reward_type = fields.Selection([
        ('discount', 'Discount'),
        ('product', 'Free Product'),
    ], string='Reward Type', default='discount',
        help="Discount - Reward will be provided as discount.\n" +
             "Free Product - Free product will be provide as reward \n" +
             "Free Shipping - Free shipping will be provided as reward (Need delivery module)")
    discount_line_product_id = fields.Many2one('product.product', readonly=False,
        help='Product used in the sales order to apply the discount.')
    reward_product_id = fields.Many2one('product.product', string="Free Product",
        help="Reward Product")
    reward_product_quantity = fields.Integer(string="Quantity", default=1, help="Reward product quantity")
    reward_product_uom_id = fields.Many2one(related='reward_product_id.product_tmpl_id.uom_id', string='Unit of Measure', readonly=True)
    discount_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed Amount')], default="percentage")

    discount_percentage = fields.Float(string="Discount",
        help='The discount in percentage, between 1 and 100')
    discount_fixed_amount = fields.Float(string="Fixed Amount", help='The discount in fixed amount')
    discount_apply_on = fields.Selection([
        ('on_order', 'On Order'),
        ('cheapest_product', 'On Cheapest Product'),
        ('specific_products', 'On Specific Products')], default="on_order",
        help="On Order - Discount on whole order\n" +
        "Cheapest product - Discount on cheapest product of the order\n" +
        "Specific products - Discount on selected specific products")
    discount_specific_product_ids = fields.Many2many('product.template', string="Products",
        help="Products that will be discounted if the discount is applied on specific products")
    discount_max_amount = fields.Float(default=0,
        help="Maximum amount of discount that can be provided")
    rule_date_from = fields.Datetime(string="Start Date", help="Coupon program start date")
    rule_date_to = fields.Datetime(string="End Date", help="Coupon program end date")
    rule_partners_domain = fields.Many2many('res.partner',


                                            string="Based on Customers", help="Coupon program will work for selected customers only")
    rule_products_domain = fields.Char(string="Based on Products", default=[['sale_ok', '=', True]], help="On Purchase of selected product, reward will be given")
    rule_min_quantity = fields.Integer(string="Minimum Quantity", default=1,
        help="Minimum required product quantity to get the reward")
    rule_minimum_amount = fields.Float(default=0.0, help="Minimum required amount to get the reward")
    rule_minimum_amount_tax_inclusion = fields.Selection([
        ('tax_included', 'Tax Included'),
        ('tax_excluded', 'Tax Excluded')], default="tax_excluded")
    product_ids = fields.Many2many('product.product', string="Products",
        help="Products that will be discounted if the discount is applied on specific products")
    status = fields.Boolean('Is active')
    is_duplicates = fields.Boolean("Duplicates")
    id_duplicates = fields.Char("ID duplicates")
    id_duplicates_product = fields.Char("ID duplicates products")
    remaining_use_promotion = fields.Integer('Remaining use', readonly=True, force_save=True)



class action_promotion_po(models.Model):
    _inherit = 'purchase.order'

    def action_promotion(self):
        product = []
        promotion = self.env['po.promotion'].search([('status', '=', True)])
        for promotion_product in promotion:
            if promotion_product.reward_type == 'product':
                for order_line in self.order_line:
                    if (promotion_product.rule_partners_domain and promotion_product.product_ids):
                        if promotion_product.rule_date_from and promotion_product.rule_date_to:
                                for product_ids_list in promotion_product.product_ids:
                                    # filter = promotion_product.filtered(lambda r: product_ids_list.id == rec.product_id.id)
                                    free_product = product_ids_list.id
                                    for customer_id in promotion_product.rule_partners_domain:
                                        customer = customer_id.id

                                        if order_line.product_id.id == free_product and customer == self.partner_id.id and (order_line.product_qty >= promotion_product.rule_min_quantity or order_line.line_sub_total >= promotion_product.rule_minimum_amount):
                                                date_order = datetime.strptime(str(order_line.date_order),
                                                                               "%Y-%m-%d %H:%M:%S")
                                                start_date = datetime.strptime(str(promotion_product.rule_date_from),
                                                                               "%Y-%m-%d %H:%M:%S")
                                                end_date = datetime.strptime(str(promotion_product.rule_date_to),
                                                                             "%Y-%m-%d %H:%M:%S")

                                                if date_order <= end_date and date_order >= start_date:
                                                    if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':
                                                        taxes = order_line.taxes_id.name
                                                        if taxes:
                                                            taxes = taxes.rstrip(taxes[-1])
                                                        result = order_line.line_sub_total * int(taxes) / 100
                                                        total = result + order_line.line_sub_total
                                                        if total >= promotion_product.rule_minimum_amount:
                                                            if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                                promotion_product.remaining_use_promotion = promotion_product.maximum_use_number - 1

                                                                product.append((0, 0, {
                                                                    'product_id': promotion_product.discount_line_product_id.id,
                                                                    'description_product': promotion_product.discount_line_product_id.name + '- ' + (
                                                                        product_ids_list.name),
                                                                    'product_qty': promotion_product.reward_product_quantity,
                                                                    'price_unit': 0, }))
                                                            elif promotion_product.maximum_use_number == 0:
                                                                product.append((0, 0, {
                                                                    'product_id': promotion_product.discount_line_product_id.id,
                                                                    'description_product': promotion_product.discount_line_product_id.name + '- ' + (
                                                                        product_ids_list.name),
                                                                    'product_qty': promotion_product.reward_product_quantity,
                                                                    'price_unit': 0, }))

                                                    elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':
                                                        total = order_line.line_sub_total
                                                        if total >= promotion_product.rule_minimum_amount:
                                                            if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                                promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1
                                                                product.append((0, 0, {
                                                                    'product_id': promotion_product.discount_line_product_id.id,
                                                                    'description_product': promotion_product.discount_line_product_id.name + '(Main product' + ' : ' + (
                                                                        product_ids_list.name) + ')',
                                                                    'product_qty': promotion_product.reward_product_quantity,
                                                                    'price_unit': 0, }))
                                                            elif promotion_product.maximum_use_number == 0:
                                                                product.append((0, 0, {
                                                                    'product_id': promotion_product.discount_line_product_id.id,
                                                                    'description_product': promotion_product.discount_line_product_id.name + '- ' + (
                                                                        product_ids_list.name),
                                                                    'product_qty': promotion_product.reward_product_quantity,
                                                                    'price_unit': 0, }))
                        else:
                            for product_ids_list in promotion_product.product_ids:
                                # filter = promotion_product.filtered(lambda r: product_ids_list.id == rec.product_id.id)
                                free_product = product_ids_list.id
                                customer = []
                                for customer_id in promotion_product.rule_partners_domain:
                                    customer = customer_id.id
                                    if order_line.product_id.id == free_product and customer == self.partner_id.id and (int(order_line.product_qty) >= promotion_product.rule_min_quantity or order_line.line_sub_total  >= promotion_product.rule_minimum_amount ):
                                        if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':
                                            taxes = order_line.taxes_id.name
                                            if taxes:
                                                taxes = taxes.rstrip(taxes[-1])
                                            result = order_line.line_sub_total * int(taxes) / 100
                                            total = result + order_line.line_sub_total
                                            if total >= promotion_product.rule_minimum_amount :
                                                if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                    promotion_product.remaining_use_promotion = promotion_product.maximum_use_number - 1

                                                    product.append((0, 0, {
                                                        'product_id': promotion_product.discount_line_product_id.id,
                                                         'description_product' : promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                        'product_qty': promotion_product.reward_product_quantity,
                                                        'price_unit': 0, }))
                                                elif promotion_product.maximum_use_number == 0:
                                                    product.append((0, 0, {
                                                        'product_id': promotion_product.discount_line_product_id.id,
                                                        'description_product': promotion_product.discount_line_product_id.name + '- ' + (
                                                            product_ids_list.name),
                                                        'product_qty': promotion_product.reward_product_quantity,
                                                        'price_unit': 0, }))

                                        elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':
                                            total = order_line.line_sub_total
                                            if total >= promotion_product.rule_minimum_amount:
                                                if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                    promotion_product.remaining_use_promotion = promotion_product.maximum_use_number - 1
                                                    product.append((0, 0, {
                                                        'product_id': promotion_product.discount_line_product_id.id,
                                                        'description_product': promotion_product.discount_line_product_id.name + '(Main product' + ' : ' + (
                                                            product_ids_list.name) + ')',
                                                        'product_qty': promotion_product.reward_product_quantity,
                                                        'price_unit': 0, }))
                                                elif promotion_product.maximum_use_number == 0:
                                                    product.append((0, 0, {
                                                        'product_id': promotion_product.discount_line_product_id.id,
                                                        'description_product': promotion_product.discount_line_product_id.name + '(Main product' + ' : ' + (
                                                            product_ids_list.name) + ')',
                                                        'product_qty': promotion_product.reward_product_quantity,
                                                        'price_unit': 0, }))


                    elif not promotion_product.rule_partners_domain and not promotion_product.product_ids:
                        if promotion_product.rule_date_from and promotion_product.rule_date_to:
                            # print("TIDAK KEDUANYA")
                            for product_ids_list in promotion_product.product_ids:
                                # filter = promotion_product.filtered(lambda r: product_ids_list.id == rec.product_id.id)

                                    if order_line.product_qty >= promotion_product.rule_min_quantity or order_line.line_sub_total >= promotion_product.rule_minimum_amount:
                                        date_order = datetime.strptime(str(order_line.date_order),
                                                                       "%Y-%m-%d %H:%M:%S")
                                        start_date = datetime.strptime(str(promotion_product.rule_date_from),
                                                                       "%Y-%m-%d %H:%M:%S")
                                        end_date = datetime.strptime(str(promotion_product.rule_date_to),
                                                                     "%Y-%m-%d %H:%M:%S")
                                        if date_order <= end_date and date_order >= start_date:
                                            if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':
                                                taxes = order_line.taxes_id.name
                                                if taxes:
                                                    taxes = taxes.rstrip(taxes[-1])
                                                result = order_line.line_sub_total * int(taxes) / 100
                                                total = result + order_line.line_sub_total
                                                if total >= promotion_product.rule_minimum_amount:
                                                    if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                        promotion_product.remaining_use_promotion = promotion_product.maximum_use_number - 1

                                                        product.append((0, 0, {
                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                            'description_product': promotion_product.discount_line_product_id.name + '- ' + (
                                                                product_ids_list.name),
                                                            'product_qty': promotion_product.reward_product_quantity,
                                                            'price_unit': 0, }))
                                                    elif promotion_product.maximum_use_number == 0:
                                                        product.append((0, 0, {
                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                            'description_product': promotion_product.discount_line_product_id.name + '(Main product' + ' : ' + (
                                                                product_ids_list.name) + ')',
                                                            'product_qty': promotion_product.reward_product_quantity,
                                                            'price_unit': 0, }))
                                            elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':
                                                total = order_line.line_sub_total
                                                if total >= promotion_product.rule_minimum_amount:
                                                    if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                        promotion_product.remaining_use_promotion = promotion_product.maximum_use_number - 1
                                                        product.append((0, 0, {
                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                            'description_product': promotion_product.discount_line_product_id.name + '(Main product' + ' : ' + (
                                                                product_ids_list.name) + ')',
                                                            'product_qty': promotion_product.reward_product_quantity,
                                                            'price_unit': 0, }))
                                                    elif promotion_product.maximum_use_number == 0:
                                                        product.append((0, 0, {
                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                            'description_product': promotion_product.discount_line_product_id.name + '(Main product' + ' : ' + (
                                                                product_ids_list.name) + ')',
                                                            'product_qty': promotion_product.reward_product_quantity,
                                                            'price_unit': 0, }))

                        else:
                            for product_ids_list in promotion_product.product_ids:
                                # filter = promotion_product.filtered(lambda r: product_ids_list.id == rec.product_id.id)
                                free_product = product_ids_list.id
                                customer = []
                                for customer_id in promotion_product.rule_partners_domain:
                                    customer = customer_id.id
                                    if order_line.product_id.id == free_product and customer == self.partner_id.id and (
                                            int(order_line.product_qty) >= promotion_product.rule_min_quantity or order_line.line_sub_total >= promotion_product.rule_minimum_amount):
                                        if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':
                                            taxes = order_line.taxes_id.name
                                            if taxes:
                                                taxes = taxes.rstrip(taxes[-1])
                                            result = order_line.line_sub_total * int(taxes) / 100
                                            total = result + order_line.line_sub_total
                                            if total >= promotion_product.rule_minimum_amount:
                                                if promotion_product.remaining_use_promotion > 0:
                                                    promotion_product.remaining_use_promotion = promotion_product.maximum_use_number - 1

                                                    product.append((0, 0, {
                                                        'product_id': promotion_product.discount_line_product_id.id,
                                                        'description_product': promotion_product.discount_line_product_id.name + '- ' + (
                                                            product_ids_list.name),
                                                        'product_qty': promotion_product.reward_product_quantity,
                                                        'price_unit': 0, }))
                                        elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':
                                            total = order_line.line_sub_total
                                            if total >= promotion_product.rule_minimum_amount:
                                                product.append((0, 0, {
                                                    'product_id': promotion_product.discount_line_product_id.id,
                                                    'description_product': promotion_product.discount_line_product_id.name + '(Main product' + ' : ' + (
                                                        product_ids_list.name) + ')',
                                                    'product_qty': promotion_product.reward_product_quantity,
                                                    'price_unit': 0, }))

                        product.append((0, 0, {
                            'product_id': promotion_product.discount_line_product_id.id,
                            'product_qty': promotion_product.reward_product_quantity,
                             'price_unit': 0, }))


            if promotion_product.reward_type == 'discount':
                if promotion_product.rule_partners_domain and promotion_product.product_ids:
                    if promotion_product.rule_date_from and promotion_product.rule_date_to:
                        for product_ids_list in promotion_product.product_ids:
                            # filter = promotion_product.filtered(lambda r: product_ids_list.id == rec.product_id.id)
                            free_product = product_ids_list.id
                            for customer_id in promotion_product.rule_partners_domain:
                                customer = customer_id.id
                                for order_line in self.order_line:
                                    if order_line.product_id.id == free_product and customer == self.partner_id.id and (order_line.product_qty >= promotion_product.rule_min_quantity or order_line.line_sub_total >= promotion_product.rule_minimum_amount):

                                        date_order = datetime.strptime(str(order_line.date_order),
                                                                       "%Y-%m-%d %H:%M:%S")
                                        start_date = datetime.strptime(str(promotion_product.rule_date_from),
                                                                       "%Y-%m-%d %H:%M:%S")
                                        end_date = datetime.strptime(str(promotion_product.rule_date_to),
                                                                     "%Y-%m-%d %H:%M:%S")
                                        if date_order <= end_date and date_order >= start_date:
                                            if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':
                                                taxes = order_line.taxes_id.name
                                                if taxes:
                                                    taxes = taxes.rstrip(taxes[-1])
                                                result = order_line.line_sub_total * int(taxes) / 100
                                                total = result + order_line.line_sub_total
                                                if total >= promotion_product.rule_minimum_amount:
                                                    if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                        promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1

                                                        if promotion_product.discount_type == 'percentage':
                                                            if promotion_product.discount_apply_on == 'specific_products':
                                                                # print("ATAS specific product")
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                result_ = -diskon_percentage
                                                                po_line = self.env['purchase.order.line'].sudo()
                                                                subtotal = order_line.line_sub_total * int(
                                                                    taxes) / 100
                                                                result_subt_total = order_line.line_sub_total + subtotal

                                                                for i in promotion_product.discount_specific_product_ids:
                                                                    if int(promotion_product.discount_max_amount) > 0:
                                                                        calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        if order_line.price_unit > promotion_product.discount_max_amount:


                                                                            vals = {
                                                                                'order_id' : self.id,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :'  + ' ' + i.name,
                                                                                'price_unit' : promotion_product.discount_max_amount,
                                                                                'line_sub_total' :result_subt_total,
                                                                        }
                                                                            if i.name not in self.order_line.mapped('description_product'):
                                                                                po_line.create(vals)

                                                                        elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                'price_unit': result_,
                                                                                'line_sub_total': result_subt_total,
                                                                            }
                                                                            if i.name not in self.order_line.mapped(
                                                                                    'description_product'):
                                                                                po_line.create(vals)
                                                                    elif int(promotion_product.discount_max_amount) == 0:
                                                                        # print("DISKON amount 0")

                                                                        vals = {
                                                                            'order_id': self.id,
                                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                                            'description_product': promotion_product.discount_line_product_id.product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            'price_unit': result_,
                                                                            'line_sub_total': result_subt_total,
                                                                        }
                                                                        if i.name not in self.order_line.mapped(
                                                                                'description_product'):
                                                                            po_line.create(vals)


                                                            elif promotion_product.discount_apply_on == 'cheapest_product':
                                                                min_price = min(self.order_line.mapped('price_unit'))
                                                                po_line = self.env['purchase.order.line'].sudo()
                                                                product_min_price = self.order_line.filtered(
                                                                    lambda r: r.price_unit == min_price)
                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                        subtotal = diskon_percentage * int(taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit


                                                                        for i in product_min_price:
                                                                            vals = {
                                                                                'order_id' : self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :'  + ' ' + i.name,
                                                                                'price_unit': promotion_product.discount_max_amount,

                                                                        }

                                                                        if i.product_id.name not in self.order_line.mapped('description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped('product_id').ids:

                                                                           po_line.create(vals)

                                                                    elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                        chepest_result = -diskon_percentage

                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit

                                                                        for i in product_min_price:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                'price_unit': chepest_result,

                                                                            }

                                                                        if i.product_id.name not in self.order_line.mapped(
                                                                                'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                                'product_id').ids:
                                                                            po_line.create(vals)

                                                                elif int(promotion_product.discount_max_amount) == 0:
                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    chepest_result = -diskon_percentage

                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        vals = {
                                                                            'order_id': self.id,
                                                                            'line_sub_total': resultsubtotal,
                                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                                            'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            'price_unit': chepest_result,

                                                                        }

                                                                    if i.product_id.name not in self.order_line.mapped(
                                                                            'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                        'product_id').ids:
                                                                        po_line.create(vals)

                                                            elif promotion_product.discount_apply_on == 'on_order':

                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if order_line.price_unit > promotion_product.discount_max_amount:
                                                                        po_line = self.env['purchase.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        on_order = -diskon_percentage



                                                                        subtotal = diskon_percentage * int(taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :'  + ' ' + i.product_id.name,
                                                                                'price_unit': promotion_product.discount_max_amount,

                                                                            }


                                                                            po_line.create(vals)
                                                                    elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                        po_line = self.env[
                                                                            'purchase.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        on_order = -diskon_percentage

                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                                'price_unit': on_order,

                                                                            }

                                                                            po_line.create(vals)
                                                                elif int(promotion_product.discount_max_amount) == 0:
                                                                    po_line = self.env[
                                                                        'purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage

                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        vals = {
                                                                            'order_id': self.id,
                                                                            'line_sub_total': resultsubtotal,
                                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                                            'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                            'price_unit': on_order,

                                                                        }

                                                                        po_line.create(vals)

                                                        elif promotion_product.discount_type == 'fixed_amount':

                                                            po_line = self.env['purchase.order.line'].sudo()


                                                            vals = {
                                                                'order_id': self.id,
                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + promotion_product.name,
                                                                'price_unit': promotion_product.discount_fixed_amount,

                                                            }
                                                            if promotion_product.name not in self.order_line.mapped(
                                                                    'description_product'):
                                                                po_line.create(vals)

                                                    else:
                                                        if promotion_product.discount_type == 'percentage':
                                                            if promotion_product.discount_apply_on == 'specific_products':
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                result_ = -diskon_percentage
                                                                po_line = self.env['purchase.order.line'].sudo()
                                                                subtotal = order_line.line_sub_total * int(
                                                                    taxes) / 100
                                                                result_subt_total = order_line.line_sub_total + subtotal

                                                                for i in promotion_product.discount_specific_product_ids:
                                                                    if int(promotion_product.discount_max_amount) > 0:
                                                                        calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        if order_line.price_unit > promotion_product.discount_max_amount:


                                                                            vals = {
                                                                                'order_id' : self.id,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :'  + ' ' + i.name,
                                                                                'price_unit' : promotion_product.discount_max_amount,
                                                                                'line_sub_total' :result_subt_total,
                                                                        }
                                                                            if i.name not in self.order_line.mapped('description_product'):
                                                                                po_line.create(vals)

                                                                        elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                'price_unit': result_,
                                                                                'line_sub_total': result_subt_total,
                                                                            }
                                                                            if i.name not in self.order_line.mapped(
                                                                                    'description_product'):
                                                                                po_line.create(vals)
                                                                    elif int(promotion_product.discount_max_amount) == 0:


                                                                        vals = {
                                                                            'order_id': self.id,
                                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                                            'description_product': promotion_product.discount_line_product_id.product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            'price_unit': result_,
                                                                            'line_sub_total': result_subt_total,
                                                                        }
                                                                        if i.name not in self.order_line.mapped(
                                                                                'description_product'):
                                                                            po_line.create(vals)

                                                            elif promotion_product.discount_apply_on == 'cheapest_product':
                                                                min_price = min(self.order_line.mapped('price_unit'))
                                                                po_line = self.env['purchase.order.line'].sudo()
                                                                product_min_price = self.order_line.filtered(
                                                                    lambda r: r.price_unit == min_price)
                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                        subtotal = diskon_percentage * int(taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit
                                                                        for i in product_min_price:
                                                                            vals = {
                                                                                'order_id' : self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :'  + ' ' + i.name,
                                                                                'price_unit': promotion_product.discount_max_amount,

                                                                        }

                                                                        if i.product_id.name not in self.order_line.mapped('description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped('product_id').ids:

                                                                           po_line.create(vals)

                                                                    elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                        chepest_result = -diskon_percentage

                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit

                                                                        for i in product_min_price:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                'price_unit': chepest_result,

                                                                            }

                                                                        if i.product_id.name not in self.order_line.mapped(
                                                                                'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                                'product_id').ids:
                                                                            po_line.create(vals)

                                                                elif int(promotion_product.discount_max_amount) == 0:
                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    chepest_result = -diskon_percentage

                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        vals = {
                                                                            'order_id': self.id,
                                                                            'line_sub_total': resultsubtotal,
                                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                                            'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            'price_unit': chepest_result,

                                                                        }

                                                                    if i.product_id.name not in self.order_line.mapped(
                                                                            'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                        'product_id').ids:
                                                                        po_line.create(vals)

                                                            elif promotion_product.discount_apply_on == 'on_order':

                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if order_line.price_unit > promotion_product.discount_max_amount:
                                                                        po_line = self.env['purchase.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        on_order = -diskon_percentage
                                                                        subtotal = diskon_percentage * int(taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :'  + ' ' + i.product_id.name,
                                                                                'price_unit': promotion_product.discount_max_amount,

                                                                            }


                                                                            po_line.create(vals)
                                                                    elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                        po_line = self.env[
                                                                            'purchase.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        on_order = -diskon_percentage

                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                                'price_unit': on_order,

                                                                            }

                                                                            po_line.create(vals)
                                                                elif int(promotion_product.discount_max_amount) == 0:
                                                                    po_line = self.env[
                                                                        'purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage

                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        vals = {
                                                                            'order_id': self.id,
                                                                            'line_sub_total': resultsubtotal,
                                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                                            'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                            'price_unit': on_order,

                                                                        }

                                                                        po_line.create(vals)

                                                        elif promotion_product.discount_type == 'fixed_amount':

                                                            po_line = self.env['purchase.order.line'].sudo()


                                                            vals = {
                                                                'order_id': self.id,
                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + promotion_product.name,
                                                                'price_unit': promotion_product.discount_fixed_amount,

                                                            }
                                                            if promotion_product.name not in self.order_line.mapped(
                                                                    'description_product'):
                                                                po_line.create(vals)

                                            elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':

                                                total = order_line.line_sub_total
                                                if total >= promotion_product.rule_minimum_amount:
                                                    if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_max_number > 0:
                                                        promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1

                                                        if promotion_product.discount_type == 'percentage':
                                                            if promotion_product.discount_apply_on == 'specific_products':
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                result_ = -diskon_percentage
                                                                po_line = self.env['purchase.order.line'].sudo()
                                                                subtotal = order_line.line_sub_total * int(
                                                                    taxes) / 100
                                                                result_subt_total = order_line.line_sub_total + subtotal

                                                                for i in promotion_product.discount_specific_product_ids:
                                                                    if int(promotion_product.discount_max_amount) > 0:
                                                                        calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        if order_line.price_unit > promotion_product.discount_max_amount:

                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                'price_unit': promotion_product.discount_max_amount,
                                                                                'line_sub_total': result_subt_total,
                                                                            }
                                                                            if i.name not in self.order_line.mapped(
                                                                                    'description_product'):
                                                                                po_line.create(vals)

                                                                        elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                'price_unit': result_,
                                                                                'line_sub_total': result_subt_total,
                                                                            }
                                                                            if i.name not in self.order_line.mapped(
                                                                                    'description_product'):
                                                                                po_line.create(vals)
                                                                    elif int(promotion_product.discount_max_amount) == 0:
                                                                        print("max amount kosong")

                                                                        vals = {
                                                                            'order_id': self.id,
                                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                                            'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            'price_unit': result_,
                                                                            'line_sub_total': result_subt_total,
                                                                        }
                                                                        if i.name not in self.order_line.mapped(
                                                                                'description_product'):
                                                                            po_line.create(vals)


                                                            elif promotion_product.discount_apply_on == 'cheapest_product':

                                                                min_price = min(
                                                                    self.order_line.mapped('price_unit'))
                                                                po_line = self.env['purchase.order.line'].sudo()
                                                                product_min_price = self.order_line.filtered(
                                                                    lambda r: r.price_unit == min_price)
                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit

                                                                        for i in product_min_price:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                'price_unit': promotion_product.discount_max_amount,

                                                                            }

                                                                        if i.product_id.name not in self.order_line.mapped(
                                                                                'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                                'product_id').ids:
                                                                            po_line.create(vals)

                                                                    elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                        chepest_result = -diskon_percentage

                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit

                                                                        for i in product_min_price:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                'price_unit': chepest_result,

                                                                            }

                                                                        if i.product_id.name not in self.order_line.mapped(
                                                                                'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                            'product_id').ids:
                                                                            po_line.create(vals)

                                                                elif int(
                                                                        promotion_product.discount_max_amount) == 0:
                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    chepest_result = -diskon_percentage

                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        vals = {
                                                                            'order_id': self.id,
                                                                            'line_sub_total': resultsubtotal,
                                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                                            'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            'price_unit': chepest_result,

                                                                        }

                                                                    if i.product_id.name not in self.order_line.mapped(
                                                                            'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                        'product_id').ids:
                                                                        po_line.create(vals)

                                                            elif promotion_product.discount_apply_on == 'on_order':

                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if order_line.price_unit > promotion_product.discount_max_amount:
                                                                        po_line = self.env[
                                                                            'purchase.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        on_order = -diskon_percentage

                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                                'price_unit': promotion_product.discount_max_amount,

                                                                            }

                                                                            po_line.create(vals)
                                                                    elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                        po_line = self.env[
                                                                            'purchase.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        on_order = -diskon_percentage

                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                                'price_unit': on_order,

                                                                            }

                                                                            po_line.create(vals)
                                                                elif int(
                                                                        promotion_product.discount_max_amount) == 0:
                                                                    po_line = self.env[
                                                                        'purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage

                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        vals = {
                                                                            'order_id': self.id,
                                                                            'line_sub_total': resultsubtotal,
                                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                                            'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                            'price_unit': on_order,

                                                                        }

                                                                        po_line.create(vals)

                                                        elif promotion_product.discount_type == 'fixed_amount':

                                                            po_line = self.env['purchase.order.line'].sudo()

                                                            vals = {
                                                                'order_id': self.id,
                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + promotion_product.name,
                                                                'price_unit': promotion_product.discount_fixed_amount,

                                                            }
                                                            if promotion_product.name not in self.order_line.mapped(
                                                                    'description_product'):
                                                                po_line.create(vals)

                                                    else:
                                                        if promotion_product.discount_type == 'percentage':
                                                            if promotion_product.discount_apply_on == 'specific_products':
                                                                taxes = order_line.taxes_id.name
                                                                if taxes:
                                                                    taxes = taxes.rstrip(taxes[-1])
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                result_ = -diskon_percentage
                                                                po_line = self.env['purchase.order.line'].sudo()
                                                                subtotal = order_line.line_sub_total * int(
                                                                    taxes) / 100
                                                                result_subt_total = order_line.line_sub_total + subtotal

                                                                for i in promotion_product.discount_specific_product_ids:
                                                                    if int(promotion_product.discount_max_amount) > 0:
                                                                        calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        if order_line.price_unit > promotion_product.discount_max_amount:


                                                                            vals = {
                                                                                'order_id' : self.id,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :'  + ' ' + i.name,
                                                                                'price_unit' : promotion_product.discount_max_amount,
                                                                                'line_sub_total' :result_subt_total,
                                                                        }
                                                                            if i.name not in self.order_line.mapped('description_product'):
                                                                                po_line.create(vals)

                                                                        elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                'price_unit': result_,
                                                                                'line_sub_total': result_subt_total,
                                                                            }
                                                                            if i.name not in self.order_line.mapped(
                                                                                    'description_product'):
                                                                                po_line.create(vals)
                                                                    elif int(promotion_product.discount_max_amount) == 0:


                                                                        vals = {
                                                                            'order_id': self.id,
                                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                                            'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            'price_unit': result_,
                                                                            'line_sub_total': result_subt_total,
                                                                        }
                                                                        if i.name not in self.order_line.mapped(
                                                                                'description_product'):
                                                                            po_line.create(vals)


                                                            elif promotion_product.discount_apply_on == 'cheapest_product':
                                                                min_price = min(self.order_line.mapped('price_unit'))
                                                                po_line = self.env['purchase.order.line'].sudo()
                                                                product_min_price = self.order_line.filtered(
                                                                    lambda r: r.price_unit == min_price)
                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if product_min_price.price_unit > promotion_product.discount_max_amount:
                                                                        taxes = order_line.taxes_id.name
                                                                        if taxes:
                                                                            taxes = taxes.rstrip(taxes[-1])

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                        subtotal = diskon_percentage * int(taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit


                                                                        for i in product_min_price:
                                                                            vals = {
                                                                                'order_id' : self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :'  + ' ' + i.name,
                                                                                'price_unit': promotion_product.discount_max_amount,

                                                                        }
                                                                        if i.product_id.name not in self.order_line.mapped('description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped('product_id').ids:

                                                                           po_line.create(vals)

                                                                    elif product_min_price.price_unit < promotion_product.discount_max_amount:
                                                                        taxes = order_line.taxes_id.name
                                                                        if taxes:
                                                                            taxes = taxes.rstrip(taxes[-1])

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                        chepest_result = -diskon_percentage

                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit

                                                                        for i in product_min_price:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                'price_unit': chepest_result,

                                                                            }

                                                                        if i.product_id.name not in self.order_line.mapped(
                                                                                'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                                'product_id').ids:
                                                                            po_line.create(vals)

                                                                elif int(promotion_product.discount_max_amount) == 0:
                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    chepest_result = -diskon_percentage
                                                                    taxes = order_line.taxes_id.name
                                                                    if taxes:
                                                                        taxes = taxes.rstrip(taxes[-1])
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        vals = {
                                                                            'order_id': self.id,
                                                                            'line_sub_total': resultsubtotal,
                                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                                            'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            'price_unit': chepest_result,

                                                                        }

                                                                    if i.product_id.name not in self.order_line.mapped(
                                                                            'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                        'product_id').ids:
                                                                        po_line.create(vals)

                                                            elif promotion_product.discount_apply_on == 'on_order':

                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if order_line.price_unit > promotion_product.discount_max_amount:
                                                                        po_line = self.env['purchase.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        on_order = -diskon_percentage



                                                                        subtotal = diskon_percentage * int(taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :'  + ' ' + i.product_id.name,
                                                                                'price_unit': promotion_product.discount_max_amount,

                                                                            }


                                                                            po_line.create(vals)
                                                                    elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                        po_line = self.env[
                                                                            'purchase.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        on_order = -diskon_percentage

                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                                'price_unit': on_order,

                                                                            }

                                                                            po_line.create(vals)
                                                                elif int(promotion_product.discount_max_amount) == 0:
                                                                    po_line = self.env[
                                                                        'purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage

                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        vals = {
                                                                            'order_id': self.id,
                                                                            'line_sub_total': resultsubtotal,
                                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                                            'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                            'price_unit': on_order,

                                                                        }

                                                                        po_line.create(vals)

                                                        elif promotion_product.discount_type == 'fixed_amount':

                                                            po_line = self.env['purchase.order.line'].sudo()


                                                            vals = {
                                                                'order_id': self.id,
                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + promotion_product.name,
                                                                'price_unit': promotion_product.discount_fixed_amount,

                                                            }
                                                            if promotion_product.name not in self.order_line.mapped(
                                                                    'description_product'):
                                                                po_line.create(vals)

                    else:
                        for product_ids_list in promotion_product.product_ids:
                            # filter = promotion_product.filtered(lambda r: product_ids_list.id == rec.product_id.id)
                            free_product = product_ids_list.id
                            for customer_id in promotion_product.rule_partners_domain:
                                customer = customer_id.id
                                for order_line in self.order_line:
                                    if order_line.product_id.id == free_product and customer == self.partner_id.id and (
                                            order_line.product_qty >= promotion_product.rule_min_quantity or order_line.line_sub_total >= promotion_product.rule_minimum_amount):



                                        if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':
                                            taxes = order_line.taxes_id.name
                                            if taxes:
                                                taxes = taxes.rstrip(taxes[-1])
                                            result = order_line.line_sub_total * int(taxes) / 100
                                            total = result + order_line.line_sub_total
                                            if total >= promotion_product.rule_minimum_amount:
                                                if promotion_product.remaining_use_promotion > 0:
                                                    promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1
                                                    if promotion_product.remaining_use_promotion > 0:
                                                        if promotion_product.discount_type == 'percentage':
                                                            if promotion_product.discount_apply_on == 'specific_products':
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                result_ = -diskon_percentage
                                                                po_line = self.env['purchase.order.line'].sudo()
                                                                subtotal = order_line.line_sub_total * int(
                                                                    taxes) / 100
                                                                result_subt_total = order_line.line_sub_total + subtotal

                                                                for i in promotion_product.discount_specific_product_ids:
                                                                    if int(promotion_product.discount_max_amount) > 0:
                                                                        calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        if order_line.price_unit > promotion_product.discount_max_amount:

                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                'price_unit': promotion_product.discount_max_amount,
                                                                                'line_sub_total': result_subt_total,
                                                                            }
                                                                            if i.name not in self.order_line.mapped(
                                                                                    'description_product'):
                                                                                po_line.create(vals)

                                                                        elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                'price_unit': result_,
                                                                                'line_sub_total': result_subt_total,
                                                                            }
                                                                            if i.name not in self.order_line.mapped(
                                                                                    'description_product'):
                                                                                po_line.create(vals)
                                                                    elif int(
                                                                            promotion_product.discount_max_amount) == 0:

                                                                        vals = {
                                                                            'order_id': self.id,
                                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                                            'description_product': promotion_product.discount_line_product_id.product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            'price_unit': result_,
                                                                            'line_sub_total': result_subt_total,
                                                                        }
                                                                        if i.name not in self.order_line.mapped(
                                                                                'description_product'):
                                                                            po_line.create(vals)


                                                            elif promotion_product.discount_apply_on == 'cheapest_product':
                                                                min_price = min(
                                                                    self.order_line.mapped('price_unit'))
                                                                po_line = self.env['purchase.order.line'].sudo()
                                                                product_min_price = self.order_line.filtered(
                                                                    lambda r: r.price_unit == min_price)
                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit

                                                                        for i in product_min_price:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                'price_unit': promotion_product.discount_max_amount,

                                                                            }

                                                                        if i.product_id.name not in self.order_line.mapped(
                                                                                'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                                'product_id').ids:
                                                                            po_line.create(vals)

                                                                    elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                        chepest_result = -diskon_percentage

                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit

                                                                        for i in product_min_price:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                'price_unit': chepest_result,

                                                                            }

                                                                        if i.product_id.name not in self.order_line.mapped(
                                                                                'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                            'product_id').ids:
                                                                            po_line.create(vals)

                                                                elif int(
                                                                        promotion_product.discount_max_amount) == 0:
                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    chepest_result = -diskon_percentage

                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        vals = {
                                                                            'order_id': self.id,
                                                                            'line_sub_total': resultsubtotal,
                                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                                            'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            'price_unit': chepest_result,

                                                                        }

                                                                    if i.product_id.name not in self.order_line.mapped(
                                                                            'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                        'product_id').ids:
                                                                        po_line.create(vals)

                                                            elif promotion_product.discount_apply_on == 'on_order':

                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if order_line.price_unit > promotion_product.discount_max_amount:
                                                                        po_line = self.env[
                                                                            'purchase.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        on_order = -diskon_percentage

                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                                'price_unit': promotion_product.discount_max_amount,

                                                                            }

                                                                            po_line.create(vals)
                                                                    elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                        po_line = self.env[
                                                                            'purchase.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        on_order = -diskon_percentage

                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                                'price_unit': on_order,

                                                                            }

                                                                            po_line.create(vals)
                                                                elif int(
                                                                        promotion_product.discount_max_amount) == 0:
                                                                    po_line = self.env[
                                                                        'purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage

                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        vals = {
                                                                            'order_id': self.id,
                                                                            'line_sub_total': resultsubtotal,
                                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                                            'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                            'price_unit': on_order,

                                                                        }

                                                                        po_line.create(vals)

                                                        elif promotion_product.discount_type == 'fixed_amount':

                                                            po_line = self.env['purchase.order.line'].sudo()

                                                            vals = {
                                                                'order_id': self.id,
                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + promotion_product.name,
                                                                'price_unit': promotion_product.discount_fixed_amount,

                                                            }
                                                            if promotion_product.name not in self.order_line.mapped(
                                                                    'description_product'):
                                                                po_line.create(vals)

                                        elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':
                                            total = order_line.line_sub_total
                                            if total >= promotion_product.rule_minimum_amount:
                                                if promotion_product.remaining_use_promotion > 0:
                                                    promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1
                                                    if promotion_product.remaining_use_promotion > 0:
                                                        if promotion_product.discount_type == 'percentage':
                                                            if promotion_product.discount_apply_on == 'specific_products':
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                result_ = -diskon_percentage
                                                                po_line = self.env['purchase.order.line'].sudo()
                                                                subtotal = order_line.line_sub_total * int(
                                                                    taxes) / 100
                                                                result_subt_total = order_line.line_sub_total + subtotal

                                                                for i in promotion_product.discount_specific_product_ids:
                                                                    if int(promotion_product.discount_max_amount) > 0:
                                                                        calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        if order_line.price_unit > promotion_product.discount_max_amount:

                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                'price_unit': promotion_product.discount_max_amount,
                                                                                'line_sub_total': result_subt_total,
                                                                            }
                                                                            if i.name not in self.order_line.mapped(
                                                                                    'description_product'):
                                                                                po_line.create(vals)

                                                                        elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                'price_unit': result_,
                                                                                'line_sub_total': result_subt_total,
                                                                            }
                                                                            if i.name not in self.order_line.mapped(
                                                                                    'description_product'):
                                                                                po_line.create(vals)
                                                                    elif int(
                                                                            promotion_product.discount_max_amount) == 0:

                                                                        vals = {
                                                                            'order_id': self.id,
                                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                                            'description_product': promotion_product.discount_line_product_id.product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            'price_unit': result_,
                                                                            'line_sub_total': result_subt_total,
                                                                        }
                                                                        if i.name not in self.order_line.mapped(
                                                                                'description_product'):
                                                                            po_line.create(vals)


                                                            elif promotion_product.discount_apply_on == 'cheapest_product':
                                                                min_price = min(
                                                                    self.order_line.mapped('price_unit'))
                                                                po_line = self.env['purchase.order.line'].sudo()
                                                                product_min_price = self.order_line.filtered(
                                                                    lambda r: r.price_unit == min_price)
                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit

                                                                        for i in product_min_price:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                'price_unit': promotion_product.discount_max_amount,

                                                                            }

                                                                        if i.product_id.name not in self.order_line.mapped(
                                                                                'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                            'product_id').ids:
                                                                            po_line.create(vals)

                                                                    elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                        chepest_result = -diskon_percentage

                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit

                                                                        for i in product_min_price:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                'price_unit': chepest_result,

                                                                            }

                                                                        if i.product_id.name not in self.order_line.mapped(
                                                                                'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                            'product_id').ids:
                                                                            po_line.create(vals)

                                                                elif int(
                                                                        promotion_product.discount_max_amount) == 0:
                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    chepest_result = -diskon_percentage

                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        vals = {
                                                                            'order_id': self.id,
                                                                            'line_sub_total': resultsubtotal,
                                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                                            'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            'price_unit': chepest_result,

                                                                        }

                                                                    if i.product_id.name not in self.order_line.mapped(
                                                                            'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                        'product_id').ids:
                                                                        po_line.create(vals)

                                                            elif promotion_product.discount_apply_on == 'on_order':

                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if order_line.price_unit > promotion_product.discount_max_amount:
                                                                        po_line = self.env[
                                                                            'purchase.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        on_order = -diskon_percentage

                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                                'price_unit': promotion_product.discount_max_amount,

                                                                            }

                                                                            po_line.create(vals)
                                                                    elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                        po_line = self.env[
                                                                            'purchase.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        on_order = -diskon_percentage

                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                                'price_unit': on_order,

                                                                            }

                                                                            po_line.create(vals)
                                                                elif int(
                                                                        promotion_product.discount_max_amount) == 0:
                                                                    po_line = self.env[
                                                                        'purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage

                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        vals = {
                                                                            'order_id': self.id,
                                                                            'line_sub_total': resultsubtotal,
                                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                                            'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                            'price_unit': on_order,

                                                                        }

                                                                        po_line.create(vals)

                                                        elif promotion_product.discount_type == 'fixed_amount':

                                                            po_line = self.env['purchase.order.line'].sudo()

                                                            vals = {
                                                                'order_id': self.id,
                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + promotion_product.name,
                                                                'price_unit': promotion_product.discount_fixed_amount,

                                                            }
                                                            if promotion_product.name not in self.order_line.mapped(
                                                                    'description_product'):
                                                                po_line.create(vals)


                elif not promotion_product.rule_partners_domain and not promotion_product.product_ids:
                    # print("Tidak keduanya")
                    if promotion_product.rule_date_from and promotion_product.rule_date_to:
                        # print("kedua nya isi tanggal")


                        for order_line in self.order_line:
                            if order_line.product_qty >= promotion_product.rule_min_quantity or order_line.line_sub_total >= promotion_product.rule_minimum_amount:
                                # print("MASUK")
                                date_order = datetime.strptime(str(order_line.date_order),
                                                               "%Y-%m-%d %H:%M:%S")
                                start_date = datetime.strptime(str(promotion_product.rule_date_from),
                                                               "%Y-%m-%d %H:%M:%S")
                                end_date = datetime.strptime(str(promotion_product.rule_date_to),
                                                             "%Y-%m-%d %H:%M:%S")
                                if date_order <= end_date and date_order >= start_date:
                                    if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':
                                        taxes = order_line.taxes_id.name
                                        if taxes:
                                            taxes = taxes.rstrip(taxes[-1])
                                        result = order_line.line_sub_total * int(taxes) / 100
                                        total = result + order_line.line_sub_total
                                        if total >= promotion_product.rule_minimum_amount:
                                            if promotion_product.remaining_use_promotion > 0:
                                                promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1
                                                if promotion_product.remaining_use_promotion > 0:
                                                    if promotion_product.discount_type == 'percentage':
                                                        if promotion_product.discount_apply_on == 'specific_products':
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            result_ = -diskon_percentage
                                                            po_line = self.env['purchase.order.line'].sudo()
                                                            subtotal = order_line.line_sub_total * int(
                                                                taxes) / 100
                                                            result_subt_total = order_line.line_sub_total + subtotal

                                                            for i in promotion_product.discount_specific_product_ids:
                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if order_line.price_unit > promotion_product.discount_max_amount:


                                                                        vals = {
                                                                            'order_id' : self.id,
                                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                                            'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :'  + ' ' + i.name,
                                                                            'price_unit' : promotion_product.discount_max_amount,
                                                                            'line_sub_total' :result_subt_total,
                                                                    }
                                                                        if i.name not in self.order_line.mapped('description_product'):
                                                                            po_line.create(vals)

                                                                    elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                        vals = {
                                                                            'order_id': self.id,
                                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                                            'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            'price_unit': result_,
                                                                            'line_sub_total': result_subt_total,
                                                                        }
                                                                        if i.name not in self.order_line.mapped(
                                                                                'description_product'):
                                                                            po_line.create(vals)
                                                                elif int(promotion_product.discount_max_amount) == 0:


                                                                    vals = {
                                                                        'order_id': self.id,
                                                                        'product_id': promotion_product.discount_line_product_id.id,
                                                                        'description_product': promotion_product.discount_line_product_id.product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                        'price_unit': result_,
                                                                        'line_sub_total': result_subt_total,
                                                                    }
                                                                    if i.name not in self.order_line.mapped(
                                                                            'description_product'):
                                                                        po_line.create(vals)


                                                        elif promotion_product.discount_apply_on == 'cheapest_product':
                                                            min_price = min(self.order_line.mapped('price_unit'))
                                                            po_line = self.env['purchase.order.line'].sudo()
                                                            product_min_price = self.order_line.filtered(
                                                                lambda r: r.price_unit == min_price)
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                    subtotal = diskon_percentage * int(taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit


                                                                    for i in product_min_price:
                                                                        vals = {
                                                                            'order_id' : self.id,
                                                                            'line_sub_total': resultsubtotal,
                                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                                            'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :'  + ' ' + i.name,
                                                                            'price_unit': promotion_product.discount_max_amount,

                                                                    }

                                                                    if i.product_id.name not in self.order_line.mapped('description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped('product_id').ids:

                                                                       po_line.create(vals)

                                                                elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    chepest_result = -diskon_percentage

                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        vals = {
                                                                            'order_id': self.id,
                                                                            'line_sub_total': resultsubtotal,
                                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                                            'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            'price_unit': chepest_result,

                                                                        }

                                                                    if i.product_id.name not in self.order_line.mapped(
                                                                            'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                            'product_id').ids:
                                                                        po_line.create(vals)

                                                            elif int(promotion_product.discount_max_amount) == 0:
                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                chepest_result = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    vals = {
                                                                        'order_id': self.id,
                                                                        'line_sub_total': resultsubtotal,
                                                                        'product_id': promotion_product.discount_line_product_id.id,
                                                                        'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                        'price_unit': chepest_result,

                                                                    }

                                                                if i.product_id.name not in self.order_line.mapped(
                                                                        'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    'product_id').ids:
                                                                    po_line.create(vals)

                                                        elif promotion_product.discount_apply_on == 'on_order':

                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if order_line.price_unit > promotion_product.discount_max_amount:
                                                                    po_line = self.env['purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage



                                                                    subtotal = diskon_percentage * int(taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        vals = {
                                                                            'order_id': self.id,
                                                                            'line_sub_total': resultsubtotal,
                                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                                            'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :'  + ' ' + i.product_id.name,
                                                                            'price_unit': promotion_product.discount_max_amount,

                                                                        }


                                                                        po_line.create(vals)
                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage

                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        vals = {
                                                                            'order_id': self.id,
                                                                            'line_sub_total': resultsubtotal,
                                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                                            'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                            'price_unit': on_order,

                                                                        }

                                                                        po_line.create(vals)
                                                            elif int(promotion_product.discount_max_amount) == 0:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + order_line.price_unit

                                                                for i in order_line:
                                                                    vals = {
                                                                        'order_id': self.id,
                                                                        'line_sub_total': resultsubtotal,
                                                                        'product_id': promotion_product.discount_line_product_id.id,
                                                                        'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        'price_unit': on_order,

                                                                    }

                                                                    po_line.create(vals)

                                                    elif promotion_product.discount_type == 'fixed_amount':

                                                        po_line = self.env['purchase.order.line'].sudo()


                                                        vals = {
                                                            'order_id': self.id,
                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                            'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + promotion_product.name,
                                                            'price_unit': promotion_product.discount_fixed_amount,

                                                        }
                                                        if promotion_product.name not in self.order_line.mapped(
                                                                'description_product'):
                                                            po_line.create(vals)

                                    elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':
                                        # print("TAX excluded")
                                        total = order_line.line_sub_total
                                        if total >= promotion_product.rule_minimum_amount:
                                            if promotion_product.remaining_use_promotion > 0:
                                                promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1

                                                if promotion_product.discount_type == 'percentage':
                                                    if promotion_product.discount_apply_on == 'specific_products':
                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                        result_ = -diskon_percentage
                                                        po_line = self.env['purchase.order.line'].sudo()
                                                        subtotal = order_line.line_sub_total * int(
                                                            taxes) / 100
                                                        result_subt_total = order_line.line_sub_total + subtotal

                                                        for i in promotion_product.discount_specific_product_ids:
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if order_line.price_unit > promotion_product.discount_max_amount:

                                                                    vals = {
                                                                        'order_id': self.id,
                                                                        'product_id': promotion_product.discount_line_product_id.id,
                                                                        'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                        'price_unit': promotion_product.discount_max_amount,
                                                                        'line_sub_total': result_subt_total,
                                                                    }
                                                                    if i.name not in self.order_line.mapped(
                                                                            'description_product'):
                                                                        po_line.create(vals)

                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                    vals = {
                                                                        'order_id': self.id,
                                                                        'product_id': promotion_product.discount_line_product_id.id,
                                                                        'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                        'price_unit': result_,
                                                                        'line_sub_total': result_subt_total,
                                                                    }
                                                                    if i.name not in self.order_line.mapped(
                                                                            'description_product'):
                                                                        po_line.create(vals)
                                                            elif int(
                                                                    promotion_product.discount_max_amount) == 0:

                                                                vals = {
                                                                    'order_id': self.id,
                                                                    'product_id': promotion_product.discount_line_product_id.id,
                                                                    'description_product': promotion_product.discount_line_product_id.product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                    'price_unit': result_,
                                                                    'line_sub_total': result_subt_total,
                                                                }
                                                                if i.name not in self.order_line.mapped(
                                                                        'description_product'):
                                                                    po_line.create(vals)


                                                    elif promotion_product.discount_apply_on == 'cheapest_product':
                                                        # print("CHEPEST PRODUCT")
                                                        min_price = min(
                                                            self.order_line.mapped('price_unit'))
                                                        po_line = self.env['purchase.order.line'].sudo()
                                                        product_min_price = self.order_line.filtered(
                                                            lambda r: r.price_unit == min_price)
                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    vals = {
                                                                        'order_id': self.id,
                                                                        'line_sub_total': resultsubtotal,
                                                                        'product_id': promotion_product.discount_line_product_id.id,
                                                                        'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                        'price_unit': promotion_product.discount_max_amount,

                                                                    }

                                                                if i.product_id.name not in self.order_line.mapped(
                                                                        'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                        'product_id').ids:
                                                                    po_line.create(vals)

                                                            elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                chepest_result = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    vals = {
                                                                        'order_id': self.id,
                                                                        'line_sub_total': resultsubtotal,
                                                                        'product_id': promotion_product.discount_line_product_id.id,
                                                                        'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                        'price_unit': chepest_result,

                                                                    }

                                                                if i.product_id.name not in self.order_line.mapped(
                                                                        'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    'product_id').ids:
                                                                    po_line.create(vals)

                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                            chepest_result = -diskon_percentage

                                                            subtotal = diskon_percentage * int(
                                                                taxes) / 100
                                                            resultsubtotal = subtotal + product_min_price.price_unit

                                                            for i in product_min_price:
                                                                vals = {
                                                                    'order_id': self.id,
                                                                    'line_sub_total': resultsubtotal,
                                                                    'product_id': promotion_product.discount_line_product_id.id,
                                                                    'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                    'price_unit': chepest_result,

                                                                }

                                                            if i.product_id.name not in self.order_line.mapped(
                                                                    'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                'product_id').ids:
                                                                po_line.create(vals)

                                                    elif promotion_product.discount_apply_on == 'on_order':

                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if order_line.price_unit > promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + order_line.price_unit

                                                                for i in order_line:
                                                                    vals = {
                                                                        'order_id': self.id,
                                                                        'line_sub_total': resultsubtotal,
                                                                        'product_id': promotion_product.discount_line_product_id.id,
                                                                        'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        'price_unit': promotion_product.discount_max_amount,

                                                                    }

                                                                    po_line.create(vals)
                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + order_line.price_unit

                                                                for i in order_line:
                                                                    vals = {
                                                                        'order_id': self.id,
                                                                        'line_sub_total': resultsubtotal,
                                                                        'product_id': promotion_product.discount_line_product_id.id,
                                                                        'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        'price_unit': on_order,

                                                                    }

                                                                    po_line.create(vals)
                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            po_line = self.env[
                                                                'purchase.order.line'].sudo()
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            on_order = -diskon_percentage

                                                            subtotal = diskon_percentage * int(
                                                                taxes) / 100
                                                            resultsubtotal = subtotal + order_line.price_unit

                                                            for i in order_line:
                                                                vals = {
                                                                    'order_id': self.id,
                                                                    'line_sub_total': resultsubtotal,
                                                                    'product_id': promotion_product.discount_line_product_id.id,
                                                                    'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                    'price_unit': on_order,

                                                                }

                                                                po_line.create(vals)

                                                elif promotion_product.discount_type == 'fixed_amount':

                                                    po_line = self.env['purchase.order.line'].sudo()

                                                    vals = {
                                                        'order_id': self.id,
                                                        'product_id': promotion_product.discount_line_product_id.id,
                                                        'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + promotion_product.name,
                                                        'price_unit': promotion_product.discount_fixed_amount,

                                                    }
                                                    if promotion_product.name not in self.order_line.mapped(
                                                            'description_product'):
                                                        po_line.create(vals)

                                            else:
                                                if promotion_product.discount_type == 'percentage':
                                                    if promotion_product.discount_apply_on == 'specific_products':
                                                        taxes = order_line.taxes_id.name
                                                        if taxes:
                                                            taxes = taxes.rstrip(taxes[-1])
                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                        result_ = -diskon_percentage
                                                        po_line = self.env['purchase.order.line'].sudo()
                                                        subtotal = order_line.line_sub_total * int(
                                                            taxes) / 100
                                                        result_subt_total = order_line.line_sub_total + subtotal

                                                        for i in promotion_product.discount_specific_product_ids:
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if order_line.price_unit > promotion_product.discount_max_amount:

                                                                    vals = {
                                                                        'order_id': self.id,
                                                                        'product_id': promotion_product.discount_line_product_id.id,
                                                                        'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                        'price_unit': promotion_product.discount_max_amount,
                                                                        'line_sub_total': result_subt_total,
                                                                    }
                                                                    if i.name not in self.order_line.mapped(
                                                                            'description_product'):
                                                                        po_line.create(vals)

                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                    vals = {
                                                                        'order_id': self.id,
                                                                        'product_id': promotion_product.discount_line_product_id.id,
                                                                        'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                        'price_unit': result_,
                                                                        'line_sub_total': result_subt_total,
                                                                    }
                                                                    if i.name not in self.order_line.mapped(
                                                                            'description_product'):
                                                                        po_line.create(vals)
                                                            elif int(
                                                                    promotion_product.discount_max_amount) == 0:

                                                                vals = {
                                                                    'order_id': self.id,
                                                                    'product_id': promotion_product.discount_line_product_id.id,
                                                                    'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + order_line.product_id.name,
                                                                    'price_unit': result_,
                                                                    'line_sub_total': result_subt_total,
                                                                }
                                                                if i.name not in self.order_line.mapped(
                                                                        'description_product'):
                                                                    po_line.create(vals)


                                                    elif promotion_product.discount_apply_on == 'cheapest_product':
                                                        # print("CHEPEST PRODUCT")
                                                        min_price = min(
                                                            self.order_line.mapped('price_unit'))
                                                        po_line = self.env['purchase.order.line'].sudo()
                                                        product_min_price = self.order_line.filtered(
                                                            lambda r: r.price_unit == min_price)
                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    vals = {
                                                                        'order_id': self.id,
                                                                        'line_sub_total': resultsubtotal,
                                                                        'product_id': promotion_product.discount_line_product_id.id,
                                                                        'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                        'price_unit': promotion_product.discount_max_amount,

                                                                    }

                                                                if i.product_id.name not in self.order_line.mapped(
                                                                        'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    'product_id').ids:
                                                                    po_line.create(vals)

                                                            elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                chepest_result = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    vals = {
                                                                        'order_id': self.id,
                                                                        'line_sub_total': resultsubtotal,
                                                                        'product_id': promotion_product.discount_line_product_id.id,
                                                                        'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                        'price_unit': chepest_result,

                                                                    }

                                                                if i.product_id.name not in self.order_line.mapped(
                                                                        'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    'product_id').ids:
                                                                    po_line.create(vals)

                                                        elif int(promotion_product.discount_max_amount) == 0:
                                                            diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                            chepest_result = -diskon_percentage

                                                            # subtotal = diskon_percentage * int(taxes) / 100
                                                            # resultsubtotal = subtotal + product_min_price.price_unit

                                                            for i in product_min_price:
                                                                vals = {
                                                                    'order_id': self.id,
                                                                    # 'line_sub_total': resultsubtotal,
                                                                    'product_id': promotion_product.discount_line_product_id.id,
                                                                    'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                    'price_unit': chepest_result,

                                                                }

                                                            if i.product_id.name not in self.order_line.mapped(
                                                                    'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                'product_id').ids:
                                                                po_line.create(vals)

                                                    elif promotion_product.discount_apply_on == 'on_order':
                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if order_line.price_unit > promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + order_line.price_unit

                                                                for i in order_line:
                                                                    vals = {
                                                                        'order_id': self.id,
                                                                        'line_sub_total': resultsubtotal,
                                                                        'product_id': promotion_product.discount_line_product_id.id,
                                                                        'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        'price_unit': promotion_product.discount_max_amount,

                                                                    }

                                                                    po_line.create(vals)
                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + order_line.price_unit

                                                                for i in order_line:
                                                                    vals = {
                                                                        'order_id': self.id,
                                                                        'line_sub_total': resultsubtotal,
                                                                        'product_id': promotion_product.discount_line_product_id.id,
                                                                        'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        'price_unit': on_order,

                                                                    }

                                                                    po_line.create(vals)
                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            po_line = self.env[
                                                                'purchase.order.line'].sudo()
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            on_order = -diskon_percentage

                                                            subtotal = diskon_percentage * int(
                                                                taxes) / 100
                                                            resultsubtotal = subtotal + order_line.price_unit

                                                            for i in order_line:
                                                                vals = {
                                                                    'order_id': self.id,
                                                                    'line_sub_total': resultsubtotal,
                                                                    'product_id': promotion_product.discount_line_product_id.id,
                                                                    'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                    'price_unit': on_order,

                                                                }

                                                                po_line.create(vals)

                                                elif promotion_product.discount_type == 'fixed_amount':

                                                    po_line = self.env['purchase.order.line'].sudo()

                                                    vals = {
                                                        'order_id': self.id,
                                                        'product_id': promotion_product.discount_line_product_id.id,
                                                        'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + promotion_product.name,
                                                        'price_unit': promotion_product.discount_fixed_amount,

                                                    }
                                                    if promotion_product.name not in self.order_line.mapped(
                                                            'description_product'):
                                                        po_line.create(vals)


                    else:
                        for product_ids_list in promotion_product.product_ids:
                            # filter = promotion_product.filtered(lambda r: product_ids_list.id == rec.product_id.id)
                            free_product = product_ids_list.id
                            for customer_id in promotion_product.rule_partners_domain:
                                customer = customer_id.id
                                for order_line in self.order_line:
                                    if order_line.product_id.id == free_product and customer == self.partner_id.id and (order_line.product_qty >= promotion_product.rule_min_quantity or order_line.line_sub_total >= promotion_product.rule_minimum_amount):
                                        if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':
                                            taxes = order_line.taxes_id.name
                                            if taxes:
                                                taxes = taxes.rstrip(taxes[-1])
                                            result = order_line.line_sub_total * int(taxes) / 100
                                            total = result + order_line.line_sub_total
                                            if total >= promotion_product.rule_minimum_amount:
                                                if promotion_product.remaining_use_promotion > 0:
                                                    promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1
                                                    if promotion_product.remaining_use_promotion > 0:
                                                        if promotion_product.discount_type == 'percentage':
                                                            if promotion_product.discount_apply_on == 'specific_products':
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                result_ = -diskon_percentage
                                                                po_line = self.env['purchase.order.line'].sudo()
                                                                subtotal = order_line.line_sub_total * int(
                                                                    taxes) / 100
                                                                result_subt_total = order_line.line_sub_total + subtotal

                                                                for i in promotion_product.discount_specific_product_ids:
                                                                    if int(promotion_product.discount_max_amount) > 0:
                                                                        calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        if order_line.price_unit > promotion_product.discount_max_amount:


                                                                            vals = {
                                                                                'order_id' : self.id,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :'  + ' ' + i.name,
                                                                                'price_unit' : promotion_product.discount_max_amount,
                                                                                'line_sub_total' :result_subt_total,
                                                                        }
                                                                            if i.name not in self.order_line.mapped('description_product'):
                                                                                po_line.create(vals)

                                                                        elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                'price_unit': result_,
                                                                                'line_sub_total': result_subt_total,
                                                                            }
                                                                            if i.name not in self.order_line.mapped(
                                                                                    'description_product'):
                                                                                po_line.create(vals)
                                                                    elif int(promotion_product.discount_max_amount) == 0:


                                                                        vals = {
                                                                            'order_id': self.id,
                                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                                            'description_product': promotion_product.discount_line_product_id.product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            'price_unit': result_,
                                                                            'line_sub_total': result_subt_total,
                                                                        }
                                                                        if i.name not in self.order_line.mapped(
                                                                                'description_product'):
                                                                            po_line.create(vals)


                                                            elif promotion_product.discount_apply_on == 'cheapest_product':
                                                                min_price = min(self.order_line.mapped('price_unit'))
                                                                po_line = self.env['purchase.order.line'].sudo()
                                                                product_min_price = self.order_line.filtered(
                                                                    lambda r: r.price_unit == min_price)
                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                        subtotal = diskon_percentage * int(taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit


                                                                        for i in product_min_price:
                                                                            vals = {
                                                                                'order_id' : self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :'  + ' ' + i.name,
                                                                                'price_unit': promotion_product.discount_max_amount,

                                                                        }

                                                                        if i.product_id.name not in self.order_line.mapped('description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped('product_id').ids:

                                                                           po_line.create(vals)

                                                                    elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                        chepest_result = -diskon_percentage

                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit

                                                                        for i in product_min_price:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                'price_unit': chepest_result,

                                                                            }

                                                                        if i.product_id.name not in self.order_line.mapped(
                                                                                'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                                'product_id').ids:
                                                                            po_line.create(vals)

                                                                elif int(promotion_product.discount_max_amount) == 0:
                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    chepest_result = -diskon_percentage

                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        vals = {
                                                                            'order_id': self.id,
                                                                            'line_sub_total': resultsubtotal,
                                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                                            'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            'price_unit': chepest_result,

                                                                        }

                                                                    if i.product_id.name not in self.order_line.mapped(
                                                                            'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                        'product_id').ids:
                                                                        po_line.create(vals)

                                                            elif promotion_product.discount_apply_on == 'on_order':

                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if order_line.price_unit > promotion_product.discount_max_amount:
                                                                        po_line = self.env['purchase.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        on_order = -diskon_percentage



                                                                        subtotal = diskon_percentage * int(taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :'  + ' ' + i.product_id.name,
                                                                                'price_unit': promotion_product.discount_max_amount,

                                                                            }


                                                                            po_line.create(vals)
                                                                    elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                        po_line = self.env[
                                                                            'purchase.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        on_order = -diskon_percentage

                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                                'price_unit': on_order,

                                                                            }

                                                                            po_line.create(vals)
                                                                elif int(promotion_product.discount_max_amount) == 0:
                                                                    po_line = self.env[
                                                                        'purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage

                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        vals = {
                                                                            'order_id': self.id,
                                                                            'line_sub_total': resultsubtotal,
                                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                                            'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                            'price_unit': on_order,

                                                                        }

                                                                        po_line.create(vals)

                                                        elif promotion_product.discount_type == 'fixed_amount':

                                                            po_line = self.env['purchase.order.line'].sudo()


                                                            vals = {
                                                                'order_id': self.id,
                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + promotion_product.name,
                                                                'price_unit': promotion_product.discount_fixed_amount,

                                                            }
                                                            if promotion_product.name not in self.order_line.mapped(
                                                                    'description_product'):
                                                                po_line.create(vals)

                                        elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':
                                            total = order_line.line_sub_total
                                            if total >= promotion_product.rule_minimum_amount:
                                                if promotion_product.remaining_use_promotion > 0:
                                                    promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1
                                                    if promotion_product.remaining_use_promotion > 0:
                                                        if promotion_product.discount_type == 'percentage':
                                                            if promotion_product.discount_apply_on == 'specific_products':
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                result_ = -diskon_percentage
                                                                po_line = self.env['purchase.order.line'].sudo()
                                                                subtotal = order_line.line_sub_total * int(
                                                                    taxes) / 100
                                                                result_subt_total = order_line.line_sub_total + subtotal

                                                                for i in promotion_product.discount_specific_product_ids:
                                                                    if int(promotion_product.discount_max_amount) > 0:
                                                                        calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        if order_line.price_unit > promotion_product.discount_max_amount:

                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                'price_unit': promotion_product.discount_max_amount,
                                                                                'line_sub_total': result_subt_total,
                                                                            }
                                                                            if i.name not in self.order_line.mapped(
                                                                                    'description_product'):
                                                                                po_line.create(vals)

                                                                        elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                'price_unit': result_,
                                                                                'line_sub_total': result_subt_total,
                                                                            }
                                                                            if i.name not in self.order_line.mapped(
                                                                                    'description_product'):
                                                                                po_line.create(vals)
                                                                    elif int(
                                                                            promotion_product.discount_max_amount) == 0:

                                                                        vals = {
                                                                            'order_id': self.id,
                                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                                            'description_product': promotion_product.discount_line_product_id.product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            'price_unit': result_,
                                                                            'line_sub_total': result_subt_total,
                                                                        }
                                                                        if i.name not in self.order_line.mapped(
                                                                                'description_product'):
                                                                            po_line.create(vals)


                                                            elif promotion_product.discount_apply_on == 'cheapest_product':
                                                                min_price = min(
                                                                    self.order_line.mapped('price_unit'))
                                                                po_line = self.env['purchase.order.line'].sudo()
                                                                product_min_price = self.order_line.filtered(
                                                                    lambda r: r.price_unit == min_price)
                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit

                                                                        for i in product_min_price:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                'price_unit': promotion_product.discount_max_amount,

                                                                            }

                                                                        if i.product_id.name not in self.order_line.mapped(
                                                                                'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                                'product_id').ids:
                                                                            po_line.create(vals)

                                                                    elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                        chepest_result = -diskon_percentage

                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit

                                                                        for i in product_min_price:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                'price_unit': chepest_result,

                                                                            }

                                                                        if i.product_id.name not in self.order_line.mapped(
                                                                                'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                            'product_id').ids:
                                                                            po_line.create(vals)

                                                                elif int(
                                                                        promotion_product.discount_max_amount) == 0:
                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    chepest_result = -diskon_percentage

                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        vals = {
                                                                            'order_id': self.id,
                                                                            'line_sub_total': resultsubtotal,
                                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                                            'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            'price_unit': chepest_result,

                                                                        }

                                                                    if i.product_id.name not in self.order_line.mapped(
                                                                            'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                        'product_id').ids:
                                                                        po_line.create(vals)

                                                            elif promotion_product.discount_apply_on == 'on_order':

                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if order_line.price_unit > promotion_product.discount_max_amount:
                                                                        po_line = self.env[
                                                                            'purchase.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        on_order = -diskon_percentage

                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                                'price_unit': promotion_product.discount_max_amount,

                                                                            }

                                                                            po_line.create(vals)
                                                                    elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                        po_line = self.env[
                                                                            'purchase.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        on_order = -diskon_percentage

                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            vals = {
                                                                                'order_id': self.id,
                                                                                'line_sub_total': resultsubtotal,
                                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                                'price_unit': on_order,

                                                                            }

                                                                            po_line.create(vals)
                                                                elif int(
                                                                        promotion_product.discount_max_amount) == 0:
                                                                    po_line = self.env[
                                                                        'purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage

                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        vals = {
                                                                            'order_id': self.id,
                                                                            'line_sub_total': resultsubtotal,
                                                                            'product_id': promotion_product.discount_line_product_id.id,
                                                                            'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                            'price_unit': on_order,

                                                                        }

                                                                        po_line.create(vals)

                                                        elif promotion_product.discount_type == 'fixed_amount':

                                                            po_line = self.env['purchase.order.line'].sudo()

                                                            vals = {
                                                                'order_id': self.id,
                                                                'product_id': promotion_product.discount_line_product_id.id,
                                                                'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + promotion_product.name,
                                                                'price_unit': promotion_product.discount_fixed_amount,

                                                            }
                                                            if promotion_product.name not in self.order_line.mapped(
                                                                    'description_product'):
                                                                po_line.create(vals)
        self.order_line = product


