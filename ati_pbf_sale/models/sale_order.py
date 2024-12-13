import datetime
from odoo.http import request, route, Response
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo import models, fields, _, api, Command
from datetime import date, timedelta
from odoo.tools import float_is_zero, html_keep_url, is_html_empty
import json
from io import BytesIO
import base64
from datetime import datetime, timedelta



class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def _onchange_template_id(self, template_id, composition_mode, model, res_id):
        res = super(MailComposeMessage, self)._onchange_template_id(template_id, composition_mode, model, res_id)
        context = self._context.copy()
        if model == 'sale.order':
            check_ir_attachment = self.env['ir.attachment'].sudo().search([
                ('res_model','=',model),
                ('res_id', '=', res_id),
                ('res_field', '=', 'attachment_helper')
            ],order="create_date desc",limit=1)
            if check_ir_attachment:
                so_obj = self.env['sale.order'].sudo().browse(res_id)
                check_ir_attachment.name = 'faktur-penjualan-' + so_obj.name
                res['value']['attachment_ids'] = [(6,0,[check_ir_attachment.id])]
        return res

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    _description = 'From quotations to invoices'

    attachment_helper = fields.Binary(string='Attachment Helper')

    def get_jib_report(self):
        record_id = self.id
        report_name = 'ati_pbf_sale.action_report_faktur_penjualan_so_custom'

        # Nama laporan QWeb yang akan digunakan
        report = 'ati_pbf_sale.new_report_faktur_penjualan'

        # Mencari ID laporan berdasarkan nama
        report_id = self.env['ir.actions.report'].search([('report_name', '=', report)])

        if report_id:

            # Menyiapkan data yang diperlukan untuk rendering laporan
            data = {
                'ids': [record_id],  # Ubah agar menjadi daftar ID, bukan ID tunggal
                'model': self._name,
            }

            # Menjalankan metode _render_qweb_pdf untuk menghasilkan PDF
            pdf, output_type = self.env.ref(report_name).sudo()._render_qweb_pdf([record_id], data=data)

            # Menghasilkan nama file PDF berdasarkan timestamp saat ini
            today_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            filename = self.name + '-' + str(today_datetime) + '.pdf'

            # Membungkus hasil PDF dalam base64
            b64_pdf = base64.b64encode(pdf)

            self.attachment_helper = b64_pdf
            self._cr.commit()

            return b64_pdf, output_type, filename

    def action_quotation_send(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        self.ensure_one()
        self.get_jib_report()
        template_id = self._find_mail_template()
        lang = self.env.context.get('lang')
        template = self.env['mail.template'].browse(template_id)
        if template.lang:
            lang = template._render_lang(self.ids)[self.id]
        ctx = {
            'default_model': 'sale.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_paynow",
            'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            'model_description': self.with_context(lang=lang).type_name,
            'new_attachment_id': 123,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }


    def func_update_partner_invoice_id(self):
        update_data = "update sale_order set partner_invoice_id = partner_id " \
                      "where partner_invoice_id <> partner_id"
        self._cr.execute(update_data)
        self._cr.commit()
        return True

    @api.onchange('partner_id','is_pasien')
    def func_onchange_for_margin(self):
        if not self.partner_id and not self.is_pasien:
            return {}
        else:
            if self.state == 'draft':
                for l in self.order_line:
                    if l.is_lock_price != True:
                        if not l.order_id.partner_id.margin_ids or l.order_id.is_pasien == True:
                            if not l.product_id.margin:
                                l.product_margin_percent = '0%'
                            else:
                                l.product_margin_percent = str(l.product_id.margin.name) + '%'
                        else:
                            margin_from_customer = 0
                            for m_margin in l.order_id.partner_id.margin_ids:
                                margin_from_customer += m_margin.value
                                l.product_margin_percent = str(margin_from_customer) + '%'
                    else:
                        pass
            else:
                pass

    def func_update_so_line_existing(self):
        self._cr.execute("""(
            select 
                a.id 
            from sale_order_line a
            join sale_order b on b.id = a.order_id 
            where b.state not in ('draft','cancel')
            and a.product_margin_percent is null
            limit 5000
        )""")
        so_line = self.env['sale.order.line'].sudo().browse([x[0] for x in self._cr.fetchall()])
        for l in so_line:
            if not l.order_id.partner_id.margin_ids or l.order_id.is_pasien == True:
                if not l.product_id.margin:
                    l.product_margin_percent = '0%'
                else:
                    l.product_margin_percent = str(l.product_id.margin.name) + '%'
            else:
                margin_from_customer = 0
                for m_margin in l.order_id.partner_id.margin_ids:
                    margin_from_customer += m_margin.value
                    l.product_margin_percent = str(margin_from_customer) + '%'
        return True

    def get_sml_helper_ids(self):
        for this in self:
            # self._cr.execute("""
            # select a.id
            # from stock_move_line a
            # join stock_move b on b.id = a.move_id
            # join sale_order_line c on c.id = b.sale_line_id
            # join stock_picking_type d on d.id = b.picking_type_id
            # where c.order_id  = {_id} and d.name not like 'Return%'
            # and a.qty_done - coalesce((select x.qty_done from stock_move_line x join stock_move y on y.id=x.move_id where y.origin_returned_move_id = b.id),0) <> 0
            # """.format(_id=this.id))
            self._cr.execute("""
                select 
                    a.id
                from stock_move_line a
                join stock_move b on b.id = a.move_id 
                join sale_order_line c on c.id = b.sale_line_id
                join stock_picking_type d on d.id = b.picking_type_id 
                where c.order_id  = {_id} and d.name not like 'Return%'
                and c.product_uom_qty - coalesce((select x.qty_done from stock_move_line x join stock_move y on y.id=x.move_id where y.origin_returned_move_id = b.id and x.id = a.id),0) <> 0
                and case
                        when a.lot_id in (select x.lot_id from stock_move_line x join stock_move y on y.id=x.move_id where y.origin_returned_move_id = b.id) then 
                            a.qty_done - (select coalesce(sum(x.qty_done),0) from stock_move_line x join stock_move y on y.id=x.move_id where y.origin_returned_move_id = b.id)
                        else a.qty_done
                    end <> 0
            """.format(_id=this.id))
            fet = [x[0] for x in self._cr.fetchall()]
            if len(fet) > 0:
                this.sml_helper_ids = [(6,0,fet)]
            else:
                this.sml_helper_ids = None

    def get_qty_return(self,stock_move_line_id=False):
        for this in self:
            # self._cr.execute("""
            # select a.id,
            # a.qty_done - coalesce((select x.qty_done from stock_move_line x join stock_move y on y.id=x.move_id where y.origin_returned_move_id = b.id),0) as qty_done
            # from stock_move_line a
            # join stock_move b on b.id = a.move_id
            # join sale_order_line c on c.id = b.sale_line_id
            # join stock_picking_type d on d.id = b.picking_type_id
            # where c.order_id  = {_id} and d.name not like 'Return%' and a.id = {_stock_move_line_id}
            # """.format(_id=this.id,_stock_move_line_id=stock_move_line_id))
            self._cr.execute("""
                select 
                    a.id,
                    case
                        when a.lot_id in (select x.lot_id from stock_move_line x join stock_move y on y.id=x.move_id where y.origin_returned_move_id = b.id) then 
                            a.qty_done - (select coalesce(sum(x.qty_done),0) from stock_move_line x join stock_move y on y.id=x.move_id where y.origin_returned_move_id = b.id)
                        else a.qty_done
                    end as qty_done
                from stock_move_line a
                join stock_move b on b.id = a.move_id 
                join sale_order_line c on c.id = b.sale_line_id
                join stock_picking_type d on d.id = b.picking_type_id 
                where c.order_id  = {_id} and d.name not like 'Return%' and a.id = {_stock_move_line_id}
            """.format(_id=this.id, _stock_move_line_id=stock_move_line_id))
            data_check = self._cr.dictfetchall()
            return data_check

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if not self.partner_id:
            self.update({'partner_invoice_id': False,'partner_shipping_id': False,'fiscal_position_id': False,})
            return
        self = self.with_company(self.company_id)
        addr = self.partner_id.address_get(['delivery', 'invoice'])
        partner_user = self.partner_id.user_id or self.partner_id.commercial_partner_id.user_id
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            # 'partner_invoice_id': addr['invoice'],
            'partner_invoice_id': self.partner_id.id,
            'partner_shipping_id': addr['delivery'],
        }
        user_id = partner_user.id
        if not self.env.context.get('not_self_saleperson'):
            user_id = user_id or self.env.context.get('default_user_id', self.env.uid)
        if user_id and self.user_id.id != user_id:
            values['user_id'] = user_id
        if self.env['ir.config_parameter'].sudo().get_param('account.use_invoice_terms'):
            if self.terms_type == 'html' and self.env.company.invoice_terms_html:
                baseurl = html_keep_url(self.get_base_url() + '/terms')
                context = {'lang': self.partner_id.lang or self.env.user.lang}
                values['note'] = _('Terms & Conditions: %s', baseurl)
                del context
            elif not is_html_empty(self.env.company.invoice_terms):
                values['note'] = self.with_context(lang=self.partner_id.lang).env.company.invoice_terms
        if not self.env.context.get('not_self_saleperson') or not self.team_id:
            default_team = self.env.context.get('default_team_id', False) or self.partner_id.team_id.id
            values['team_id'] = self.env['crm.team'].with_context(
                default_team_id=default_team
            )._get_default_team_id(domain=['|', ('company_id', '=', self.company_id.id), ('company_id', '=', False)], user_id=user_id)
        self.update(values)


    sml_helper_ids = fields.Many2many('stock.move.line', 'stock_move_line_sale_order_rel','sale_order_id','stock_move_line_id',compute=get_sml_helper_ids)
    # @api.depends('partner_id','partner_id.jenis_order')
    # def _compute_jenis_order(self):
    #     for sale in self:
    #         if sale.partner_id:
    #             sale.jenis_order = sale.partner_id.jenis_order

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('waiting_approval_apj', 'Waiting Approval APJ'),
        ('waiting_approval_finance', 'Waiting Approval Finance'),
        ('waiting_approval_manager', 'Waiting Approval Manager'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')

    jenis_order = fields.Selection(related='partner_id.x_studio_jenis_order', string='Jenis Order')

    partner_id = fields.Many2one(
        'res.partner', string='Customer (*)', readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        required=True, change_default=True, index=True, tracking=1,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", )

    pricelist_id = fields.Many2one(
        'product.pricelist', string='Pricelist (*)', check_company=True,  # Unrequired company
        required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", tracking=1,
        help="If you change the pricelist, only newly added lines will be affected.")
    is_lock_price = fields.Boolean(string="Is Lock Price", default=False)


    def func_lock_price(self):
        self.is_lock_price = True
        for x in self.order_line:
            x.is_lock_price = True


    def func_unlock_price(self):
        self.is_lock_price = False
        for x in self.order_line:
            x.is_lock_price = False

    
    def button_print_report_faktur_penjualan(self):
        return self.env.ref('ati_pbf_sale.action_report_faktur_penjualan_so_custom').report_action(self)

    @api.depends('order_line.price_total','global_discount')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            line = order.order_line
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax

            amountnya = amount_untaxed - order.global_discount
            for tax in line.tax_id:
                amount_tax_nya = amountnya * tax.amount / 100

                order.update({
                    'amount_untaxed': amount_untaxed,
                    'amount_tax': amount_tax_nya,
                    'amount_total': (amount_untaxed - order.global_discount) + amount_tax_nya,
                })

    @api.depends('no_code_promo_program_ids')
    def _compute_check_promo(self):
        if not self.no_code_promo_program_ids:
            self.check_promo = False
        else:
            self.check_promo = True

    @api.depends('partner_id.expired_registration')
    def _compute_check_cust_exp(self):
        for sale in self:
            if not sale.partner_id.expired_registration or sale.partner_id.expired_registration >= date.today():
                sale.check_cust_exp = False
            elif sale.partner_id.expired_registration < date.today():
                sale.check_cust_exp = True

    @api.depends('user_id')
    def _compute_is_pasien_panel(self):
        is_panel_access = self.env.user.has_group('ati_pbf_sale.sale_order_pasien_panel')
        if not self.env.user.has_group('ati_pbf_sale.sale_order_approval_apj'):
            if not is_panel_access:
                self.pasien_panel = False
            else:
                self.pasien_panel = True

        elif self.env.user.has_group('ati_pbf_sale.sale_order_approval_apj'):
            if not is_panel_access:
                self.pasien_panel = False
            else:
                self.pasien_panel = True
    
    def _payment_term_date(self):
        payment_term_line = self.payment_term_id.line_ids.filtered(lambda line: line.value == 'balance')
        days = payment_term_line.days
        invoice_date_due = self.date_order
        if payment_term_line.option == 'day_after_invoice_date':
            invoice_date_due = invoice_date_due + timedelta(days=days)
        elif payment_term_line.option == 'day_following_month':
            invoice_date_due = (invoice_date_due.replace(day=1) + timedelta(days=31)).replace(day=1) - timedelta(days=1)
            if invoice_date_due.day != days and invoice_date_due.day > days:
                invoice_date_due.replace(day=days)
        elif payment_term_line.option == 'day_current_month':
            invoice_date_due = (invoice_date_due.replace(day=1) + timedelta(days=31)).replace(day=1) - timedelta(days=1)
            if invoice_date_due.day != days and invoice_date_due.day > days:
                invoice_date_due.replace(day=days)
        elif payment_term_line.option == 'after_invoice_month':
            invoice_date_due = (invoice_date_due.replace(day=1) + timedelta(days=31)).replace(day=1) + timedelta(days=days)
        return invoice_date_due

    @api.depends('partner_id')
    def _compute_sales_person(self):
        for this in self:
            if this.partner_id:
                this.sales_person = this.partner_id.sales_person
            else:
                this.sales_person = False

    # added by ibad
    special_discount = fields.Boolean('Special Discount')
    sales_person = fields.Many2one('hr.employee', string='Sales Person (*)',compute=_compute_sales_person, index=True, tracking=1, store=True)
    global_discount = fields.Monetary('Global Discount')
    reason_to_reject_apj = fields.Text('Reason', tracking=True)
    reason_to_reject_finance = fields.Text('Reason', tracking=True)
    reason_to_reject_manager = fields.Text('Reason', tracking=True)
    check_promo = fields.Boolean('Cek Promo', compute='_compute_check_promo', default=False, store=True)
    check_cust_exp = fields.Boolean('Cek Customer Expiration', compute='_compute_check_cust_exp', default=False, store=True)
    is_pasien = fields.Boolean('Is Panel?')
    pasien = fields.Many2one('panel.panel', string='Panel Name (*)', index=True)
    pasien_panel = fields.Boolean(string='Is Access Right?', compute='_compute_is_pasien_panel', index=True)

    ## added by amal
    add_promotion = fields.Boolean('Add Promotion', default=False)
    confirm_date = fields.Date(string='Confirm Date',)

    @api.depends('order_line.tax_id', 'order_line.price_unit', 'amount_total', 'amount_untaxed')
    def _compute_tax_totals_json(self):
        def compute_taxes(order_line):
            additional_margin = order_line.price_unit * order_line.additional_margin / 100
            # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin  # - discount
            dis_res = order_line.harga_satuan_baru

            discount_percent = dis_res * order_line.discount / 100  # - line.discount_amount or 0.0

            # subtotal = ((order_line.price_unit + order_line.product_margin_amount + additional_margin) - (order_line.discount_amount))
            subtotal = ((order_line.harga_satuan_baru) - (order_line.discount_amount))
            order = order_line.order_id

            return order_line.tax_id._origin.compute_all(subtotal, order.currency_id, order_line.product_uom_qty,
                                                         product=order_line.product_id,
                                                         partner=order.partner_shipping_id)

        account_move = self.env['account.move']
        for order in self:
            # total_tax_amount = 0
            tax_perline = 0
            panjang_line = []
            for line in order.order_line:
                if line.price_subtotal > 0:
                    panjang_line.append(line.id)

            global_discount_perline = 0
            for line in order.order_line:
                if order.global_discount > 0 and len(panjang_line) > 0:
                    global_discount_perline = order.global_discount/len(panjang_line)
                else:
                    global_discount_perline = 0
                for tax in line.tax_id:
                    tax_perline += (line.price_subtotal - global_discount_perline) * tax.amount / 100
                # total_tax_amount += tax_perline
            # print(line.price_subtotal,global_discount_perline,total_tax_amount)
            order.amount_total = order.amount_untaxed - order.global_discount + tax_perline
            tax_lines_data = account_move._prepare_tax_lines_data_for_totals_from_object(order.order_line,
                                                                                         compute_taxes)

            tax_totals = account_move._get_tax_totals(order.partner_id, tax_lines_data, order.amount_total,
                                                      order.amount_untaxed, order.currency_id)

            amountnya = order.amount_untaxed - order.global_discount
            order.amount_total = order.amount_untaxed - order.global_discount + tax_perline
            total_amount_sale = order.amount_untaxed - order.global_discount + tax_perline
            for line in order.order_line:
                for tax in line.tax_id:
                    amount_tax_nya = "{0:,.2f}".format(amountnya * tax.amount / 100)

                    if 'groups_by_subtotal' in tax_totals:
                        tax_totals['groups_by_subtotal']['Untaxed Amount'][0]['tax_group_amount'] = amount_tax_nya
                        if not line.currency_id:
                            tax_totals['groups_by_subtotal']['Untaxed Amount'][0]['formatted_tax_group_amount'] = (
                                        '' + ' ' + str(amount_tax_nya))
                        else:
                            tax_totals['groups_by_subtotal']['Untaxed Amount'][0]['formatted_tax_group_amount'] = (line.currency_id.symbol + ' ' + str(amount_tax_nya))
                    for tax_group in tax_totals['groups_by_subtotal']['Untaxed Amount']:
                        if tax_group['tax_group_name'].lower() in tax.name.lower():
                            # print(type(amount_tax_nya))
                            # tax_group['tax_group_amount'] = amount_tax_nya
                            tax_group['formatted_tax_group_amount'] = amount_tax_nya

            if 'Untaxed Amount' in tax_totals['groups_by_subtotal']:
                if tax_totals['groups_by_subtotal']['Untaxed Amount'][0]['tax_group_name'] == False:
                    tax_totals['groups_by_subtotal']['Untaxed Amount'][0]['tax_group_name'] = 'Taxes'

            tax_totals['amount_total'] = total_amount_sale
            tax_totals['formatted_amount_total'] = "Rp\u00a0{:,.2f}".format(total_amount_sale)

            order.tax_totals_json = json.dumps(tax_totals)

    # def action_confirm(self):
    #     if self._get_forbidden_state_confirm() & set(self.mapped('state')):
    #         raise UserError(_(
    #             'It is not allowed to confirm an order in the following states: %s'
    #         ) % (', '.join(self._get_forbidden_state_confirm())))
    #
    #     for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
    #         order.message_subscribe([order.partner_id.id])
    #     self.write(self._prepare_confirmation_values())
    #
    #     # Context key 'default_name' is sometimes propagated up to here.
    #     # We don't need it and it creates issues in the creation of linked records.
    #     context = self._context.copy()
    #     context.pop('default_name', None)
    #
    #     # for sale in self:
    #     #     if sale.partner_id.name == 'PT Berkat Mahkota Putra (Cabang)':
    #     #         for line in sale.order_line:
    #     #             line.order_id.sudo()._action_confirm()
    #     #     else:
    #     self.with_context(context).sudo()._action_confirm()
    #     if self.env.user.has_group('sale.group_auto_done_setting'):
    #         self.action_done()
    #     return True

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        product_not_active = []
        for order_line in self.order_line:
            # active_or_not = [product.activate_product for product in order_line.product_id]

            for product in order_line.product_id:
                if product.activate_product == False:
                    if product.sale_ok:
                        product_not_active.append(product.name)


        if not product_not_active:
            self.write({'confirm_date': fields.Date.today()})
            return res
        else:
            raise ValidationError(
                _("Product Non Active!\nMenunggu approval manager (manager mengaktifkan produk)\n\nNon-active product:\n%s" % (', \n'.join(product_not_active))))

    def confirm_quotation_with_apj(self):

        promotion = self.env['so.promotion'].search([('status', '=', True)])

        for promotion_product in promotion:
            for order_line in self.order_line:
                for product_ids_list in promotion_product.product_ids:
                    if order_line.product_id.id == product_ids_list.id and order_line.is_promotion != True and order_line.is_discount != True and order_line.is_promo != True:
                        raise UserError('Click the Promotion button to check your product got a promo')

        for sale in self:
            # CHECK TAXES IN SO LINE #
            tax_ids = []
            line_tax_ids = []
            for line in sale.order_line:
                if line.tax_id:
                    line_tax_ids.append(line.tax_id)
                    for tax in line.tax_id:
                        tax_ids.append(tax.id)
                    # tax_ids.append(line.tax_id.id)

            first_tax = line_tax_ids[0]

            # Loop untuk membandingkan setiap elemen dengan elemen pertama
            for tax in line_tax_ids:
                if tax != first_tax:
                    raise UserError("Cannot confirm Sale with different taxes.")

            # tax_ids = set(list(tax_ids))
            # if len(tax_ids) > 1:
            #     raise UserError(_('Cannot confirm Sale with different taxes.'))

            ## CHECK PRICE
            check_price = self._context.get('check_price',False)
            if check_price:
                price_check = False
                for line in sale.order_line:
                    if line.price_check:
                        price_check = True
                if price_check:
                    form_view_id = self.env['ir.model.data']._xmlid_to_res_id('ati_pbf_sale.notif_price_so_line')
                    ctx = self._context.copy()
                    # ctx['hs_code_diff'] = True
                    return {
                            'name': _('Check Price'),
                            'type': 'ir.actions.act_window',
                            'res_model': 'sale.order',
                            'view_type': 'form',
                            'view_mode': 'form',
                            'target': 'new',
                            'view_id': False,
                            'res_id': sale.id,
                            'views': [(form_view_id, 'form')],
                            'context': ctx,
                    }

            if not sale.partner_id.expired_registration:
                # cek approval finance jika ada tunggakan di SO sebelumnya ...
                id_of_so = []
                payment_state = []
                so_object = self.search(
                    [('partner_id', '=', sale.partner_id.id), ('order_line.invoice_lines', '!=', False), ('invoice_ids.state', 'not in', ['cancel'])])
                if not so_object:
                    # if not sale.special_discount and not sale.check_promo and not sale.add_promotion:
                    if not sale.special_discount and not sale.check_promo:
                        sale.action_confirm()
                    else:
                        # sale.state = 'waiting_approval_manager'
                        sale.write({
                            'state': 'waiting_approval_manager'
                        })
                else:
                    id_of_so = []
                    payment_state = []
                    so_object = self.search(
                        [('partner_id', '=', sale.partner_id.id), ('order_line.invoice_lines', '!=', False),
                         ('invoice_ids.state', 'not in', ['cancel'])])
                    list_parameter = []
                    for so_ in so_object:
                        for inv in so_.invoice_ids:
                            if inv.payment_state != 'paid' and inv.invoice_date_due < sale.date_order.date() and inv.state == 'posted':
                                list_parameter.append(inv.id)
                            payment_state.append(inv.payment_state)
                    if len(list_parameter) > 0:
                        sale.state = 'waiting_approval_finance'
                    else:
                        if not sale.special_discount and not sale.check_promo:
                            sale.action_confirm()
                        else:
                            # sale.state = 'waiting_approval_manager'
                            sale.write({
                                'state': 'waiting_approval_manager'
                            })

            elif sale.partner_id.expired_registration < date.today():
                # sale.state = 'waiting_approval_apj'
                self.ensure_one()
                ir_model_data = self.env['ir.model.data']
                view = ir_model_data._xmlid_lookup('ati_pbf_sale.ati_quotation_confirm_form_inherit_ib')[2]

                ctx = dict(self.env.context or {})
                ctx.update({
                    'default_model': 'quotation.confirm',
                    'active_model': 'quotation.confirm',
                    'active_id': sale.ids,
                    'partner_id': sale.partner_id.id
                })

                return {
                    'name': _('Attention!'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'quotation.confirm',
                    'views': [(view, 'form')],
                    'view_id': view,
                    'target': 'new',
                    'context': ctx
                }
            elif sale.partner_id.expired_registration >= date.today():
                # cek approval finance jika ada tunggakan di SO sebelumnya ...
                id_of_so = []
                payment_state = []
                so_object = self.search(
                    [('partner_id', '=', sale.partner_id.id), ('order_line.invoice_lines', '!=', False), ('invoice_ids.state', 'not in', ['cancel'])])
                if not so_object:
                    # if not sale.special_discount and not sale.check_promo and not sale.add_promotion:
                    if not sale.special_discount and not sale.check_promo:
                        sale.action_confirm()
                    else:
                        # sale.state = 'waiting_approval_manager'
                        sale.write({
                            'state': 'waiting_approval_manager'
                        })

                else:
                    id_of_so = []
                    payment_state = []
                    so_object = self.search(
                        [('partner_id', '=', sale.partner_id.id), ('order_line.invoice_lines', '!=', False),
                         ('invoice_ids.state', 'not in', ['cancel'])])
                    list_parameter = []
                    for so_ in so_object:
                        for inv in so_.invoice_ids:
                            if inv.payment_state != 'paid' and inv.invoice_date_due < sale.date_order.date() and inv.state == 'posted':
                                list_parameter.append(inv.id)
                            payment_state.append(inv.payment_state)
                    if len(list_parameter) > 0 :
                        sale.state = 'waiting_approval_finance'
                    else:
                        if not sale.special_discount and not sale.check_promo:
                            sale.action_confirm()
                        else:
                            # sale.state = 'waiting_approval_manager'
                            sale.write({
                                'state': 'waiting_approval_manager'
                            })
                        # if 'paid' in payment_state and len(set(payment_state)) == 1:
                        #     # if not sale.special_discount and not sale.check_promo and not sale.add_promotion:
                        #     if not sale.special_discount and not sale.check_promo:
                        #         sale.action_confirm()
                        #     else:
                        #         # sale.state = 'waiting_approval_manager'
                        #         sale.write({
                        #             'state': 'waiting_approval_manager'
                        #         })
                        # else:
                        #     id_of_so = []
                        #     payment_state = []
                        #     so_object = self.search(
                        #         [('partner_id', '=', sale.partner_id.id), ('order_line.invoice_lines', '!=', False),
                        #          ('invoice_ids.state', 'not in', ['cancel'])])
                        #     list_parameter = []
                        #     for so_ in so_object:
                        #         for inv in so_.invoice_ids:
                        #             if inv.payment_state != 'paid' and inv.invoice_date_due < sale.date_order.date() and inv.state == 'posted':
                        #                 list_parameter.append(inv.id)
                        #             # payment_state.append(inv.payment_state)
                        #     if len(list_parameter) > 0:
                        #         sale.state = 'waiting_approval_finance'
                        #     else:
                        #         sale.action_confirm()
            else:
                id_of_so = []
                payment_state = []
                so_object = self.search(
                    [('partner_id', '=', sale.partner_id.id), ('order_line.invoice_lines', '!=', False),
                     ('invoice_ids.state', 'not in', ['cancel'])])
                list_parameter = []
                for so_ in so_object:
                    for inv in so_.invoice_ids:
                        if inv.payment_state != 'paid' and inv.invoice_date_due < sale.date_order.date() and inv.state == 'posted':
                            list_parameter.append(inv.id)
                        # payment_state.append(inv.payment_state)
                if len(list_parameter) > 0:
                    sale.state = 'waiting_approval_finance'
                else:
                    sale.action_confirm()

    def action_continue_confirm(self):
        state = self._context.get('state')
        caller_method = self._context.get('caller_method','confirm_quotation_with_apj')
        if state == 'waiting_approval_manager':
            caller_method = self._context.get('caller_method','approve_manager')
        method = getattr(self.with_context(check_price=False), caller_method)
        return method()

    def approve_apj(self):
        apj_access = self.user_has_groups('ati_pbf_sale.sale_order_approval_apj')
        if not apj_access:
            raise UserError(_('Only APJ can approve it.'))
        else:
            for sale in self:
                # cek approval finance jika ada tunggakan di SO sebelumnya ...
                id_of_so = []
                payment_state = []
                so_object = self.search(
                    [('partner_id', '=', sale.partner_id.id), ('order_line.invoice_lines', '!=', False), ('invoice_ids.state', 'not in', ['cancel'])])
                if not so_object:
                    # if not sale.special_discount and not sale.check_promo and not sale.add_promotion:
                    if not sale.special_discount and not sale.check_promo:
                        sale.action_confirm()
                    else:
                        # sale.state = 'waiting_approval_manager'
                        sale.write({
                            'state': 'waiting_approval_manager'
                        })

                else:
                    id_of_so = []
                    payment_state = []
                    so_object = self.search(
                        [('partner_id', '=', sale.partner_id.id), ('order_line.invoice_lines', '!=', False),
                         ('invoice_ids.state', 'not in', ['cancel'])])
                    list_parameter = []
                    for so_ in so_object:
                        for inv in so_.invoice_ids:
                            if inv.payment_state != 'paid' and inv.invoice_date_due < sale.date_order.date() and inv.state == 'posted':
                                list_parameter.append(inv.id)
                            payment_state.append(inv.payment_state)
                    if len(list_parameter) > 0:
                        sale.state = 'waiting_approval_finance'
                    else:
                        if not sale.special_discount and not sale.check_promo:
                            sale.action_confirm()
                        else:
                            # sale.state = 'waiting_approval_manager'
                            sale.write({
                                'state': 'waiting_approval_manager'
                            })
                        # if 'paid' in payment_state and len(set(payment_state)) == 1:
                        #     # if not sale.special_discount and not sale.check_promo and not sale.add_promotion:
                        #     if not sale.special_discount and not sale.check_promo:
                        #         sale.action_confirm()
                        #     else:
                        #         # sale.state = 'waiting_approval_manager'
                        #         sale.write({
                        #             'state': 'waiting_approval_manager'
                        #         })
                        # else:
                        #     id_of_so = []
                        #     payment_state = []
                        #     so_object = self.search(
                        #         [('partner_id', '=', sale.partner_id.id), ('order_line.invoice_lines', '!=', False),
                        #          ('invoice_ids.state', 'not in', ['cancel'])])
                        #     list_parameter = []
                        #     for so_ in so_object:
                        #         for inv in so_.invoice_ids:
                        #             if inv.payment_state != 'paid' and inv.invoice_date_due < sale.date_order.date() and inv.state == 'posted':
                        #                 list_parameter.append(inv.id)
                        #             # payment_state.append(inv.payment_state)
                        #     if len(list_parameter) > 0:
                        #         sale.state = 'waiting_approval_finance'
                        #     else:
                        #         sale.action_confirm()


    def approve_finance(self):
        finance_access = self.user_has_groups('ati_pbf_sale.sale_order_approval_finance')
        if not finance_access:
            raise UserError(_('Only finance team can approve it.'))
        else:
            for sale in self:
                # cek apakah ada special discount atau promotion di SO ...
                # if not sale.special_discount and not sale.check_promo and not sale.add_promotion:
                if not sale.special_discount and not sale.check_promo:
                    sale.action_confirm()
                else:
                    # sale.state = 'waiting_approval_manager'
                    sale.write({
                        'state': 'waiting_approval_manager'
                    })



    def approve_manager(self):
        manager_access = self.user_has_groups('ati_pbf_sale.sale_order_approval_manager')

        ## CHECK PRICE
        check_price = self._context.get('check_price',False)
        if check_price:
            price_check = False
            for line in self.order_line:
                if line.price_check:
                    price_check = True
            if price_check:
                form_view_id = self.env['ir.model.data']._xmlid_to_res_id('ati_pbf_sale.notif_price_so_line')
                ctx = self._context.copy()
                # ctx['hs_code_diff'] = True
                return {
                        'name': _('Check Price'),
                        'type': 'ir.actions.act_window',
                        'res_model': 'sale.order',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'target': 'new',
                        'view_id': False,
                        'res_id': self.id,
                        'views': [(form_view_id, 'form')],
                        'context': ctx,
                }

        if not manager_access:
            raise UserError(_('Only manager can approve it.'))
        else:
            for sale in self:
                # sale.state = 'sale'
                sale.action_confirm()

    def reject_apj(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        view = ir_model_data._xmlid_lookup('ati_pbf_sale.ati_reason_reject_sale_order_form_inherit_ib_apj')[2]

        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'sale.order',
            'active_model': 'sale.order',
            'active_id': self.ids[0]
        })

        return {
            'name': _('Reject'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sale.order.reject.apj',
            'views': [(view, 'form')],
            'view_id': view,
            'target': 'new',
            'context': ctx
        }

    def reject_finance(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        view = ir_model_data._xmlid_lookup('ati_pbf_sale.ati_reason_reject_sale_order_form_inherit_ib_finance')[2]

        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'sale.order',
            'active_model': 'sale.order',
            'active_id': self.ids[0]
        })

        return {
            'name': _('Reject'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sale.order.reject.finance',
            'views': [(view, 'form')],
            'view_id': view,
            'target': 'new',
            'context': ctx
        }

    def reject_manager(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        view = ir_model_data._xmlid_lookup('ati_pbf_sale.ati_reason_reject_sale_order_form_inherit_ib_manager')[2]

        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'sale.order',
            'active_model': 'sale.order',
            'active_id': self.ids[0]
        })

        return {
            'name': _('Reject'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sale.order.reject.manager',
            'views': [(view, 'form')],
            'view_id': view,
            'target': 'new',
            'context': ctx
        }


    def _create_inv_product_delivered_more_than_three_day(self):
        picking_id = []
        invoice_id = []
        self._cr.execute("""
                                select
                                    a.id as so_id,
                                    b.id as am_id,
                                    b.invoice_date as invoice_date
                                from sale_order a
                                    join account_move b on b.sales_reference = a.name
                                where b.move_type = 'out_invoice'
                                    and b.state = 'draft'
                                    and a.state not in ('cancel')
                            """.format())
        data_check = self._cr.dictfetchall()
        for data in data_check:
            range_of_days = (datetime.now().date()) - data['invoice_date']
            if range_of_days.days >= 3:
                sale_obj = self.env['sale.order'].search([('id', '=', data['so_id'])])
                for sale in sale_obj:
                    if not sale.activity_ids:
                        todos = {
                            'res_id': sale.id,
                            'res_model_id': self.env['ir.model'].search([('model', '=', 'sale.order')]).id,
                            'user_id': 1,
                            'summary': '',
                            'note': 'confirm invoice',
                            'activity_type_id': self.env['mail.activity.type'].search(
                                [('name', '=', 'To Do')], limit=1).id,
                            'date_deadline': date.today()
                        }
                        self.env['mail.activity'].create(todos)
        # sale_obj = self.env['sale.order'].search([('state', 'not in', ['cancel'])])
        # for sale in sale_obj:
            # if sale.picking_ids:
            #     for picking in sale.picking_ids:
            #         if picking.id not in picking_id:
            #             picking_id.append(picking.id)
            #
            #
            #         pick_obj = self.env['stock.picking'].search([('id', '=', min(picking_id))])
            #
            #         if pick_obj.date_done:
            #             range_of_days = (datetime.now() + timedelta(hours=7)) - (pick_obj.date_done + timedelta(hours=7))
            #             if not sale.invoice_ids:
            #                 if not sale.activity_ids:
            #                     if range_of_days.days >= 3:
            #                         todos = {
            #                             'res_id': sale.id,
            #                             'res_model_id': self.env['ir.model'].search([('model', '=', 'sale.order')]).id,
            #                             'user_id': 1,
            #                             'summary': '',
            #                             'note': 'create invoice',
            #                             'activity_type_id': self.env['mail.activity.type'].search([('name', '=', 'To Do')], limit=1).id,
            #                             'date_deadline': date.today()
            #                         }
            #                         self.env['mail.activity'].create(todos)
            #
            #             picking_id.clear()

    def write(self, val):
        # res = super().write(val)
        res = super(SaleOrder, self).write(val)
        product = []

        for order_line in self.order_line:
            if order_line.product_uom_qty:
                if ((round(order_line.price_subtotal/order_line.product_uom_qty, 2)) < (round(order_line.price_unit, 2))):
                    product.append(order_line.product_id.name)

        # if product:
            # raise UserError(_('Product (%s) tidak dapat diproses karena kurang dari harga modal' % (', '.join(product))))

        if 'is_pasien' in val:
            for this in self:
                am_obj =  self.env['account.move'].sudo().search([('invoice_origin','=',this.name)])
                if am_obj:
                    for rec in am_obj:
                        rec.is_pasien = val['is_pasien']
                        if rec.is_pasien == False:
                            rec.pasien = None
                        else:
                            rec.pasien = this.pasien.id
                for l in this.order_line:
                    if this.state == 'draft':
                        if l.is_lock_price != True:
                            if not this.partner_id.margin_ids or this.is_pasien == True:
                                if not l.product_id.margin:
                                    l.product_margin_percent = '0%'
                                else:
                                    l.product_margin_percent = str(l.product_id.margin.name) + '%'
                            else:
                                margin_from_customer = 0
                                for m_margin in this.partner_id.margin_ids:
                                    margin_from_customer += m_margin.value
                                    l.product_margin_percent = str(margin_from_customer) + '%'
                        else:
                            pass
                    else:
                        pass
        if 'order_line' in val:
            for l in self.order_line:
                if self.state == 'draft':
                    if l.is_lock_price != True:
                        if not self.partner_id.margin_ids or self.is_pasien == True:
                            if not l.product_id.margin:
                                l.product_margin_percent = '0%'
                            else:
                                l.product_margin_percent = str(l.product_id.margin.name) + '%'
                        else:
                            margin_from_customer = 0
                            for m_margin in self.partner_id.margin_ids:
                                margin_from_customer += m_margin.value
                                l.product_margin_percent = str(margin_from_customer) + '%'
                    else:
                        pass
                else:
                    pass
        if 'pasien' in val:
            for this in self:
                am_obj = self.env['account.move'].sudo().search([('invoice_origin', '=', this.name)])
                if am_obj:
                    for rec in am_obj:
                        rec.is_pasien = this.is_pasien
                        if rec.is_pasien == False:
                            rec.pasien = None
                        else:
                            rec.pasien = val['pasien']
        return res

    def create(self, val):
        # res = super().create
        res = super(SaleOrder, self).create(val)
        product = []

        for order_line in res.order_line:
            if ((round(order_line.price_subtotal / order_line.product_uom_qty, 2)) < (round(order_line.price_unit, 2))):
                product.append(order_line.product_id.name)

        for this in res:
            for l in this.order_line:
                if this.state == 'draft':
                    if l.is_lock_price != True:
                        if not this.partner_id.margin_ids or this.is_pasien == True:
                            if not l.product_id.margin:
                                l.product_margin_percent = '0%'
                            else:
                                l.product_margin_percent = str(l.product_id.margin.name) + '%'
                        else:
                            margin_from_customer = 0
                            for m_margin in this.partner_id.margin_ids:
                                margin_from_customer += m_margin.value
                                l.product_margin_percent = str(margin_from_customer) + '%'
                    else:
                        pass
                else:
                    pass

        # if product:
        #     raise UserError(_('Product (%s) tidak dapat diproses karena kurang dari harga modal' % (', '.join(product))))

        return res

    def _func_cancel_so(self):
        sale_ids = self.env['sale.order'].search([('state', '=', 'sale')])
        for sale in sale_ids:
            if sale.confirm_date:
                today = fields.Date.today()
                confirm_date = sale.confirm_date
                dateDiff = (today - confirm_date).days
                if dateDiff >= int(3):
                    if any(pick.state in ('draft','confirmed','assigned') for pick in sale.picking_ids):
                        sale.action_cancel()


class payment_term(models.Model):
    _inherit = 'account.payment.term'

    is_cod = fields.Boolean(string="Is COD")

class account_move(models.Model):
    _inherit = 'account.move'

    @api.model
    def create(self, val):
        # res = super().create
        res = super(account_move, self).create(val)
        for rec in res:
            so_obj =  self.env['sale.order'].sudo().search([('name','=',rec.invoice_origin)])
            if so_obj:
                for this in so_obj:
                    this.is_pasien = so_obj.is_pasien
                    if this.is_pasien == False:
                        this.pasien = None
                    else:
                        this.pasien = so_obj.pasien.id
        return res

    is_pasien = fields.Boolean(string="Is Panel?")
    pasien = fields.Many2one('panel.panel', string='Panel Name')