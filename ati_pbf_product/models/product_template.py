import lxml.etree
from odoo import models, fields, _, api
from odoo.exceptions import ValidationError, RedirectWarning, UserError
from datetime import datetime, time, timedelta, date

class product_template_ib(models.Model):
    _inherit = 'product.template'
    _description = 'Product template'

    def func_update_internal_reference(self):
        update_data = "update product_template set default_code = sku || '/' || new_sku"
        self._cr.execute(update_data)
        self._cr.commit()
        return True

    def write(self, vals):
        res = super(product_template_ib, self).write(vals)
        if 'margin' in vals:
            for this in self:
                so_line = self.env['sale.order.line'].sudo().search([('product_id.product_tmpl_id', '=', this.id)])
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
                vals_historical = {
                    'name': this.name + ' | ' + self.env.user.name,
                    'product_tmpl_id': this.id,
                    'user_id': self.env.user.id,
                    'change_date': datetime.now(),
                    'margin': vals['margin'],
                    'note': 'Margin diisi' if vals['margin'] != False else 'Margin tidak diisi'
                }
                new_historical = self.env['ati.historical.margin.product'].sudo().create(vals_historical)
        return res

    # @api.depends('user_id')
    def _compute_is_admin(self):
        if self.env.user.name != 'Administrator':
            for prd in self:
                prd.is_admin = False

        elif self.env.user.name == 'Administrator':
            for prd in self:
                prd.is_admin = True

    def _compute_is_other_user(self):
        other_user_hasgroup = self.user_has_groups('ati_pbf_product.product_template_approval_other_user')
        if not other_user_hasgroup:
            self.is_other_user = False
        else:
            self.is_other_user = True

    def _compute_is_manager(self):
        manager_hasgroup = self.user_has_groups('ati_pbf_product.product_template_approval_manager')
        if not manager_hasgroup:
            self.is_manager = False
        else:
            self.is_manager = True

    @api.depends('new_sku', 'sku')
    def compute_default_code(self):
        for this in self:
            print(this.new_sku,this.sku)
            if this.sku:
                default_code = str(this.sku) +'/' + str(this.new_sku)
            else:
                default_code = '/' + str(this.new_sku)
            this.default_code = default_code

    default_code = fields.Char('Internal Reference', compute=compute_default_code, store=True)
    new_sku = fields.Char('New SKU', default='/')
    sku = fields.Char('Old SKU')
    nie = fields.Char('NIE')
    kode_bpom = fields.Char('Kode BPOM')
    # pabrik = fields.Char('Pabrik')
    pabrik = fields.Many2one('pabrik.product', string='Pabrik')
    pabrik_reference = fields.Char('Pabrik Alias')
    jenis_obat = fields.Many2one('jenis.obat', string='Jenis Obat', store=True)
    distribution_type = fields.Selection(selection=[
            ('dalam_negeri', 'Dalam Negeri'),
            ('luar_negeri', 'Luar Negeri')
        ], string='Distribution Type')
    industry_code = fields.Char('Industry Code')
    bentuk_sediaan = fields.Many2one('bentuk.sediaan', string='Bentuk Sediaan')
    hna = fields.Float('HNA')
    margin = fields.Many2one('margin.product', string='Margin', tracking=True,)
    jenis_product = fields.Selection(
        [('ppn', 'PPN'), ('non-ppn', 'Non PPN')], 'Jenis Product', index=True)
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('waiting', 'Waiting Approval'),
        ('done', 'Completed')
    ], string='State', required=True, readonly=False, copy=False, tracking=True, default='draft')
    approval_note = fields.Text('Note', tracking=True)
    reason_to_reject = fields.Text('Reason', tracking=True)
    activate_product = fields.Boolean('Active', default=False)
    purchase_price = fields.Float('Purchase Price', compute='_compute_po_price', readonly=False)
    # list_price = fields.Float(
    #     'Sales Price', default=1.0,
    #     digits='Product Price',
    #     compute='_compute_list_price',
    #     help="Price at which the product is sold to customers.",
    #     readonly=False,
    #     store=True
    # )
    is_admin = fields.Boolean(compute='_compute_is_admin', readonly=False)
    is_other_user = fields.Boolean(compute='_compute_is_other_user', readonly=False)
    is_manager = fields.Boolean(compute='_compute_is_manager', readonly=False)
    # # added 07/12/2022
    # list_price = fields.Float('Sales Price',company_dependent=True, default=1.0,digits='Product Price',help="Price at which the product is sold to customers.",)
    list_price = fields.Float('Sales Price', compute='_compute_list_price', default=1.0,digits='Product Price',help="Price at which the product is sold to customers.",)
    composition = fields.Text('Composition', translate=True)
    kemasan = fields.Text('Kemasan', translate=True)
    harga_jual = fields.Monetary('Harga Jual', currency_field='currency_id', compute='_compute_harga_jual')
    harga_jual_incl_ppn = fields.Monetary('Harga Jual Incl PPN', currency_field='currency_id', compute='_compute_harga_jual_incl_ppn')
    harga_awal_ga = fields.Float(string="Harga Awal GA",currency_field='currency_id')
    standard_price = fields.Float(
        'Cost', compute='_compute_standard_price',
        inverse='_set_standard_price', search='_search_standard_price',
        digits='Product Price', groups="base.group_user",
        tracking=True,
        help="""In Standard Price & AVCO: value of the product (automatically computed in AVCO).
            In FIFO: value of the next unit that will leave the stock (automatically computed).
            Used to value the product when the purchase cost is not known (e.g. inventory adjustment).
            Used to compute margins on sale orders.""")
    name = fields.Char('Name', index=True, required=True, translate=True, tracking=True,)
    historical_margin_ids = fields.One2many('ati.historical.margin.product', 'product_tmpl_id', string="Historical Margin")
    purchase_category_id = fields.Many2one('ati.purchase.category', string="Purchase Category")

    @api.depends('standard_price', 'margin')
    def _compute_harga_jual(self):
        for rec in self:
            percentage = rec.standard_price * rec.margin.name / 100
            rec.harga_jual = rec.standard_price + percentage

    @api.depends('harga_jual', 'taxes_id', 'taxes_id.amount')
    def _compute_harga_jual_incl_ppn(self):
        for rec in self:
            percentage = rec.harga_jual * rec.taxes_id.amount / 100
            rec.harga_jual_incl_ppn = rec.harga_jual + percentage

    @api.model
    def create(self, vals):
        if vals.get('new_sku', '/') == '/':
            vals['new_sku'] = self.env['ir.sequence'].next_by_code('ati.product.new.sku') or '/'
        # check_product = self.env['product.product'].sudo().search([('product_tmpl_id','=',vals.get('id'))])
        # for x in check_product:
        #     x.harga_awal_ga = vals.get('harga_awal_ga')
        return super().create(vals)

    # def write(self, vals):
    #     print('111')
    #     res = super(product_template_ib, self).write(vals)
    #     if 'harga_awal_ga' in vals:
    #         check_product = self.env['product.product'].sudo().search([('product_tmpl_id', '=', self.id)])
    #         for rec in check_product:
    #             print('222')
    #             rec.harga_awal_ga = vals['harga_awal_ga']
    #     return res

    @api.constrains('use_expiration_date')
    def use_expiration_date_check(self):
        for rec in self:
            if rec.tracking != 'none':
                if rec.use_expiration_date == False:
                    raise UserError(_('Expiration date is required field!'))

    # @api.depends('standard_price')
    # def _compute_list_price(self):
    #     for prd in self:
    #         prd.list_price = prd.standard_price

    @api.depends('standard_price','product_variant_ids.standard_price')
    def _compute_list_price(self):
        for rec in self:
            if rec.product_variant_ids and rec.mapped('product_variant_ids').mapped('company_sales_price_ids').filtered(lambda r: r.is_active) and len(rec.product_variant_ids) == 1:
                rec.list_price = sum(rec.mapped('product_variant_ids').mapped('lst_price')) or sum(rec.mapped('product_variant_ids').mapped('standard_price'))
            else:
                rec.list_price = rec.standard_price


    @api.depends('seller_ids')
    def _compute_po_price(self):
        product_id = []
        seller_id = []
        effective_date = []
        for product in self:
            for seller in product.seller_ids:
                product_id.append(product.id)
                seller_id.append(seller.id)
                effective_date.append(seller.effective_date)

        if False in effective_date:
            while False in effective_date:
                effective_date.remove(False)
        else:
            pass

        if not effective_date:
            pass
        else:
            seller_obj = self.env['product.supplierinfo'].search([('product_tmpl_id', 'in', product_id), ('effective_date', '=', max(effective_date))])
            for seller_obj_ in seller_obj:
                seller_obj_.product_tmpl_id.purchase_price = seller_obj_.price

    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(product_template_ib, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                  toolbar=toolbar, submenu=submenu)
        doc = lxml.etree.XML(res['arch'])
        user_hasgroup = self.user_has_groups('ati_pbf_product.product_template_approval_user')
        user_manager = self.user_has_groups('ati_pbf_product.product_template_approval_manager')
        other_user_hasgroup = self.user_has_groups('ati_pbf_product.product_template_approval_other_user')

        if view_type == 'form' and not user_hasgroup and not self.env.user.name == 'Administrator' and not user_manager:
            if other_user_hasgroup:
                for node_form in doc.xpath("//form"):
                    node_form.set("create", 'false')
                    # node_form.set("edit", 'true')
                    node_form.set("edit", 'false')
            else:
                for node_form in doc.xpath("//form"):
                    node_form.set("create", 'false')
                    node_form.set("edit", 'false')

        elif view_type == 'tree' and not user_hasgroup and not self.env.user.name == 'Administrator' and not user_manager:
            for node_form in doc.xpath("//tree"):
                node_form.set("create", 'false')
                node_form.set("edit", 'false')

        elif view_type == 'kanban' and not user_hasgroup and not self.env.user.name == 'Administrator' and not user_manager:
            for node_form in doc.xpath("//kanban"):
                node_form.set("create", 'false')
                node_form.set("edit", 'false')

        elif view_type == 'form' and self.env.user.name == 'Administrator':
            for node_form in doc.xpath("//form"):
                node_form.set("create", 'true')
                node_form.set("edit", 'true')

        res['arch'] = lxml.etree.tostring(doc)
        return res

    def submit(self):
        self.write(
            {
                'state': 'waiting'
            }
        )

    def approve(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        view = ir_model_data._xmlid_lookup('ati_pbf_product.ati_reason_product_template_approval_form_inherit_ib')[2]

        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'product.template',
            'active_model': 'product.template',
            'active_id': self.ids[0]
        })

        return {
            'name': _('Product Approval'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'product.template.approval',
            'views': [(view, 'form')],
            'view_id': view,
            'target': 'new',
            'context': ctx
        }

    def reject(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        view = ir_model_data._xmlid_lookup('ati_pbf_product.ati_reason_reject_product_template_form_inherit_ib')[2]

        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'product.template',
            'active_model': 'product.template',
            'active_id': self.ids[0]
        })

        return {
            'name': _('Reject'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'product.template.reject',
            'views': [(view, 'form')],
            'view_id': view,
            'target': 'new',
            'context': ctx
        }

class product_template_approval_ib(models.Model):
    _name = 'product.template.approval'
    _description = 'Product Template Approval'

    name = fields.Text('Note')

    def approve_act_popup(self):
        ctx = dict(self.env.context or {})

        product_template = self.env['product.template'].browse(ctx['active_ids'])
        for prt in product_template:
            prt.approval_note = self.name
            prt.write(
                {
                    'state': 'done'
                }
            )
        # added 07/12/2022
        self._set_company_sales_price(product_template=product_template)
        
    
    def _set_company_sales_price(self, product_template=None):
        if product_template:
            Company = self.env['res.company'].sudo().search([])
            CompanySalesPrice = self.env['company.sale.price'].sudo()
            ctx = self.env.context
            for prod in product_template.mapped('product_variant_ids'):
                for com in Company:
                    if not prod.company_sales_price_ids.filtered(lambda r: r.company_id.id == com.id and r.is_active):
                        # if self.env.company.id == com.id:
                        CompanySalesPrice |= CompanySalesPrice.create({
                            'product_id': prod.id,
                            'company_id': com.id,
                            'is_active': True
                        })
            for c in CompanySalesPrice:
                if c.company_id.id == self.env.company.id:
                    c.lst_price = c.product_id.product_tmpl_id.standard_price
                else:
                    # c.product_id.lst_price = 0
                    c.lst_price = 0


class product_template_reject_ib(models.Model):
    _name = 'product.template.reject'
    _description = 'Product Template Reject'

    name = fields.Text('Reason')

    def reject_act_popup(self):
        ctx = dict(self.env.context or {})

        product_template = self.env['product.template'].browse(ctx['active_ids'])
        for prt in product_template:
            prt.reason_to_reject = self.name
            prt.write(
                {
                    'state': 'draft'
                }
            )


class ati_historical_margin_product(models.Model):
    _name = 'ati.historical.margin.product'

    name = fields.Char(string="Name")
    product_tmpl_id = fields.Many2one('product.template', string="Product Template")
    user_id = fields.Many2one('res.users', string="User Id")
    change_date = fields.Datetime(string="Change Date")
    margin = fields.Many2one('margin.product', string="Margin (%)")
    note = fields.Char(string="Note")

class ati_purchase_category(models.Model):
    _name = 'ati.purchase.category'

    name = fields.Char(string="Name")
    active = fields.Boolean(string="Active", default=True)