from odoo import models, fields, _, api
from odoo.http import request
from odoo.exceptions import UserError
from json import dumps
import uuid
import http
from odoo.exceptions import UserError, ValidationError, Warning, RedirectWarning
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.tools.misc import clean_context, OrderedSet
from collections import defaultdict

class DeliveryOrder(models.Model):
    _inherit = 'stock.picking'
    _description = 'Stock & Logistic Management'

    def _compute_is_requested(self):
        msg_id = self.env['mail.message'].search([('model', '=', 'stock.picking'),
                                                  ('res_id', '=', self.id),
                                                  ('is_requested_open_do', '=', True),
                                                  ('is_approved', '=', False),
                                                  ('is_rejected', '=', False),
                                                  ('author_id', '=', self.env.user.partner_id.id)], limit=1, order='id asc')
        if not msg_id:
            self.is_requested = False
        else:
            self.is_requested = True

    @api.depends('do_reportbutton', 'do_reportbutton.name', 'do_reportbutton.button_clicked', 'do_reportbutton.picking_ids')
    def _compute_one_click(self):
        check_for_click = self.env['do.reportbutton.click'].search(
            [('name', 'in', self.env.user.ids), ('picking_ids', 'in', self.ids)])
        if not check_for_click:
            self.one_click = False

        else:
            for check_for_click_ in check_for_click:
                if check_for_click_.button_clicked == False:
                    self.one_click = False
                elif check_for_click_.button_clicked == True:
                    self.one_click = True

    def _compute_one_click_check(self):
        check_for_click = self.env['do.reportbutton.click'].search(
            [('name', 'in', self.env.user.ids), ('picking_ids', 'in', self.ids)])

        if not check_for_click:
            for picking in self:
                picking.doreport_button_check = False
        else:
            for picking in self:
                for check_for_click_ in check_for_click:
                    if picking.id == check_for_click_.picking_ids.id:
                        picking.doreport_button_check = True

    @api.depends('user_id')
    def _compute_is_admin(self):
        if self.env.user.name != 'Administrator':
            for picking in self:
                picking.is_admin = False

        elif self.env.user.name == 'Administrator':
            for picking in self:
                picking.is_admin = True

    def _compute_manager_do_report_user(self):
        # msg_id = self.env['mail.message'].search([('model', '=', 'stock.picking'),
        #                                              ('res_id', '=', self.id),
        #                                              ('is_requested_open_do', '=', True),
        #                                              ('is_approved', '=', False),
        #                                              ('is_rejected', '=', False),
        #                                              ('requested_user', '!=', False)
        #                                              ], limit=1, order='id asc')

        msg_id = self.env['mail.message'].search([('model', '=', 'stock.picking'),
                                                  ('res_id', 'in', self.ids),
                                                  ('is_requested_open_do', '=', True),
                                                  ('is_approved', '=', False),
                                                  ('is_rejected', '=', False),
                                                  ('author_id.user_ids.manager_approval.user_ids.id', '=', self.env.user.id)])

        if not msg_id:
            for pick in self:
                pick.manager_do_report_user = False
        else:
            for pick in self:
                pick.manager_do_report_user = True

    @api.model
    def get_default_user(self):
        return self.env.user.id

    @api.onchange('current_user')
    def func_onchange_current_user(self):
        self.get_apj_helper_ids()

    def get_apj_helper_ids(self):
        for this in self:
            self._cr.execute("""(
                select a.id from hr_employee a
                 join res_users b on b.id = a.user_id 
                 join res_groups_users_rel c on c.uid = b.id
                 join res_groups d on d.id = c.gid 
                where d.id = 70
            )""")
            fet = [x[0] for x in self._cr.fetchall()]
            this.apj_helper_ids = [(6, 0, fet)]

    picking_type_id_name = fields.Char('picking_type_id_name', related='picking_type_id.name', store=True)
    checker = fields.Many2one('checker', string='Checker')
    picker = fields.Many2one('picker', string='Picker')
    customer_invoice = fields.Char('No. Invoice Customer')
    coli = fields.Char('Coli')
    expedition_name = fields.Char('Nama Ekspedisi')
    plat_number = fields.Char('No. Plat')
    driver_name = fields.Char('Nama Supir')
    apj = fields.Many2one('hr.employee', string='APJ')
    delivery_status = fields.Char('Delivery Order Status', tracking=True)
    apj_helper_ids = fields.Many2many('hr.employee', 'apj_hr_employee_rel', 'apj_id',
                                          'employee_id',
                                          compute=get_apj_helper_ids)
    current_user = fields.Many2one('res.users', default=get_default_user)

    # returns
    return_reason = fields.Many2one('return.reason', string='Reason')
    scheduled_date = fields.Datetime(
        'Scheduled Date', compute='_compute_scheduled_date', inverse='_set_scheduled_date', store=True,
        index=True, default=fields.Datetime.now, tracking=True,
        states={'done': [('readonly', False)], 'cancel': [('readonly', False)]},
        help="Scheduled time for the first part of the shipment to be processed. Setting manually a value here would set it as expected date for all the stock moves.")
    is_no_backorder = fields.Boolean(string='Is No Backorder')
    invoice_check = fields.Boolean(string='Inv Check', default=False)
    one_click = fields.Boolean(string='One click', compute='_compute_one_click', readonly=False)
    do_reportbutton = fields.One2many('do.reportbutton.click', 'picking_ids', string='DO Report Button Clicked Count')
    doreport_button_check = fields.Boolean(compute='_compute_one_click_check', readonly=False)
    is_admin = fields.Boolean(compute='_compute_is_admin', readonly=False)
    is_requested = fields.Boolean(compute='_compute_is_requested', readonly=False)
    manager_do_report_user = fields.Boolean(compute='_compute_manager_do_report_user', string='Manager DO Report User',
                                            readonly=False)

    access_token = fields.Char('Identification token', default=lambda self: str(uuid.uuid4()), readonly=True, required=True, copy=False)
    jumlah_koli = fields.Integer('Jumlah Koli', tracking=True)
    nomor_koli = fields.Char('Nomor Koli', tracking=True)
    kasir = fields.Many2one('hr.employee', string='Kasir')

    def button_validate(self):
        # Clean-up the context key at validation to avoid forcing the creation of immediate
        # transfers.
        ctx = dict(self.env.context)
        ctx.pop('default_immediate_transfer', None)
        self = self.with_context(ctx)

        # Sanity checks.
        pickings_without_moves = self.browse()
        pickings_without_quantities = self.browse()
        pickings_without_lots = self.browse()
        products_without_lots = self.env['product.product']
        for picking in self:
            if not picking.move_lines and not picking.move_line_ids:
                pickings_without_moves |= picking

            picking.message_subscribe([self.env.user.partner_id.id])
            picking_type = picking.picking_type_id
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            no_quantities_done = all(float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in picking.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
            no_reserved_quantities = all(float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in picking.move_line_ids)
            if no_reserved_quantities and no_quantities_done:
                pickings_without_quantities |= picking

            if picking_type.use_create_lots or picking_type.use_existing_lots:
                lines_to_check = picking.move_line_ids
                if not no_quantities_done:
                    lines_to_check = lines_to_check.filtered(lambda line: float_compare(line.qty_done, 0, precision_rounding=line.product_uom_id.rounding))
                for line in lines_to_check:
                    product = line.product_id
                    if product and product.tracking != 'none':
                        if not line.lot_name and not line.lot_id:
                            pickings_without_lots |= picking
                            products_without_lots |= product

            if picking.picking_type_id_name == 'Receipts':
                # if 'active_ids' in ctx and not picking.is_return:
                if self.purchase_id != False and not picking.is_return:
                    po = self.env['purchase.order'].browse(self.purchase_id.ids)
                    if_of_supplierinfo = []

                    if po:
                        for po_obj in po:
                            for order_line in po_obj.order_line:
                                for prd in order_line.product_id:
                                    for seller_ids in prd.seller_ids:
                                        if_of_supplierinfo.append(seller_ids.id)
                                        if seller_ids.id == po_obj.id_of_supplierinfo:
                                            seller_ids.effective_date = po_obj.effective_date

        if not self._should_show_transfers():
            if pickings_without_moves:
                raise UserError(_('Please add some items to move.'))
            if pickings_without_quantities:
                raise UserError(self._get_without_quantities_error_message())
            if pickings_without_lots:
                raise UserError(_('Kolom Batch pada product Wajib Diisi'))
        else:
            message = ""
            if pickings_without_moves:
                message += _('Transfers %s: Please add some items to move.') % ', '.join(pickings_without_moves.mapped('name'))
            if pickings_without_quantities:
                message += _('\n\nTransfers %s: You cannot validate these transfers if no quantities are reserved nor done. To force these transfers, switch in edit more and encode the done quantities.') % ', '.join(pickings_without_quantities.mapped('name'))
            if pickings_without_lots:
                message += _('\n\nTransfers %s: You need to supply a Lot/Serial number for products %s.') % (', '.join(pickings_without_lots.mapped('name')), ', '.join(products_without_lots.mapped('display_name')))
            if message:
                raise UserError(message.lstrip())

        # Run the pre-validation wizards. Processing a pre-validation wizard should work on the
        # moves and/or the context and never call `_action_done`.
        if not self.env.context.get('button_validate_picking_ids'):
            self = self.with_context(button_validate_picking_ids=self.ids)
        res = self._pre_action_done_hook()
        if res is not True:
            return res

        # Call `_action_done`.
        if self.env.context.get('picking_ids_not_to_backorder'):
            pickings_not_to_backorder = self.browse(self.env.context['picking_ids_not_to_backorder'])
            pickings_to_backorder = self - pickings_not_to_backorder
        else:
            pickings_not_to_backorder = self.env['stock.picking']
            pickings_to_backorder = self
        pickings_not_to_backorder.with_context(cancel_backorder=True)._action_done()
        pickings_to_backorder.with_context(cancel_backorder=False)._action_done()

        if self.user_has_groups('stock.group_reception_report') \
                and self.user_has_groups('stock.group_auto_reception_report') \
                and self.filtered(lambda p: p.picking_type_id.code != 'outgoing'):
            lines = self.move_lines.filtered(lambda m: m.product_id.type == 'product' and m.state != 'cancel' and m.quantity_done and not m.move_dest_ids)
            if lines:
                # don't show reception report if all already assigned/nothing to assign
                wh_location_ids = self.env['stock.location']._search([('id', 'child_of', self.picking_type_id.warehouse_id.view_location_id.ids), ('usage', '!=', 'supplier')])
                if self.env['stock.move'].search([
                        ('state', 'in', ['confirmed', 'partially_available', 'waiting', 'assigned']),
                        ('product_qty', '>', 0),
                        ('location_id', 'in', wh_location_ids),
                        ('move_orig_ids', '=', False),
                        ('picking_id', 'not in', self.ids),
                        ('product_id', 'in', lines.product_id.ids)], limit=1):
                    action = self.action_view_reception_report()
                    action['context'] = {'default_picking_ids': self.ids}
                    return action
        return True

    # def button_validate(self):
    #     res = super(DeliveryOrder, self).button_validate()
    #     ctx = dict(self.env.context or {})
    #
    #     for picking in self:
    #
    #         if picking.picking_type_id_name == 'Receipts':
    #             # if 'active_ids' in ctx and not picking.is_return:
    #             if self.purchase_id != False and not picking.is_return:
    #                 po = self.env['purchase.order'].browse(self.purchase_id.ids)
    #                 if_of_supplierinfo = []
    #
    #                 if po:
    #                     for po_obj in po:
    #                         for order_line in po_obj.order_line:
    #                             for prd in order_line.product_id:
    #                                 for seller_ids in prd.seller_ids:
    #                                     if_of_supplierinfo.append(seller_ids.id)
    #                                     if seller_ids.id == po_obj.id_of_supplierinfo:
    #                                         seller_ids.effective_date = po_obj.effective_date
    #     return res

    def on_delivery(self):
        if not self.delivery_status:
            self.delivery_status = 'On Delivery'

    def on_complete(self):
        self.delivery_status = 'Completed'
    
    def button_print_no_backorder(self):
        return self.env.ref('ati_pbf_stock.action_report_no_backorder_custom').report_action(self)

    def button_report_delivery_order(self):
        data_ = {
            'name': self.env.user.id,
            'button_clicked': True,
            'picking_ids': self.id,
        }

        self.write({'do_reportbutton': [(0, 0, data_)]})

        return self.env.ref('ati_pbf_stock.action_report_delivery_order_custom').report_action(self)

    def button_report_retur(self):
        return self.env.ref('ati_pbf_stock.action_report_tanda_terima_retur').report_action(self)

    def button_report_return_picking(self):
        return self.env.ref('ati_pbf_stock.action_report_picking_pbf').report_action(self)

    def request_approval_for_print_do(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        self.ensure_one()
        template_id = self.env['mail.template'].search([('name', '=', 'Stock Picking: Request to Delivery Order Report')])

        base_url = request.env['ir.config_parameter'].get_param('web.base.url')
        base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)

        url_approve = request.env['ir.config_parameter'].get_param('web.base.url')
        url_approve += '/web/approve?token=%s&db=%s&user_id=%s&id=%s&view_id=%s&requestor=%s&manager=%s&do_number=%s&requestor_email=%s&manager_email=%s&requestor_id=%s&user=%s' % (self.access_token,
                            self._cr.dbname,
                            self.env.user.id,
                            self.id,
                            self.env.ref('stock.view_picking_form').id,
                            self.env.user.name,
                            self.env.user.manager_approval.name or '',
                            self.name,
                            self.env.user.partner_id.email,
                            self.env.user.manager_approval.email or '',
                            self.env.user.partner_id.id,
                            self.env.user.manager_approval.user_ids.id)

        url_reject = request.env['ir.config_parameter'].get_param('web.base.url')
        url_reject += '/web/reject?token=%s' \
                      '&db=%s' \
                      '&user_id=%s' \
                      '&id=%s' \
                      '&view_id=%s' \
                      '&requestor=%s' \
                      '&manager=%s' \
                      '&do_number=%s' \
                      '&requestor_email=%s' \
                      '&manager_email=%s&user=%s' % (
                            self.access_token,
                            self._cr.dbname,
                            self.env.user.id,
                            self.id,
                            self.env.ref('stock.view_picking_form').id,
                            self.env.user.name,
                            self.env.user.manager_approval.name or '',
                            self.name,
                            self.env.user.partner_id.email,
                            self.env.user.manager_approval.email or '',
                            self.env.user.manager_approval.user_ids.id)

        body_html = f'''Dear {request.env.user.manager_approval.name or ''},<br><br>
                        {request.env.user.name} request to open DO Report Button on
                        <a href={base_url}>{self.name}</a><br><br>
                        <a href={url_approve} style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;">Approve</a> <a href={url_reject} style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;"> Reject</a><br><br>
                        Thank you,<br>
                        {request.env.user.signature}'''
        template_id.body_html = body_html



        ctx = {
            'default_model': 'stock.picking',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id.id,
            'default_partner_ids': self.env.user.manager_approval.ids,
            'default_composition_mode': 'comment',
            'default_is_requested_open_do': True,
            'mark_so_as_sent': True,
            'force_email': True,
        }

        if not self.env.user.manager_approval:
            raise UserError(_('Anda harus mengisi manager approval di Menu User'))
        else:
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(False, 'form')],
                'view_id': False,
                'target': 'new',
                'context': ctx,
            }

    def open_the_list_of_request_do_report(self):
        msg_id = self.env['mail.message'].search([('model', '=', 'stock.picking'),
                                                  ('res_id', '=', self.id),
                                                  ('is_requested_open_do', '=', True),
                                                  ('is_approved', '=', False),
                                                  ('is_rejected', '=', False)],
                                                 order='id asc')

        view_id = self.env.ref('ati_pbf_stock.view_do_reportbutton_request_form').id

        return {
            'name': _('DO Report Request List'),
            'res_model': 'do.reportbutton.req',
            'view_mode': 'form',
            'view_id': view_id,
            'domain': False,
            'context': {
                'edit': False,
                'create': False,
                'active_id': self.id
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    @api.constrains('move_line_ids_without_package', 'move_ids_without_package')
    def _ati_check_demand_qty(self):
        for res in self:
            if res.picking_type_id.code in ('incoming', 'outgoing'):
                for operation in res.move_ids_without_package:
                    for move_line in operation.move_line_ids:
                        if operation.product_uom_qty < move_line.qty_done:
                            raise ValidationError(_('Quantity done tidak boleh lebih dari Demand.'))
                        if operation.product_uom_qty < operation.quantity_done:
                            raise ValidationError(_('Quantity done tidak boleh lebih dari Demand.'))
                        if operation.product_uom_qty < operation.quantity_done:
                            raise ValidationError(_('Quantity done tidak boleh lebih dari Demand.'))
                        # if move_line.product_uom_qty < move_line.qty_done:
                        #     raise ValidationError(_('Quantity done tidak boleh lebih dari Demand.'))

class ResUsers(models.Model):
    _inherit = 'res.users'
    _description = 'Users'

    manager_approval = fields.Many2one('res.partner', string='Manager Approval')

class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'
    _description = 'Mail Composer'

    @api.depends('template_id')
    def _compute_mail_template_name(self):
        self.mail_template_name = self.template_id.name

    mail_template_name = fields.Char(string='Mail template name', compute='_compute_mail_template_name', readonly=False)

class OpenReportDo(models.TransientModel):
    _name = 'open.report.do'
    _description = 'Open Report DO'

class stock_move(models.Model):
    _inherit = 'stock.move'

    # def _action_done(self, cancel_backorder=False):
    #     res = super(stock_move, self)._action_done(cancel_backorder=cancel_backorder)
    #
    #
    #     valued_moves = {valued_type: self.env['stock.move'] for valued_type in self._get_valued_types()}
    #     for this in self:
    #         stock_valuation_layers = self.env['stock.valuation.layer'].sudo()
    #         if this.sale_line_id.id != False:
    #             valued_moves['out'] = self.env['stock.move'].search([('sale_line_id', '=', this.sale_line_id.id)])
    #             todo_valued_moves = valued_moves['out']
    #             if todo_valued_moves:
    #                 # todo_valued_moves._sanity_check_for_valuation()
    #
    #                 stock_valuation_layers |= getattr(todo_valued_moves, '_create_%s_svl' % 'out')()
    #                 stock_valuation_layers._validate_accounting_entries()
    #                 stock_valuation_layers._validate_analytic_accounting_entries()
    #
    #                 stock_valuation_layers._check_company()
    #     return res

    def _create_out_svl(self, forced_quantity=None):
        """Create a `stock.valuation.layer` from `self`.

        :param forced_quantity: under some circunstances, the quantity to value is different than
            the initial demand of the move (Default value = None)
        """
        svl_vals_list = []
        for move in self:
            move = move.with_company(move.company_id)
            valued_move_lines = move._get_out_move_lines()
            if not valued_move_lines:
                valued_move_lines = self.env['stock.move.line'].sudo().search([('move_id','=',move.id)])
            valued_quantity = 0
            for valued_move_line in valued_move_lines:
                valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done,move.product_id.uom_id)
            if float_is_zero(forced_quantity or valued_quantity,precision_rounding=move.product_id.uom_id.rounding):
                continue
            svl_vals = move.product_id._prepare_out_svl_vals(forced_quantity or valued_quantity, move.company_id)
            svl_vals.update(move._prepare_common_svl_vals())
            if forced_quantity:
                svl_vals[
                    'description'] = 'Correction of %s (modification of past move)' % move.picking_id.name or move.name
            svl_vals['description'] += svl_vals.pop('rounding_adjustment', '')
            svl_vals_list.append(svl_vals)
        return self.env['stock.valuation.layer'].sudo().create(svl_vals_list)

