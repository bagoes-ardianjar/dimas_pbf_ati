from odoo import models, fields, api
import datetime
from datetime import datetime



class ati_pbf_promotion_so(models.Model):
    _name = 'so.promotion'
    _description = 'ati_pbf_promotion_so.ati_pbf_promotion_so'

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
    rule_partners_domain = fields.Many2many('res.partner', string="Based on Customers", help="Coupon program will work for selected customers only")
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

    reward_product_desc = fields.Char(string='Discount Product Desc')

    def button_approval_manager_sales(self):
        for rec in self:
            rec.status = True

    def button_cancel(self):
        for rec in self:
            rec.status = False

    @api.onchange('maximum_use_number')
    def onchange_remaining_use(self):
        for rec in self:
            rec.remaining_use_promotion = rec.maximum_use_number

    @api.model
    def create(self, values):

        promotion = self.env['so.promotion'].sudo().search([])

        if values['reward_type'] == 'product':
            values['reward_product_id']
            searchProduct = self.env['product.product'].sudo().search([('id', '=', values['reward_product_id'])])
            name_product = searchProduct.name

            # product = self.env['product.product'].sudo().create({
            #     'name': 'Free product' + ' ' + '-' + ' ' + name_product,
            # })
            #
            # values['discount_line_product_id'] = product.id
        elif values['reward_type'] == 'discount':
            if values['discount_type'] == 'percentage':
                values['discount_specific_product_ids']

                for data in values['discount_specific_product_ids']:
                    id = data[2]

                    searchProduct = self.env['product.product'].sudo().search([('id', '=', id)])

                    percent = str(values['discount_percentage']) + '%'

                    product = self.env['product.product'].sudo().create({
                        'name': percent + ' ' + 'discount on products',
                    })

                    values['discount_line_product_id'] = product.id

        return super(ati_pbf_promotion_so, self).create(values)