from odoo import models, fields, _, api
from datetime import date, datetime, timedelta
import json

class AccountMove(models.Model):
    _inherit = 'account.move'
    _description = 'Account Move'

    def func_update_display_name_am(self):
        self._cr.execute("""(
            select 
                a.id 
            from account_move a 
            join res_partner b on b.id = a.partner_id 
            where b.display_name = ''
        )""")
        check_am = self.env['account.move'].sudo().browse([x[0] for x in self._cr.fetchall()])
        for x in check_am:
            x.partner_id.name_get()
        return True

    def func_update_invoice_date(self):
        update_data = "update account_move set invoice_date = create_date " \
                      "where move_type = 'out_invoice' and invoice_date is null"
        self._cr.execute(update_data)
        self._cr.commit()
        return True

    def func_update_partner_id(self):
        update_data = "update account_move t set partner_id = (" \
                      "select z.partner_id from account_move w " \
                      "join account_move_line v on v.move_id = w.id " \
                      "join sale_order_line_invoice_rel x on x.invoice_line_id = v.id " \
                      "join sale_order_line y on y.id = x.order_line_id " \
                      "join sale_order z on z.id = y.order_id " \
                      "where w.partner_id <> z.partner_id and w.id = t.id group by z.partner_id) " \
                      "where t.id in (" \
                      "select a.id " \
                      "from account_move a " \
                      "join account_move_line b on b.move_id =a.id " \
                      "join sale_order_line_invoice_rel c on c.invoice_line_id = b.id " \
                      "join sale_order_line d on d.id = c.order_line_id " \
                      "join sale_order e on e.id = d.order_id " \
                      "where a.partner_id <> e.partner_id group by a.id)"
        self._cr.execute(update_data)
        self._cr.commit()
        return True

    @api.depends('invoice_origin')
    def _compute_source_document(self):
        for move in self:
            move.source_document = move.invoice_origin

    def _compute_invoice_address(self):
        for this in self:
            check_data = self.env['res.partner'].sudo().search([('parent_id','=',this.partner_id.id),('type','=','invoice')], limit=1)
            this.invoice_address_id = check_data.id if check_data else None

    source_document = fields.Char(string='Source Document', compute='_compute_source_document', store=True)
    invoice_address_id = fields.Many2one('res.partner', string='Invoice Address', compute=_compute_invoice_address)

    reset_access = fields.Boolean('Reset Access', compute='_compute_reset_access', default=False, readonly=False)
    # state = fields.Selection(selection=[
    #     ('draft', 'Draft'),
    #     ('waiting_approval', 'Waiting Approval'),
    #     ('posted', 'Posted'),
    #     ('cancel', 'Cancelled'),
    # ], string='Status', required=True, readonly=True, copy=False, tracking=True,
    #     default='draft')

    tukar_faktur = fields.Boolean(string='Tukar Faktur', default=False)
    purchase_person = fields.Many2one('hr.employee', string='Purchase Person')
    sales_person = fields.Many2one('hr.employee', string='Sales Person')

    def _compute_reset_access(self):
        if self.user_has_groups('ati_pbf_account.account_move_reset_button_access_right'):
            self.reset_access = True
        elif not self.user_has_groups('ati_pbf_account.account_move_reset_button_access_right'):
            self.reset_access = False

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for move in self:
            if move.move_type == 'out_invoice' and move.is_from_so != False:
                tax_totals_json = json.loads(move.tax_totals_json)
                if 'amount_total' in tax_totals_json:
                    move.amount_residual = tax_totals_json['amount_total']
                    for tax in tax_totals_json['groups_by_subtotal']['Untaxed Amount']:
                        move.amount_tax = tax['tax_group_amount']
                    tax_name = []
                    if move.is_from_so != False:
                        so_obj = self.env['sale.order'].search([('name', '=', move.sales_reference)])
                        if so_obj:
                            for so_obj_ in so_obj:
                                for so_line in so_obj_.order_line:
                                    for tax_line in so_line.tax_id:
                                        if tax_line.name not in tax_name:
                                            tax_name.append(tax_line.name)

                    for mvl in move.line_ids:
                        if mvl.name == move.name:
                            mvl.price_unit = -1 * tax_totals_json['amount_total']
                        if mvl.name in tax_name:
                            for tax in tax_totals_json['groups_by_subtotal']['Untaxed Amount']:
                                mvl.price_unit = tax['tax_group_amount']
            if move.move_type == 'in_invoice':
                move.payment_state = 'not_paid'
            if move.move_type == 'in_refund':
                # print('111',move.tax_totals_json)
                move.payment_state = 'not_paid'
                tax_totals_json = json.loads(move.tax_totals_json)
                amount_tax = -1 * move.amount_tax
                move.amount_residual = move.amount_untaxed + amount_tax
            # if move.move_type == 'out_invoice' and move.is_from_so == False:
            #     for mvl in move.line_ids:
            #         print(mvl.price_unit,mvl.name, mvl.tax_base_amount)
                # move.amount_residual = tax_totals_json['amount_total']

            # elif move.move_type == 'in_invoice':
            #     tax_totals_json = json.loads(move.tax_totals_json)
            #     if 'amount_total' in tax_totals_json:
            #         aml = self.env['account.move.line'].search(
            #             [('move_id', '=', move.id), ('exclude_from_invoice_tab', '=', True), ('price_unit', '=', -1 * move.amount_total)])
            #         if aml:
            #             for aml_ in aml:
            #                 aml_.price_unit = -1 * tax_totals_json['amount_total']
            #
            #         aml = self.env['account.move.line'].search(
            #             [('move_id', '=', move.id),
            #              ('price_unit', '=', move.amount_tax)])
            #         if aml:
            #             for aml_ in aml:
            #                 for tax in tax_totals_json['groups_by_subtotal']['Untaxed Amount']:
            #                     aml_.price_unit = tax['tax_group_amount']
            #
            #         move.amount_residual = tax_totals_json['amount_total']
            #         for tax in tax_totals_json['groups_by_subtotal']['Untaxed Amount']:
            #             move.amount_tax = tax['tax_group_amount']
            #             move.amount_total = (move.amount_untaxed + tax['tax_group_amount']) - move.total_discount if move.total_discount else 0
            #             move.amount_tax_signed = -1 * move.amount_tax
            #             move.amount_total_signed = -1 * move.amount_total
            #             move.amount_total_in_currency_signed = -1 * move.amount_total
            #             move.amount_residual_signed = -1 * move.amount_total

    # def approve_cn(self):
    #     if self.move_type == 'out_refund' or self.move_type == 'in_refund':
    #         self.state = 'posted'

    def get_six_digit_vbill(self):
        six_digit = 'draft'
        if self.name and  self.state == 'posted':
            if len(self.name) > 13 and len(self.name[13:]) == 4:
                six_digit = f'00{self.name[13:]}'
            elif len(self.name) > 13 and len(self.name[13:]) == 5:
                six_digit = f'0{self.name[13:]}'
            else:
                six_digit = f'{self.name[13:]}'
        return six_digit

    def button_print_tanda_terima_barang(self):
        return self.env.ref('ati_pbf_account.action_report_vendor_bill_ttb_custom').report_action(self)

    @api.model
    def _prepare_tax_lines_data_for_totals_from_object(self, object_lines, tax_results_function):
        """ Prepares data to be passed as tax_lines_data parameter of _get_tax_totals() from any
			object using taxes. This helper is intended for purchase.order and sale.order, as a common
			function centralizing their behavior.

			:param object_lines: A list of records corresponding to the sub-objects generating the tax totals
								 (sale.order.line or purchase.order.line, for example)

			:param tax_results_function: A function to be called to get the results of the tax computation for a
										 line in object_lines. It takes the object line as its only parameter
										 and returns a dict in the same format as account.tax's compute_all
										 (most probably after calling it with the right parameters).

			:return: A list of dict in the format described in _get_tax_totals's tax_lines_data's docstring.
		"""
        tax_lines_data = []

        for line in object_lines:
            tax_results = tax_results_function(line)
            for tax_result in tax_results['taxes']:
                current_tax = self.env['account.tax'].browse(tax_result['id'])

                # Tax line
                tax_lines_data.append({
                    'line_key': f"tax_line_{line.id}_{tax_result['id']}",
                    'tax_amount': tax_result['amount'],
                    'tax': current_tax,
                })

                # Base for this tax line
                tax_lines_data.append({
                    'line_key': 'base_line_%s' % line.id,
                    'base_amount': tax_results['total_excluded'],
                    'tax': current_tax,
                })

                # Base for the taxes whose base is affected by this tax line
                if tax_result['tax_ids']:
                    affected_taxes = self.env['account.tax'].browse(tax_result['tax_ids'])
                    for affected_tax in affected_taxes:
                        tax_lines_data.append({
                            'line_key': 'affecting_base_line_%s_%s' % (line.id, tax_result['id']),
                            'base_amount': tax_result['amount'],
                            'tax': affected_tax,
                            'tax_affecting_base': current_tax,
                        })


            if not tax_results['taxes']:
                current_tax = self.env['account.tax'].browse()

                # Tax line
                tax_lines_data.append({
                    'line_key': f"tax_line_{line.id}_0",
                    'tax_amount': 0,  # tax_result['amount'],
                    'tax': current_tax,
                })

                # Base for this tax line
                tax_lines_data.append({
                    'line_key': 'base_line_%s' % line.id,
                    'base_amount': tax_results['total_excluded'],
                    'tax': current_tax,
                })

                # Base for the taxes whose base is affected by this tax line
                # if tax_result['tax_ids']:
                affected_taxes = self.env['account.tax'].browse()
                for affected_tax in affected_taxes:
                    tax_lines_data.append({
                        'line_key': 'affecting_base_line_%s_%s' % (line.id, 0),
                        'base_amount': 0,  # tax_result['amount'],
                        'tax': affected_tax,
                        'tax_affecting_base': current_tax,
                    })

        return tax_lines_data
    
    
    def _post(self, soft=True):
        res = super(AccountMove, self)._post(soft=True)

        picking_id = []

        for inv in self:
            for inv_line in inv.invoice_line_ids:
                for so_line in inv_line.sale_line_ids:
                    for sale in so_line.order_id:
                        if sale.picking_ids:
                            for picking in sale.picking_ids:
                                picking_obj = self.env['stock.picking'].search([('id', '=', picking.id), ('state', 'in', ['done']), ('invoice_check', '=', False)])
                                for picking_obj_ in picking_obj:
                                    if picking_obj_.id not in picking_id:
                                        picking_id.append(picking_obj_.id)

                                    # search stock.picking for inv date based on effective date on each picking
                                    search_picking = self.env['stock.picking'].search([('id', '=', min(picking_id))])
                                    if search_picking:
                                        for picking_1 in search_picking:
                                            if picking_1.picking_type_id.name == 'Delivery Orders':
                                                if picking_1.date_done:
                                                    if inv.move_type == 'out_invoice':
                                                        effective_date = picking_1.date_done + timedelta(hours=7)
                                                        inv.invoice_date = effective_date.date()
                                                        picking_1.write({'invoice_check': True})
                                                        picking_id.clear()

        return res

    def _recompute_tax_lines(self, recompute_tax_base_amount=False, tax_rep_lines_to_recompute=None):
        ''' Compute the dynamic tax lines of the journal entry.

        :param lines_map: The line_ids dispatched by type containing:
            * base_lines: The lines having a tax_ids set.
            * tax_lines: The lines having a tax_line_id set.
            * terms_lines: The lines generated by the payment terms of the invoice.
            * rounding_lines: The cash rounding lines of the invoice.
        '''
        self.ensure_one()
        in_draft_mode = self != self._origin

        def _serialize_tax_grouping_key(grouping_dict):
            ''' Serialize the dictionary values to be used in the taxes_map.
            :param grouping_dict: The values returned by '_get_tax_grouping_key_from_tax_line' or '_get_tax_grouping_key_from_base_line'.
            :return: A string representing the values.
            '''
            return '-'.join(str(v) for v in grouping_dict.values())

        def _compute_base_line_taxes(base_line):
            ''' Compute taxes amounts both in company currency / foreign currency as the ratio between
            amount_currency & balance could not be the same as the expected currency rate.
            The 'amount_currency' value will be set on compute_all(...)['taxes'] in multi-currency.
            :param base_line:   The account.move.line owning the taxes.
            :return:            The result of the compute_all method.
            '''
            move = base_line.move_id

            if move.is_invoice(include_receipts=True):
                handle_price_include = True
                sign = -1 if move.is_inbound() else 1
                quantity = base_line.quantity
                is_refund = move.move_type in ('out_refund', 'in_refund')

                price_unit_wo_discount = base_line.ati_price_unit

                total_discount_1 = price_unit_wo_discount * base_line.discount_1 / 100.0 if base_line.discount_1 else 0.0
                price_unit_wo_discount = price_unit_wo_discount - total_discount_1

                total_discount_2 = price_unit_wo_discount * base_line.discount_2 / 100.0 if base_line.discount_2 else 0.0
                price_unit_wo_discount = price_unit_wo_discount - total_discount_2

                total_discount_3 = base_line.discount_3 if base_line.discount_3 else 0.0
                price_unit_wo_discount = price_unit_wo_discount - total_discount_3

                total_discount_4 = base_line.discount_4 if base_line.discount_4 else 0.0
                price_unit_wo_discount = price_unit_wo_discount - total_discount_4

                if base_line.discount_type and base_line.discount_type == 'fixed':
                    price_unit_wo_discount = sign * (
                                price_unit_wo_discount - (base_line.discount / (base_line.quantity or 1.0)))
                else:
                    price_unit_wo_discount = sign * price_unit_wo_discount * (1 - (base_line.discount / 100.0))

                ''' #Putra Penambahan Discount 1, 2, 3, 4 untuk perhitungan tax '''
                # if move.move_type == 'in_invoice':
                #     discount_1 = sign * base_line.price_unit * (base_line.discount_1 / 100.0) if base_line.discount_1 else 0.0
                #     discount_2 = sign * base_line.price_unit * (base_line.discount_2 / 100.0) if base_line.discount_2 else 0.0
                #     discount_3 = sign * (base_line.discount_3 / (base_line.quantity or 1.0)) if base_line.discount_3 else 0.0
                #     discount_4 = sign * (base_line.discount_4 / (base_line.quantity or 1.0)) if base_line.discount_4 else 0.0
                #     price_unit_wo_discount = price_unit_wo_discount - discount_1 - discount_2 - discount_3 - discount_4

            else:
                handle_price_include = False
                quantity = 1.0
                tax_type = base_line.tax_ids[0].type_tax_use if base_line.tax_ids else None
                is_refund = (tax_type == 'sale' and base_line.debit) or (tax_type == 'purchase' and base_line.credit)
                price_unit_wo_discount = base_line.amount_currency

            return base_line.tax_ids._origin.with_context(force_sign=move._get_tax_force_sign()).compute_all(
                price_unit_wo_discount,
                currency=base_line.currency_id,
                quantity=quantity,
                product=base_line.product_id,
                partner=base_line.partner_id,
                is_refund=is_refund,
                handle_price_include=handle_price_include,
                include_caba_tags=move.always_tax_exigible,
            )

        taxes_map = {}

        # ==== Add tax lines ====
        to_remove = self.env['account.move.line']
        for line in self.line_ids.filtered('tax_repartition_line_id'):
            grouping_dict = self._get_tax_grouping_key_from_tax_line(line)
            grouping_key = _serialize_tax_grouping_key(grouping_dict)
            if grouping_key in taxes_map:
                # A line with the same key does already exist, we only need one
                # to modify it; we have to drop this one.
                to_remove += line
            else:
                taxes_map[grouping_key] = {
                    'tax_line': line,
                    'amount': 0.0,
                    'tax_base_amount': 0.0,
                    'grouping_dict': False,
                }
        if not recompute_tax_base_amount:
            self.line_ids -= to_remove

        # ==== Mount base lines ====
        for line in self.line_ids.filtered(lambda line: not line.tax_repartition_line_id):
            # Don't call compute_all if there is no tax.
            if not line.tax_ids:
                if not recompute_tax_base_amount:
                    line.tax_tag_ids = [(5, 0, 0)]
                continue

            compute_all_vals = _compute_base_line_taxes(line)

            # Assign tags on base line
            if not recompute_tax_base_amount:
                line.tax_tag_ids = compute_all_vals['base_tags'] or [(5, 0, 0)]

            for tax_vals in compute_all_vals['taxes']:
                grouping_dict = self._get_tax_grouping_key_from_base_line(line, tax_vals)
                grouping_key = _serialize_tax_grouping_key(grouping_dict)

                tax_repartition_line = self.env['account.tax.repartition.line'].browse(
                    tax_vals['tax_repartition_line_id'])
                tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id

                taxes_map_entry = taxes_map.setdefault(grouping_key, {
                    'tax_line': None,
                    'amount': 0.0,
                    'tax_base_amount': 0.0,
                    'grouping_dict': False,
                })
                taxes_map_entry['amount'] += tax_vals['amount']
                taxes_map_entry['tax_base_amount'] += self._get_base_amount_to_display(tax_vals['base'],
                                                                                       tax_repartition_line,
                                                                                       tax_vals['group'])
                taxes_map_entry['grouping_dict'] = grouping_dict

        # ==== Pre-process taxes_map ====
        taxes_map = self._preprocess_taxes_map(taxes_map)

        # ==== Process taxes_map ====
        for taxes_map_entry in taxes_map.values():
            # The tax line is no longer used in any base lines, drop it.
            if taxes_map_entry['tax_line'] and not taxes_map_entry['grouping_dict']:
                if not recompute_tax_base_amount:
                    self.line_ids -= taxes_map_entry['tax_line']
                continue

            currency = self.env['res.currency'].browse(taxes_map_entry['grouping_dict']['currency_id'])

            # Don't create tax lines with zero balance.
            if currency.is_zero(taxes_map_entry['amount']):
                if taxes_map_entry['tax_line'] and not recompute_tax_base_amount:
                    self.line_ids -= taxes_map_entry['tax_line']
                continue

            # tax_base_amount field is expressed using the company currency.
            tax_base_amount = currency._convert(taxes_map_entry['tax_base_amount'], self.company_currency_id,
                                                self.company_id, self.date or fields.Date.context_today(self))

            # Recompute only the tax_base_amount.
            if recompute_tax_base_amount:
                if taxes_map_entry['tax_line']:
                    taxes_map_entry['tax_line'].tax_base_amount = tax_base_amount
                continue

            for inv_line in self.line_ids:
                for so_line in inv_line.sale_line_ids:
                    taxes_map_entry['amount'] = -1 * so_line.price_tax

            balance = currency._convert(
                taxes_map_entry['amount'],
                self.company_currency_id,
                self.company_id,
                self.date or fields.Date.context_today(self),
            )
            to_write_on_line = {
                'amount_currency': taxes_map_entry['amount'],
                'currency_id': taxes_map_entry['grouping_dict']['currency_id'],
                'debit': balance > 0.0 and balance or 0.0,
                'credit': balance < 0.0 and -balance or 0.0,
                'tax_base_amount': tax_base_amount,
            }

            if taxes_map_entry['tax_line']:
                # Update an existing tax line.
                taxes_map_entry['tax_line'].update(to_write_on_line)
            else:
                create_method = in_draft_mode and self.env['account.move.line'].new or self.env[
                    'account.move.line'].create
                tax_repartition_line_id = taxes_map_entry['grouping_dict']['tax_repartition_line_id']
                tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_repartition_line_id)
                tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id
                taxes_map_entry['tax_line'] = create_method({
                    **to_write_on_line,
                    'name': tax.name,
                    'move_id': self.id,
                    'partner_id': line.partner_id.id,
                    'company_id': line.company_id.id,
                    'company_currency_id': line.company_currency_id.id,
                    'tax_base_amount': tax_base_amount,
                    'exclude_from_invoice_tab': True,
                    **taxes_map_entry['grouping_dict'],
                })

            if in_draft_mode:
                taxes_map_entry['tax_line'].update(
                    taxes_map_entry['tax_line']._get_fields_onchange_balance(force_computation=True))


class account_move_reversal(models.TransientModel):
    _inherit = 'account.move.reversal'


    def reverse_moves(self):
        res = super(account_move_reversal, self).reverse_moves()
        for move in self.new_move_ids:
            context = self._context.copy()
            # self._cr.execute("""(
            #                     select a.id, a.product_id, a.quantity,
            #                     b.stock_move_id
            #                     from account_move_line a
            #                     join account_move b on b.id = a.move_id
            #                     where a.move_id = {_move} and a.product_id is not null
            #                 )""".format(_move=move.id))
            # chek_data = self._cr.dictfetchall()
            # self._cr.execute("""(
            #     select d.product_id, d.qty_done from account_move_line a
            #     join account_move b on b.id = a.move_id
            #     join stock_move c on c.id = b.stock_move_id
            #     join stock_move_line d on d.move_id = c.id
            #     where a.move_id = {_move} and d.product_id is not null and d.qty_done <> 0
            # )""".format(_move=move.id))
            # chek_data = self._cr.dictfetchall()
            stock_move_line = context.get('stock_move_line', [])
            for k in stock_move_line:
                self._cr.execute("""(select id from account_move_line
                where move_id = {_move} and product_id = {_prod}
                )""".format(_move=move.id,_prod=k['product_id']))
                fet = [x[0] for x in self._cr.fetchall()]
                if k['quantity'] != 0:
                    update_data = "update account_move_line set quantity = {_qty} " \
                                  "where move_id = {_move} and product_id = {_prod}".format(_qty=k['quantity'],
                                                                                            _move=move.id,
                                                                                            _prod=k['product_id'])
                    self._cr.execute(update_data)
                    self._cr.commit()
            delete_data = "delete from account_move_line where move_id = {_move_id} and exclude_from_invoice_tab = false and product_id is not null and quantity = 0".format(_move_id=move.id)
            self._cr.execute(delete_data)
            self._cr.commit()
            delete_data = "delete from account_move_line where move_id = {_move_id} and exclude_from_invoice_tab = false and price_subtotal = 0".format(
                _move_id=move.id)
            self._cr.execute(delete_data)
            self._cr.commit()

            self._cr.execute("""(select a.id from account_move_line a
                                join purchase_order_line b on a.purchase_line_id = b.id 
                                where a.move_id = {_move} and a.exclude_from_invoice_tab = false
                                and b.price_subtotal = 0
                            )""".format(_move=move.id, _prod=k['product_id']))
            fet_data = [x[0] for x in self._cr.fetchall()]
            for data in fet_data:
                delete_data = "delete from account_move_line where id = {_id} and exclude_from_invoice_tab = false".format(
                    _id=data)
                self._cr.execute(delete_data)
                self._cr.commit()

            for i in move.invoice_line_ids:
                if move.move_type != 'out_refund':
                    i.price_subtotal = i.quantity * i.ati_price_unit
                else:
                    i.price_subtotal = i.quantity * i.harga_satuan
            picking = self.env['stock.picking'].sudo().search([('id', '=', context.get('active_id')), ('date_done', '!=', False)],order='id desc',limit=1)
            if picking.date_done:
                update_data = "update account_move set invoice_date = '{_effective_date}', date = '{_effective_date}' " \
                              "where id = {_id}".format(_effective_date=picking.date_done,
                                                                                     _id=move.id)
                self._cr.execute(update_data)
                self._cr.commit()
        return res

class inherit_account_account(models.Model):
    _inherit = 'account.account'
    _description = 'Account Account'

    cashflow_report = fields.Boolean(string='Cashflow Report', default=True, store=True)