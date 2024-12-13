from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang, format_date, get_lang
import json


class AccountMove(models.Model):
    _inherit = 'account.move'

    source_document_id = fields.Many2one(string='Source Document Id', comodel_name='stock.picking', readonly=True)
    sales_reference = fields.Char(string='Sales Reference', readonly=True)
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('approval', 'Approval'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
    ], string='Status', required=True, readonly=True, copy=False, tracking=True,
    default='draft')
    reason_return_id = fields.Many2one(string='Reason', comodel_name='return.reason', readonly=True)
    is_from_so = fields.Boolean(string='Is From SO', default=False, copy=False)
    is_from_po = fields.Boolean(string='Is From PO', default=False, copy=False)

    def _check_balanced(self):
        ''' Assert the move is fully balanced debit = credit.
        An error is raised if it's not the case.
        '''
        moves = self.filtered(lambda move: move.line_ids)
        if not moves:
            return

        # /!\ As this method is called in create / write, we can't make the assumption the computed stored fields
        # are already done. Then, this query MUST NOT depend of computed stored fields (e.g. balance).
        # It happens as the ORM makes the create with the 'no_recompute' statement.
        self.env['account.move.line'].flush(self.env['account.move.line']._fields)
        self.env['account.move'].flush(['journal_id'])
        self._cr.execute('''
            SELECT line.move_id, ROUND(SUM(line.debit - line.credit), currency.decimal_places)
            FROM account_move_line line
            JOIN account_move move ON move.id = line.move_id
            JOIN account_journal journal ON journal.id = move.journal_id
            JOIN res_company company ON company.id = journal.company_id
            JOIN res_currency currency ON currency.id = company.currency_id
            WHERE line.move_id IN %s
            GROUP BY line.move_id, currency.decimal_places
            HAVING ROUND(SUM(line.debit - line.credit), currency.decimal_places) != 0.0;
        ''', [tuple(self.ids)])

        query_res = self._cr.fetchall()
        if query_res:
            ids = [res[0] for res in query_res]
            sums = [res[1] for res in query_res]
            return
            # raise UserError(
            #     _("Cannot create unbalanced journal entry. Ids: %s\nDifferences debit - credit: %s") % (ids, sums))

    def copy_data(self, default=None):
        res = super(AccountMove, self).copy_data(default=default)
        stock_move_line = self._context.get('stock_move_line', [])
        # # added by ibad
        if self.move_type != 'out_invoice':
            index_of_sml = -1
            index_of_sml1 = -1
            del_indices = []
            end_del_indices = []
            line_ids_length = []
            count_len_of_line_ids = 0
            line_ids_begin_len = len(res[0]['line_ids'])

            for line_ids_len in res[0]['line_ids']:
                count_len_of_line_ids += 1
                line_ids_length.append(count_len_of_line_ids)
            for aml_ in res[0]['line_ids']:
                index_of_sml += 1
                if aml_[2]['product_id'] == stock_move_line[0]['product_id']:
                    break
            for i in range(0, index_of_sml):
                del_indices.append(i)

            givenIndices = del_indices
            indicesList = sorted(givenIndices, reverse=True)

            for indx in indicesList:
                if indx < len(res[0]['line_ids']):
                    res[0]['line_ids'].pop(indx)
            for aml_1 in res[0]['line_ids']:
                index_of_sml1 += 1
                if aml_1[2]['product_id'] == stock_move_line[0]['product_id']:
                    continue
            for j in range(index_of_sml1 + 1, len(res[0]['line_ids'])):
                end_del_indices.append(j)

            endIndices = end_del_indices
            endIndicesList = sorted(endIndices, reverse=True)

            for end_indx in endIndicesList:
                if end_indx < len(res[0]['line_ids']):
                    res[0]['line_ids'].pop(end_indx)


        if self._context.get('return', False) and self.move_type == 'out_invoice':
            data = {}
            debit = 0
            total_debit = 0
            total_credit = 0
            total_untax_amount = 0
            res[0]['global_order_discount'] = 0.0
            if stock_move_line:

                for sml in stock_move_line:
                    data[sml['product_id']] = {}
                    data[sml['product_id']]['quantity'] = sml['quantity']
                i = 0
                for aml in res[0]['line_ids']:
                    if aml[2].get('is_global_line', False):
                        res[0]['line_ids'].pop(i)
                    i += 1

                
                for aml in res[0]['line_ids']:
                    if not aml[2].get('exclude_from_invoice_tab', True):
                        # aml[2]['discount'] = 0.0
                        aml[2]['discount_1'] = 0.0
                        aml[2]['discount_2'] = 0.0
                        aml[2]['discount_3'] = 0.0
                        aml[2]['discount_4'] = 0.0
                        if aml[2]['product_id'] in data:
                            aml[2]['quantity'] = data[aml[2]['product_id']]['quantity']
                        else:
                            aml[2]['quantity'] =  0
                        # aml[2]['quantity'] = data[aml[2]['product_id']]['quantity']
                        aml[2]['price_unit'] = aml[2]['harga_satuan']
                        debit = aml[2]['quantity'] * aml[2]['price_unit']
                        aml[2]['debit'] = -debit if debit < 0 else 0.0
                        aml[2]['credit'] = debit if debit > 0 else 0.0
                        aml[2]['amount_currency'] = debit
                        aml[2]['price_subtotal'] = debit
                        aml[2]['price_total'] = debit
                        currency_id = self.env['res.currency'].sudo().browse(aml[2]['currency_id'])
                        untax_amount = self.env['account.tax'].sudo().browse(aml[2]['tax_ids'][0][2]).compute_all(debit, currency_id)
                        total_untax_amount += untax_amount['total_included'] - untax_amount['total_excluded']
                        total_debit -= debit
                        total_credit += debit

                for aml in res[0]['line_ids']:
                    if aml[2].get('exclude_from_invoice_tab', False) and aml[2].get('tax_repartition_line_id', False):
                        aml[2]['tax_base_amount'] = total_credit
                        aml[2]['price_unit'] = total_untax_amount
                        debit = aml[2]['price_unit']
                        aml[2]['debit'] = -debit if debit < 0 else 0.0
                        aml[2]['credit'] = debit if debit > 0 else 0.0
                        aml[2]['amount_currency'] = debit
                        aml[2]['price_subtotal'] = debit
                        aml[2]['price_total'] = debit
                        total_debit -= debit

                for aml in res[0]['line_ids']:
                    if aml[2].get('exclude_from_invoice_tab', False) and not aml[2].get('tax_repartition_line_id', True):
                        disc_account_id = int(self.env['ir.config_parameter'].sudo().search([('key', '=', 'discount_account_invoive.discount_item_account')]).value) or None
                        if aml[2]['account_id'] == disc_account_id:
                            total_debit = 0
                        aml[2]['price_unit'] = total_debit
                        debit = aml[2]['price_unit']
                        aml[2]['debit'] = -debit if debit < 0 else 0.0
                        aml[2]['credit'] = debit if debit > 0 else 0.0
                        aml[2]['amount_currency'] = debit
                        aml[2]['price_subtotal'] = debit
                        aml[2]['price_total'] = debit
        elif self._context.get('return', False) and self.move_type == 'in_invoice':
            stock_move_line = self._context.get('stock_move_line', [])
            data = {}
            debit = 0
            total_debit = 0
            total_credit = 0
            total_untax_amount = 0
            total_discount = 0
            res[0]['global_order_discount'] = 0.0
            if stock_move_line:

                for sml in stock_move_line:
                    data[sml['product_id']] = {}
                    data[sml['product_id']]['quantity'] = sml['quantity']
                i = 0
                for aml in res[0]['line_ids']:
                    if aml[2].get('is_global_line', False):
                        res[0]['line_ids'].pop(i)
                    i += 1

                
                for aml in res[0]['line_ids']:
                    if not aml[2].get('exclude_from_invoice_tab', True):
                        aml[2]['discount'] = 0.0
                        # aml[2]['discount_1'] = 0.0
                        # aml[2]['discount_2'] = 0.0
                        # aml[2]['discount_3'] = 0.0
                        # aml[2]['discount_4'] = 0.0
                        if aml[2]['product_id'] in data:
                            aml[2]['quantity'] = data[aml[2]['product_id']]['quantity']
                        else:
                            aml[2]['quantity'] =  0
                        # aml[2]['quantity'] = data[aml[2]['product_id']]['quantity']
                        debit = aml[2]['quantity'] * aml[2]['price_unit']
                        aml[2]['debit'] = debit if debit > 0 else 0.0
                        aml[2]['credit'] = -debit if debit < 0 else 0.0
                        aml[2]['amount_currency'] = debit
                        aml[2]['price_subtotal'] = debit
                        aml[2]['price_total'] = debit
                        currency_id = self.env['res.currency'].sudo().browse(aml[2]['currency_id'])
                        untax_amount = self.env['account.tax'].sudo().browse(aml[2]['tax_ids'][0][2]).compute_all(debit, currency_id)
                        total_untax_amount += untax_amount['total_included'] - untax_amount['total_excluded']
                        total_debit += debit
                        total_credit -= debit

                for aml in res[0]['line_ids']:
                    if aml[2].get('exclude_from_invoice_tab', False) and aml[2].get('tax_repartition_line_id', False):
                        aml[2]['tax_base_amount'] = total_debit
                        aml[2]['price_unit'] = total_untax_amount
                        debit = aml[2]['price_unit']
                        aml[2]['debit'] = debit if debit > 0 else 0.0
                        aml[2]['credit'] = -debit if debit < 0 else 0.0
                        aml[2]['amount_currency'] = debit
                        aml[2]['price_subtotal'] = debit
                        aml[2]['price_total'] = debit
                        total_credit -= debit

                for aml in res[0]['line_ids']:
                    if aml[2].get('exclude_from_invoice_tab', False) and not aml[2].get('tax_repartition_line_id', True):
                        disc_account_id = int(self.env['ir.config_parameter'].sudo().search([('key', '=', 'discount_account_invoive.bill_discount_item_account')]).value) or None
                        if aml[2]['account_id'] == disc_account_id:
                            total_credit = 0
                        aml[2]['price_unit'] = total_credit
                        debit = aml[2]['price_unit']
                        aml[2]['debit'] = debit if debit > 0 else 0.0
                        aml[2]['credit'] = -debit if debit < 0 else 0.0
                        aml[2]['amount_currency'] = debit
                        aml[2]['price_subtotal'] = debit
                        aml[2]['price_total'] = debit
        # print('id',self.id)
        # delete_data = "delete from account_move_line where move_id={_id} and quantity = 0".format(
        #     _id=self.id)
        # self._cr.execute(delete_data)
        # self._cr.commit()
        return res


    # action confirm state draft - credit note
    def action_confirm_approve(self):
        self.write({'state': 'approval'})
    
    def _reverse_move_vals(self, default_values, cancel=True):
        res = super(AccountMove, self)._reverse_move_vals(default_values, cancel)
        return res

    # @api.depends('line_ids.amount_currency', 'line_ids.tax_base_amount', 'line_ids.tax_line_id', 'partner_id', 'currency_id', 'amount_total', 'amount_untaxed')
    # def _compute_tax_totals_json(self):
    #     """ Computed field used for custom widget's rendering.
    #         Only set on invoices.
    #     """
    #     for move in self:
    #         if not move.is_invoice(include_receipts=True):
    #             # Non-invoice moves don't support that field (because of multicurrency: all lines of the invoice share the same currency)
    #             move.tax_totals_json = None
    #             continue
    #
    #         tax_lines_data = move._prepare_tax_lines_data_for_totals_from_invoice()
    #         if move.is_from_so or move.is_from_po:
    #             taxes = 0
    #             tax_pph = 0
    #             for line in move.invoice_line_ids:
    #                 for tax_id in line.tax_ids:
    #                     if tax_id.tax_group_id.name == 'PPN':
    #                         taxes = tax_id.amount
    #                     if tax_id.tax_group_id.name == 'PPH 22' or tax_id.tax_group_id.name == 'PPH 23':
    #                         tax_pph = tax_id.amount
    #
    #             default_odoo_tax_totals_json = json.dumps({
    #                 **self._get_tax_totals(move.partner_id, tax_lines_data, move.amount_total, move.amount_untaxed, move.currency_id),
    #                 'allow_tax_edition': move.is_purchase_document(include_receipts=False) and move.state == 'draft',
    #             })
    #             json_object = json.loads(default_odoo_tax_totals_json)
    #
    #             currency = move.currency_id or move.partner_id.property_purchase_currency_id or self.env.company.currency_id
    #             amount_tax = currency.round((json_object.get('amount_untaxed') - move.global_order_discount) * taxes / 100)
    #             amount_pph = currency.round((json_object.get('amount_untaxed') - move.global_order_discount) * tax_pph / 100)
    #             total = currency.round((json_object.get('amount_untaxed') - move.global_order_discount) + amount_tax + amount_pph)
    #
    #             # json_object['tax_group_amount'] = amount_tax
    #             json_object['amount_total'] = total
    #             json_object['formatted_amount_total'] = formatLang(self.env, total, currency_obj=currency)
    #             # json_object['formatted_amount_untaxed'] = "Rp\xa0"+str(currency.round(json_object.get('amount_untaxed')))
    #             if json_object['groups_by_subtotal']:
    #                 for untaxed_amount in json_object['groups_by_subtotal']['Untaxed Amount']:
    #                     if untaxed_amount['tax_group_name'] == 'PPN':
    #                         # amount_tax = amount_tax
    #                         untaxed_amount['tax_group_amount'] = amount_tax
    #                         untaxed_amount['formatted_tax_group_amount'] = formatLang(self.env, amount_tax, currency_obj=currency)
    #                     elif untaxed_amount['tax_group_name'] == 'PPH 22' or untaxed_amount['tax_group_name'] == 'PPH 23':
    #                         # amount_tax = amount_pph
    #                         untaxed_amount['tax_group_amount'] = amount_pph
    #                         untaxed_amount['formatted_tax_group_amount'] = formatLang(self.env, amount_pph, currency_obj=currency)
    #
    #             move.tax_totals_json = json.dumps(json_object)
    #         # else:
    #         #     tax_lines_data = move._prepare_tax_lines_data_for_totals_from_invoice()
    #         #     move.tax_totals_json = json.dumps({
    #         #         **self._get_tax_totals(move.partner_id, tax_lines_data, move.amount_total, move.amount_untaxed, move.currency_id),
    #         #         'allow_tax_edition': move.is_purchase_document(include_receipts=False) and move.state == 'draft',
    #         #     })
    #         else:
    #             taxes = 0
    #             tax_pph = 0
    #             for line in move.invoice_line_ids:
    #                 for tax_id in line.tax_ids:
    #                     if tax_id.tax_group_id.name == 'PPN':
    #                         taxes = tax_id.amount
    #                     if tax_id.tax_group_id.name == 'PPH 22' or tax_id.tax_group_id.name == 'PPH 23':
    #                         tax_pph = tax_id.amount
    #
    #             default_odoo_tax_totals_json = json.dumps({
    #                 **self._get_tax_totals(move.partner_id, tax_lines_data, move.amount_total, move.amount_untaxed,
    #                                        move.currency_id),
    #                 'allow_tax_edition': move.is_purchase_document(include_receipts=False) and move.state == 'draft',
    #             })
    #             json_object = json.loads(default_odoo_tax_totals_json)
    #
    #             currency = move.currency_id or move.partner_id.property_purchase_currency_id or self.env.company.currency_id
    #             amount_tax = currency.round((json_object.get('amount_untaxed') - move.global_order_discount) * taxes / 100)
    #             amount_pph = currency.round((json_object.get('amount_untaxed') - move.global_order_discount) * tax_pph / 100)
    #             total = currency.round((json_object.get('amount_untaxed') - move.global_order_discount) + amount_tax + amount_pph)
    #
    #             # json_object['tax_group_amount'] = amount_tax
    #             json_object['amount_total'] = total
    #             json_object['formatted_amount_total'] = formatLang(self.env, total, currency_obj=currency)
    #             # json_object['formatted_amount_untaxed'] = "Rp\xa0"+str(currency.round(json_object.get('amount_untaxed')))
    #             if json_object['groups_by_subtotal']:
    #                 for untaxed_amount in json_object['groups_by_subtotal']['Untaxed Amount']:
    #                     if untaxed_amount['tax_group_name'] == 'PPN':
    #                         # amount_tax = amount_tax
    #                         untaxed_amount['tax_group_amount'] = amount_tax
    #                         untaxed_amount['formatted_tax_group_amount'] = formatLang(self.env, amount_tax, currency_obj=currency)
    #                     elif untaxed_amount['tax_group_name'] == 'PPH 22' or untaxed_amount['tax_group_name'] == 'PPH 23':
    #                         # amount_tax = amount_pph
    #                         untaxed_amount['tax_group_amount'] = amount_pph
    #                         untaxed_amount['formatted_tax_group_amount'] = formatLang(self.env, amount_pph, currency_obj=currency)
    #             move.tax_totals_json = json.dumps(json_object)

    # @api.depends('line_ids.amount_currency', 'line_ids.tax_base_amount', 'line_ids.tax_line_id', 'partner_id',
    #              'currency_id', 'amount_total', 'amount_untaxed')
    # def _compute_tax_totals_json(self):
    #     """ Computed field used for custom widget's rendering.
    #         Only set on invoices.
    #     """
    #     for move in self:
    #         if not move.is_invoice(include_receipts=True):
    #             # Non-invoice moves don't support that field (because of multicurrency: all lines of the invoice share the same currency)
    #             move.tax_totals_json = None
    #             continue
    #
    #         tax_lines_data = move._prepare_tax_lines_data_for_totals_from_invoice()
    #         if move.is_from_so or move.is_from_po:
    #             taxes = 0
    #             tax_pph = 0
    #             for line in move.invoice_line_ids:
    #                 for tax_id in line.tax_ids:
    #                     if tax_id.tax_group_id.name == 'PPN':
    #                         taxes = tax_id.amount
    #                     if tax_id.tax_group_id.name == 'PPH 22' or tax_id.tax_group_id.name == 'PPH 23':
    #                         tax_pph = tax_id.amount
    #
    #             default_odoo_tax_totals_json = json.dumps({
    #                 **self._get_tax_totals(move.partner_id, tax_lines_data, move.amount_total, move.amount_untaxed,
    #                                        move.currency_id),
    #                 'allow_tax_edition': move.is_purchase_document(include_receipts=False) and move.state == 'draft',
    #             })
    #             json_object = json.loads(default_odoo_tax_totals_json)
    #
    #             currency = move.currency_id or move.partner_id.property_purchase_currency_id or self.env.company.currency_id
    #             amount_tax = currency.round((move.amount_untaxed - move.global_order_discount) * taxes / 100)
    #             amount_pph = currency.round((move.amount_untaxed - move.global_order_discount) * tax_pph / 100)
    #             total = currency.round((move.amount_untaxed - move.global_order_discount) + amount_tax + amount_pph)
    #
    #             # json_object['tax_group_amount'] = amount_tax
    #             json_object['amount_total'] = total
    #             json_object['formatted_amount_total'] = formatLang(self.env, total, currency_obj=currency)
    #             # json_object['formatted_amount_untaxed'] = "Rp\xa0"+str(currency.round(json_object.get('amount_untaxed')))
    #             if json_object['groups_by_subtotal']:
    #                 for untaxed_amount in json_object['groups_by_subtotal']['Untaxed Amount']:
    #                     if untaxed_amount['tax_group_name'] == 'PPN':
    #                         # amount_tax = amount_tax
    #                         untaxed_amount['tax_group_amount'] = amount_tax
    #                         untaxed_amount['formatted_tax_group_amount'] = formatLang(self.env, amount_tax,
    #                                                                                   currency_obj=currency)
    #                     elif untaxed_amount['tax_group_name'] == 'PPH 22' or untaxed_amount[
    #                         'tax_group_name'] == 'PPH 23':
    #                         # amount_tax = amount_pph
    #                         untaxed_amount['tax_group_amount'] = amount_pph
    #                         untaxed_amount['formatted_tax_group_amount'] = formatLang(self.env, amount_pph,
    #                                                                                   currency_obj=currency)
    #
    #             move.tax_totals_json = json.dumps(json_object)
    #         # else:
    #         #     tax_lines_data = move._prepare_tax_lines_data_for_totals_from_invoice()
    #         #     move.tax_totals_json = json.dumps({
    #         #         **self._get_tax_totals(move.partner_id, tax_lines_data, move.amount_total, move.amount_untaxed, move.currency_id),
    #         #         'allow_tax_edition': move.is_purchase_document(include_receipts=False) and move.state == 'draft',
    #         #     })
    #         else:
    #             taxes = 0
    #             tax_pph = 0
    #             for line in move.invoice_line_ids:
    #                 for tax_id in line.tax_ids:
    #                     if tax_id.tax_group_id.name == 'PPN':
    #                         taxes = tax_id.amount
    #                     if tax_id.tax_group_id.name == 'PPH 22' or tax_id.tax_group_id.name == 'PPH 23':
    #                         tax_pph = tax_id.amount
    #
    #             default_odoo_tax_totals_json = json.dumps({
    #                 **self._get_tax_totals(move.partner_id, tax_lines_data, move.amount_total, move.amount_untaxed,
    #                                        move.currency_id),
    #                 'allow_tax_edition': move.is_purchase_document(include_receipts=False) and move.state == 'draft',
    #             })
    #             json_object = json.loads(default_odoo_tax_totals_json)
    #
    #             currency = move.currency_id or move.partner_id.property_purchase_currency_id or self.env.company.currency_id
    #             amount_tax = currency.round((move.amount_untaxed - move.global_order_discount) * taxes / 100)
    #             amount_pph = currency.round((move.amount_untaxed - move.global_order_discount) * tax_pph / 100)
    #             total = currency.round((move.amount_untaxed - move.global_order_discount) + amount_tax + amount_pph)
    #
    #             # json_object['tax_group_amount'] = amount_tax
    #             json_object['amount_total'] = total
    #             json_object['formatted_amount_total'] = formatLang(self.env, total, currency_obj=currency)
    #             # json_object['formatted_amount_untaxed'] = "Rp\xa0"+str(currency.round(json_object.get('amount_untaxed')))
    #             if json_object['groups_by_subtotal']:
    #                 for untaxed_amount in json_object['groups_by_subtotal']['Untaxed Amount']:
    #                     if untaxed_amount['tax_group_name'] == 'PPN':
    #                         # amount_tax = amount_tax
    #                         untaxed_amount['tax_group_amount'] = amount_tax
    #                         untaxed_amount['formatted_tax_group_amount'] = formatLang(self.env, amount_tax,
    #                                                                                   currency_obj=currency)
    #                     elif untaxed_amount['tax_group_name'] == 'PPH 22' or untaxed_amount[
    #                         'tax_group_name'] == 'PPH 23':
    #                         # amount_tax = amount_pph
    #                         untaxed_amount['tax_group_amount'] = amount_pph
    #                         untaxed_amount['formatted_tax_group_amount'] = formatLang(self.env, amount_pph,
    #                                                                                   currency_obj=currency)
    #             move.tax_totals_json = json.dumps(json_object)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    additional_margin = fields.Float(string='Additional Margin (%)')
    discount_amount = fields.Monetary(string='Discount Amount')
    product_margin_percent = fields.Char(string='Product Margin (%)')
    product_margin_amount = fields.Float(string='Product Margin')


    @api.model
    def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes, move_type):
        res = super(AccountMoveLine, self)._get_price_total_and_subtotal_model(price_unit, quantity, discount, currency, product, partner, taxes, move_type)

        if self.move_id.move_type in ['out_refund', 'in_refund']:
            subtotal_after_margin = ((self.price_unit - self.product_margin_amount - self.additional_margin) + self.product_margin_amount + self.additional_margin) * self.quantity
            if self.product_margin_amount:
                res['price_subtotal'] = subtotal_after_margin - self.discount_amount
        else:
            additional_margin = self.price_unit * self.additional_margin / 100
            dis_res = self.price_unit + self.product_margin_amount + additional_margin
            discount_percent = dis_res * self.discount / 100
            subtotal = ((self.price_unit + self.product_margin_amount + additional_margin) - (self.discount_amount))
            if taxes:
                taxes_res = taxes._origin.with_context(force_sign=1).compute_all(subtotal,
                    quantity=quantity, currency=currency, product=product, partner=partner, is_refund=move_type in ('out_refund', 'in_refund'))

                if self.product_margin_amount:
                    res['price_subtotal'] = taxes_res['total_excluded']

        # if self.move_id.id != False:
        #     delete_data = "delete from account_move_line where move_id={_id} and quantity = 0".format(
        #         _id=self.move_id.id)
        #     self._cr.execute(delete_data)
        #     self._cr.commit()
        return res
