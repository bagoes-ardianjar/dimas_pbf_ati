from odoo import models, fields, _, api
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError

class product_product_ib(models.Model):
    _inherit = 'product.product'
    _description = 'Product product'

    # inherited fields ... .
    state = fields.Selection(related='product_tmpl_id.state', string='State')
    activate_product = fields.Boolean(related='product_tmpl_id.activate_product', string='Active')
    sku = fields.Char('Old SKU', related='product_tmpl_id.sku')
    nie = fields.Char('NIE', related='product_tmpl_id.nie')
    kode_bpom = fields.Char('Kode BPOM', related='product_tmpl_id.kode_bpom')
    pabrik = fields.Many2one('pabrik.product', string='Pabrik', related='product_tmpl_id.pabrik')
    pabrik_reference = fields.Char('Pabrik Alias', related='product_tmpl_id.pabrik_reference')
    jenis_obat = fields.Many2one('jenis.obat', string='Jenis Obat', store=True, related='product_tmpl_id.jenis_obat')
    distribution_type = fields.Selection(selection=[
        ('dalam_negeri', 'Dalam Negeri'),
        ('luar_negeri', 'Luar Negeri')
    ], string='Distribution Type', related='product_tmpl_id.distribution_type')
    industry_code = fields.Char('Industry Code', related='product_tmpl_id.industry_code')
    bentuk_sediaan = fields.Many2one('bentuk.sediaan', string='Bentuk Sediaan', related='product_tmpl_id.bentuk_sediaan')
    hna = fields.Float('HNA', related='product_tmpl_id.hna')
    margin = fields.Many2one('margin.product', string='Margin', related='product_tmpl_id.margin', tracking=True,)
    jenis_product = fields.Selection(
        [('ppn', 'PPN'), ('non-ppn', 'Non PPN')], 'Jenis Product', index=True, related='product_tmpl_id.jenis_product')
    # set readonly=False (composition field)
    composition = fields.Text('Composition', related='product_tmpl_id.composition', readonly=False)
    kemasan = fields.Text('Kemasan', related='product_tmpl_id.kemasan')
    harga_awal_ga = fields.Float(string="Harga Awal GA", currency_field='currency_id', related='product_tmpl_id.harga_awal_ga')
    standard_price = fields.Float(
        'Cost', company_dependent=True,
        digits='Product Price',
        tracking=True,
        groups="base.group_user",
        help="""In Standard Price & AVCO: value of the product (automatically computed in AVCO).
            In FIFO: value of the next unit that will leave the stock (automatically computed).
            Used to value the product when the purchase cost is not known (e.g. inventory adjustment).
            Used to compute margins on sale orders.""")

    # add 07/12/2022
    company_sales_price_ids = fields.One2many('company.sale.price', 'product_id', string='Sales Price')

    @api.model_create_multi
    def create(self, vals_list):
        res = super(product_product_ib, self).create(vals_list)

        if 'margin' in vals_list[0]:
            if vals_list[0]['margin'] != False:
                raise ValidationError(_("You can only change the margin from Inventory Menu"))

        else:
            pass

        return res

    def write(self, vals):
        res = super(product_product_ib, self).write(vals)

        for prd_prd in self:
            if 'margin' not in vals:
                pass
            elif 'margin' in vals:
                raise ValidationError(_("You can only change the margin from Inventory Menu"))
            else:
                pass

        return res

# class product_supplerinfo_for_product_product_ib(models.Model):
#     _inherit = 'product.supplierinfo'
#     _description = 'Product supplierinfo for product.product'
#
#     # added by ibad ...
#     discount_1 = fields.Integer('Discount 1 (%)')
#     discount_2 = fields.Integer('Discount 2 (%)')
#     discount_3 = fields.Integer('Discount 3')
#     discount_4 = fields.Integer('Discount 4')
#     effective_date = fields.Datetime('Effective Date')
#     price_include_ppn = fields.Float('Price (Include PPN)')
#     hna = fields.Char(compute='_get_hna', string='HNA')
#
#     def _get_hna(self):
#         for prd in self.product_tmpl_id:
#             self.hna = prd.hna


    def company_sales_price_view(self):
        domain = [('product_id', '=', self.id),('company_id','=',self.env.company.id)]
        return {
            'name': _('Company Sales Price'),
            'domain': domain,
            'res_model': 'company.sale.price',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'help': ('''<p class="o_view_nocontent_smiling_face">
                            Click to Create for Company sales price
                        </p>'''),
            'limit': 80,
            'context': "{'default_product_id': %s}" % (self.id)
        }

    # override origin func odoo. 07/12/2022
    @api.depends('list_price', 'price_extra')
    @api.depends_context('uom')
    def _compute_product_lst_price(self):
        to_uom = None
        if 'uom' in self._context:
            to_uom = self.env['uom.uom'].browse(self._context['uom'])

        for product in self:
            if to_uom:
                list_price = product.uom_id._compute_price(product.list_price, to_uom)
            else:
                list_price = product.list_price
            product.lst_price = list_price + product.price_extra
            # update again
            product.lst_price = product._forced_set_sales_price(sales_price=product.lst_price)

    
    def _forced_set_sales_price(self,**kwargs):
        sales_price = 0
        for rec in self:
            # if rec.categ_id and rec.categ_id.property_cost_method in ('average'):
            if rec.categ_id and rec.categ_id.property_cost_method:
                sales_price = sum(rec.company_sales_price_ids.filtered(lambda r: r.product_id.id == rec.id and r.company_id.id == rec.env.company.id and r.is_active).mapped('lst_price')) or 0
            else:
                sales_price = kwargs.get('sales_price',0)
        return sales_price

    def action_manage_company_sales_price(self):
        action = self.env.ref('ati_pbf_product.action_company_sale_price_wiz').read()[0]
        return action
    

class CompanySalesPrice(models.Model):
    _name = 'company.sale.price'
    _description = 'Company Sales Price'


    product_id = fields.Many2one('product.product', string='Product')
    company_id = fields.Many2one('res.company', string='Company',default=lambda self: self.env.company.id, index=1)
    currency_id = fields.Many2one('res.currency', string='Currency',default=lambda self: self.env.company.currency_id.id)
    lst_price = fields.Float('Sales Price',digits='Product Price', compute='compute_company_sales_price', inverse='',help="The sale price is managed from the product. Click on the 'Configure Variants' button to set the company sales prices.")
    is_active = fields.Boolean(string='Active ?', default=True)


    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id,'%s: %s' % (rec.product_id.name if rec.product_id else 'New','{:,}'.format(rec.lst_price) or 0)))
        return res

    
    @api.depends('product_id','product_id.standard_price','product_id.uom_id','product_id.lst_price')
    # @api.depends('product_id','product_id.standard_price','product_id.uom_id')
    def compute_company_sales_price(self):
        for rec in self:
            if rec and rec.product_id and rec.company_id.id == rec.env.company.id:
                rec.lst_price = rec.product_id.standard_price or 0
            else:
                # rec.lst_price = rec.product_id.standard_price
                rec.lst_price = 0

            rec.product_id.lst_price = rec.lst_price
            # rec.product_id.product_tmpl_id.list_price = rec.lst_price

