# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################

import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare
import json
from itertools import groupby
import math

import time

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    def func_update_total_tax(self):
        total_tax = self.env['account.move'].sudo().search([])

        for line in total_tax.invoice_line_ids:
            line._compute_tax_line()
        return True

    def func_update_total_tax_all(self):
        total_tax = self.env['account.move'].sudo().search([])

        for line in total_tax:
            line._compute_total_tax()
        return True

    def _stock_account_prepare_anglo_saxon_out_lines_vals(self):
        ''' Prepare values used to create the journal items (account.move.line) corresponding to the Cost of Good Sold
        lines (COGS) for customer invoices.

        Example:

        Buy a product having a cost of 9 being a storable product and having a perpetual valuation in FIFO.
        Sell this product at a price of 10. The customer invoice's journal entries looks like:

        Account                                     | Debit | Credit
        ---------------------------------------------------------------
        200000 Product Sales                        |       | 10.0
        ---------------------------------------------------------------
        101200 Account Receivable                   | 10.0  |
        ---------------------------------------------------------------

        This method computes values used to make two additional journal items:

        ---------------------------------------------------------------
        220000 Expenses                             | 9.0   |
        ---------------------------------------------------------------
        101130 Stock Interim Account (Delivered)    |       | 9.0
        ---------------------------------------------------------------

        Note: COGS are only generated for customer invoices except refund made to cancel an invoice.

        :return: A list of Python dictionary to be passed to env['account.move.line'].create.
        '''
        lines_vals_list = []
        price_unit_prec = self.env['decimal.precision'].precision_get('Product Price')
        for move in self:
            # Make the loop multi-company safe when accessing models like product.product
            move = move.with_company(move.company_id)

            if not move.is_sale_document(include_receipts=True) or not move.company_id.anglo_saxon_accounting:
                continue

            for line in move.invoice_line_ids:

                # Filter out lines being not eligible for COGS.
                if not line._eligible_for_cogs():
                    continue

                # Retrieve accounts needed to generate the COGS.
                accounts = line.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=move.fiscal_position_id)
                debit_interim_account = accounts['stock_output']
                credit_expense_account = accounts['expense'] or move.journal_id.default_account_id
                if not debit_interim_account or not credit_expense_account:
                    continue

                # Compute accounting fields.
                sign = -1 if move.move_type == 'out_refund' else 1
                price_unit = line._stock_account_get_anglo_saxon_price_unit()
                balance = sign * line.quantity * price_unit

                if move.currency_id.is_zero(balance) or float_is_zero(price_unit, precision_digits=price_unit_prec):
                    continue

                # Add interim account line.
                if line.name:
                    name = line.name,
                else:
                    name = line.product_id.name
                lines_vals_list.append({
                    'name': name[:64],
                    'move_id': move.id,
                    'partner_id': move.commercial_partner_id.id,
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_uom_id.id,
                    'quantity': line.quantity,
                    'price_unit': price_unit,
                    'debit': balance < 0.0 and -balance or 0.0,
                    'credit': balance > 0.0 and balance or 0.0,
                    'account_id': debit_interim_account.id,
                    'exclude_from_invoice_tab': True,
                    'is_anglo_saxon_line': True,
                })

                # Add expense account line.
                lines_vals_list.append({
                    'name': name[:64],
                    'move_id': move.id,
                    'partner_id': move.commercial_partner_id.id,
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_uom_id.id,
                    'quantity': line.quantity,
                    'price_unit': -price_unit,
                    'debit': balance > 0.0 and balance or 0.0,
                    'credit': balance < 0.0 and -balance or 0.0,
                    'account_id': credit_expense_account.id,
                    'analytic_account_id': line.analytic_account_id.id,
                    'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
                    'exclude_from_invoice_tab': True,
                    'is_anglo_saxon_line': True,
                })
        return lines_vals_list

    @api.depends('line_ids.amount_currency', 'line_ids.tax_base_amount', 'line_ids.tax_line_id', 'partner_id', 'currency_id', 'amount_total', 'amount_untaxed')
    def _compute_tax_totals_json(self):
        """ Computed field used for custom widget's rendering.
            Only set on invoices.
        """
        for move in self:
            if not move.is_invoice(include_receipts=True):
                # Non-invoice moves don't support that field (because of multicurrency: all lines of the invoice share the same currency)
                move.tax_totals_json = None
                continue

            tax_lines_data = move._prepare_tax_lines_data_for_totals_from_invoice()

            move.tax_totals_json = json.dumps({
                **self._get_tax_totals(move.partner_id, tax_lines_data, move.amount_total, move.amount_untaxed, move.currency_id),
                'allow_tax_edition': move.is_purchase_document(include_receipts=True) and move.state == 'draft',
            })
            if move.tax_helper_flag == True and move.tax_totals_json:
                total_tax_ppn = 0
                check_tax_ppn = 0
                total_tax_pph = 0
                check_tax_pph = 0
                price_subtotal = 0
                for invoice_line_id in move.invoice_line_ids:
                    if move.move_type == 'out_invoice' and move.is_from_so == False:
                        # discount_perline = invoice_line_id.discount if invoice_line_id.discount_type == 'fixed' else invoice_line_id.harga_satuan * invoice_line_id.discount / 100.0
                        discount_perline = invoice_line_id.discount_amount
                        price_subtotal = (invoice_line_id.harga_satuan - discount_perline) * invoice_line_id.quantity
                        for tax_id in invoice_line_id.tax_ids:
                            if 'ppn' in tax_id.name.lower():
                                check_tax_ppn = tax_id.id
                                # total_tax_ppn += invoice_line_id.price_subtotal * tax_id.amount / 100
                                total_tax_ppn += (price_subtotal - move.global_order_discount) * tax_id.amount / 100
                            else:
                                check_tax_pph = tax_id.id
                                total_tax_pph += (price_subtotal - move.global_order_discount) * tax_id.amount / 100
                    if move.move_type == 'in_invoice' and move.is_from_po == False:
                        ati_harga_unit = invoice_line_id.ati_price_unit
                        line_discount_1 = ati_harga_unit * invoice_line_id.discount_1 / 100.0 if invoice_line_id.discount_1 else 0.0
                        ati_harga_unit = ati_harga_unit - line_discount_1
                        line_discount_2 = ati_harga_unit * invoice_line_id.discount_2 / 100.0 if invoice_line_id.discount_2 else 0.0
                        ati_harga_unit = ati_harga_unit - line_discount_2
                        line_discount_3 = invoice_line_id.discount_3 if invoice_line_id.discount_3 else 0.0
                        ati_harga_unit = ati_harga_unit - line_discount_3
                        line_discount_4 = invoice_line_id.discount_4 if invoice_line_id.discount_4 else 0.0
                        ati_harga_unit = ati_harga_unit - line_discount_4
                        total_discount_line = (line_discount_1 + line_discount_2 + line_discount_3 + line_discount_4)
                        price_subtotal = ati_harga_unit * invoice_line_id.quantity
                        for tax_id in invoice_line_id.tax_ids:
                            if 'ppn' in tax_id.name.lower():
                                check_tax_ppn = tax_id.id
                                # total_tax_ppn += invoice_line_id.price_subtotal * tax_id.amount / 100
                                total_tax_ppn += (price_subtotal - move.global_order_discount) * tax_id.amount / 100
                            else:
                                check_tax_pph = tax_id.id
                                total_tax_pph += (price_subtotal - move.global_order_discount) * tax_id.amount / 100
                tax_totals = json.loads(move.tax_totals_json)
                if 'Untaxed Amount' in tax_totals['groups_by_subtotal']:
                    for group in tax_totals['groups_by_subtotal']['Untaxed Amount']:
                        if total_tax_ppn > 0:
                            group['tax_group_amount'] = total_tax_ppn
                            group['formatted_tax_group_amount'] = "Rp\u00a0{:,.2f}".format(total_tax_ppn)
                            updated_tax_totals_json = json.dumps(tax_totals)
                            move.write({'tax_totals_json': updated_tax_totals_json})

                new_amount_total = (price_subtotal - move.global_order_discount) + total_tax_ppn + total_tax_pph

                tax_totals['amount_total'] = new_amount_total
                tax_totals['formatted_amount_total'] = "Rp\u00a0{:,.2f}".format(new_amount_total)
                updated_tax_totals_json = json.dumps(tax_totals)
                move.write({'tax_totals_json': updated_tax_totals_json})

    tax_helper_flag = fields.Boolean(string='Taxes Helper', default=False)

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
                    price_unit_wo_discount = sign * (price_unit_wo_discount - (base_line.discount / (base_line.quantity or 1.0)))
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

                tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_vals['tax_repartition_line_id'])
                tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id

                taxes_map_entry = taxes_map.setdefault(grouping_key, {
                    'tax_line': None,
                    'amount': 0.0,
                    'tax_base_amount': 0.0,
                    'grouping_dict': False,
                })
                taxes_map_entry['amount'] += tax_vals['amount']
                taxes_map_entry['tax_base_amount'] += self._get_base_amount_to_display(tax_vals['base'], tax_repartition_line, tax_vals['group'])
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
            tax_base_amount = currency._convert(taxes_map_entry['tax_base_amount'], self.company_currency_id, self.company_id, self.date or fields.Date.context_today(self))

            # Recompute only the tax_base_amount.
            if recompute_tax_base_amount:
                if taxes_map_entry['tax_line']:
                    taxes_map_entry['tax_line'].tax_base_amount = tax_base_amount
                continue

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
                create_method = in_draft_mode and self.env['account.move.line'].new or self.env['account.move.line'].create
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
                taxes_map_entry['tax_line'].update(taxes_map_entry['tax_line']._get_fields_onchange_balance(force_computation=True))

    @api.depends('line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched',
                 'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
                 'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
                 'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched',
                 'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
                 'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
                 'line_ids.debit',
                 'line_ids.credit',
                 'line_ids.currency_id',
                 'line_ids.amount_currency',
                 'line_ids.amount_residual',
                 'line_ids.amount_residual_currency',
                 'line_ids.payment_id.state',
                 'line_ids.full_reconcile_id',
                 'global_discount_type',
                 'global_order_discount')
    def _compute_amount(self):
        for move in self:
            if move.payment_state == 'invoicing_legacy':
                # invoicing_legacy state is set via SQL when setting setting field
                # invoicing_switch_threshold (defined in account_accountant).
                # The only way of going out of this state is through this setting,
                # so we don't recompute it here.
                move.payment_state = move.payment_state
                continue

            total_untaxed = 0.0
            total_untaxed_currency = 0.0
            total_tax = 0.0
            total_tax_currency = 0.0
            total_to_pay = 0.0
            total_residual = 0.0
            total_residual_currency = 0.0
            total = 0.0
            total_currency = 0.0
            total_global_discount = 0.0
            total_discount = 0.0
            global_discount = 0.0
            global_discount_currency = 0.0
            currencies = move._get_lines_onchange_currency().currency_id

            total_discount_1_2_3_4 = 0
            total_discount_1 = 0
            total_discount_2 = 0
            total_discount_3 = 0
            total_discount_4 = 0

            price_subtotal_po = 0
            total_discount_so = 0
            total_discount_so_all = 0
            total_tax_ppn = 0
            check_tax_ppn = 0
            total_tax_pph = 0
            check_tax_pph = 0
            for invoice_line_id in move.invoice_line_ids:

                if move.move_type == 'out_invoice':
                    if move.is_from_so != False:
                        invoice_line_id.ati_price_unit = invoice_line_id.sale_line_ids.price_unit
                        invoice_line_id.harga_satuan = (invoice_line_id.sale_line_ids.price_subtotal / invoice_line_id.sale_line_ids.product_uom_qty) + invoice_line_id.sale_line_ids.discount_amount
                        invoice_line_id.price_subtotal = invoice_line_id.sale_line_ids.price_subtotal
                        if invoice_line_id.discount_type == 'fixed':
                            total_discount_so = invoice_line_id.sale_line_ids.discount_amount
                        elif invoice_line_id.discount_type == 'percent':
                            total_discount_so = invoice_line_id.sale_line_ids.discount_amount

                        string_id_new = str(invoice_line_id.id)
                        count_underscore = string_id_new.count('_')
                        if count_underscore == 0:
                            # discount_perline = invoice_line_id.discount if invoice_line_id.discount_type == 'fixed' else invoice_line_id.harga_satuan * invoice_line_id.discount / 100.0
                            discount_perline = invoice_line_id.discount_amount
                            price_subtotal = (invoice_line_id.harga_satuan - discount_perline) * invoice_line_id.quantity
                            for tax_id in invoice_line_id.tax_ids:
                                if 'ppn' in tax_id.name.lower():
                                    check_tax_ppn = tax_id.id
                                    # total_tax_ppn += invoice_line_id.price_subtotal * tax_id.amount / 100
                                    total_tax_ppn += (price_subtotal - invoice_line_id.global_diskon_line) * tax_id.amount / 100
                                else:
                                    check_tax_pph = tax_id.id
                                    total_tax_pph += (price_subtotal - invoice_line_id.global_diskon_line) * tax_id.amount / 100
                    elif move.is_from_so == False:
                        if len(invoice_line_id.product_id) > 0 and invoice_line_id.product_id.standard_price > 0:
                            # invoice_line_id.ati_price_unit = invoice_line_id.product_id.standard_price
                            # invoice_line_id.harga_satuan = invoice_line_id.ati_price_unit
                            string_id_new = str(invoice_line_id.id)
                            count_underscore = string_id_new.count('_')
                            if count_underscore == 0:
                                self._cr.execute(
                                    """
                                        select ati_price_unit from account_move_line where id = {_id}
                                    """.format(_id=invoice_line_id.id))
                                check_price = self._cr.dictfetchall()
                                invoice_line_id.ati_price_unit = check_price[0]['ati_price_unit']

                                self._cr.execute(
                                    """
                                        select harga_satuan from account_move_line where id = {_id} 
                                    """.format(_id=invoice_line_id.id))
                                check_harga_satuan = self._cr.dictfetchall()
                                invoice_line_id.harga_satuan = check_harga_satuan[0]['harga_satuan']

                            # invoice_line_id.harga_satuan = invoice_line_id.ati_price_unit
                            # invoice_line_id.price_unit = invoice_line_id.harga_satuan
                        else:
                            string_id_new = str(invoice_line_id.id)
                            count_underscore = string_id_new.count('_')
                            if count_underscore == 0:
                                self._cr.execute(
                                    """
                                        select ati_price_unit from account_move_line where id = {_id} 
                                    """.format(_id=invoice_line_id.id))
                                check_price = self._cr.dictfetchall()
                                invoice_line_id.ati_price_unit = check_price[0]['ati_price_unit']

                                self._cr.execute(
                                    """
                                        select harga_satuan from account_move_line where id = {_id} 
                                    """.format(_id=invoice_line_id.id))
                                check_harga_satuan = self._cr.dictfetchall()
                                invoice_line_id.harga_satuan = check_harga_satuan[0]['harga_satuan']

                            # invoice_line_id.harga_satuan = invoice_line_id.ati_price_unit
                            # invoice_line_id.price_unit = invoice_line_id.harga_satuan
                        count_underscore = string_id_new.count('_')
                        if count_underscore == 0:
                            # discount_perline = invoice_line_id.discount if invoice_line_id.discount_type == 'fixed' else invoice_line_id.harga_satuan * invoice_line_id.discount / 100.0
                            discount_perline = invoice_line_id.discount_amount
                            price_subtotal = (invoice_line_id.harga_satuan - discount_perline) * invoice_line_id.quantity
                            for tax_id in invoice_line_id.tax_ids:
                                if 'ppn' in tax_id.name.lower():
                                    check_tax_ppn = tax_id.id
                                    # total_tax_ppn += invoice_line_id.price_subtotal * tax_id.amount / 100
                                    total_tax_ppn += price_subtotal * tax_id.amount / 100
                                else:
                                    check_tax_pph = tax_id.id
                                    total_tax_pph += price_subtotal * tax_id.amount / 100
                            # price_total_tax += invoice_line_id.price_total
                            # price_subtotal_tax += invoice_line_id.price_subtotal
                        if total_tax_ppn > 0:
                            if move.tax_helper_flag == True and invoice_line_id.bantuan_ppn == False:
                                new_aml_vals = {
                                    'name': 'PPN - 11% (Sales)',
                                    'display_type': False,
                                    'quantity': 1,
                                    'account_id': int(self.env['account.account'].sudo().search(
                                        [('name', '=', 'VAT Sales')]).id) or None,
                                    # 'product_uom_id': line.product_id.uom_id.id,
                                    'debit': 0,
                                    'credit': total_tax_ppn,
                                    'parent_state': 'draft',
                                    'company_id': invoice_line_id.company_id.id,
                                    'journal_id': invoice_line_id.journal_id.id,
                                    # 'analytic_account_id': self.analytic_account_id.id,
                                    'exclude_from_invoice_tab': True,
                                    # 'tax_tag_invert': invert,
                                    'partner_id': invoice_line_id.partner_id.id,
                                    'move_id': invoice_line_id.move_id.id,
                                    # 'tax_line_id': tax_id.id,
                                }
                                new_aml_id = self.env['account.move.line'].sudo().create(new_aml_vals)
                                invoice_line_id.bantuan_ppn = True
                        if total_tax_pph > 0:
                            if move.tax_helper_flag == True and invoice_line_id.bantuan_pph == False:
                                new_aml_vals = {
                                    'name': 'PPH - Sales',
                                    'display_type': False,
                                    'quantity': 1,
                                    'account_id': int(self.env['account.account'].sudo().search(
                                        [('name', '=', 'Prepaid Tax Pph 22')]).id) or None,
                                    # 'product_uom_id': line.product_id.uom_id.id,
                                    'debit': 0,
                                    'credit': total_tax_pph,
                                    'parent_state': 'draft',
                                    'company_id': invoice_line_id.company_id.id,
                                    'journal_id': invoice_line_id.journal_id.id,
                                    # 'analytic_account_id': self.analytic_account_id.id,
                                    'exclude_from_invoice_tab': True,
                                    # 'tax_tag_invert': invert,
                                    'partner_id': invoice_line_id.partner_id.id,
                                    'move_id': invoice_line_id.move_id.id,
                                    # 'tax_line_id': tax_id.id,
                                }
                                new_aml_id = self.env['account.move.line'].sudo().create(new_aml_vals)
                                invoice_line_id.bantuan_pph = True

                        if invoice_line_id.discount_type == 'fixed':
                            total_discount_so = invoice_line_id.discount
                        elif invoice_line_id.discount_type == 'percent':
                            total_discount_so = invoice_line_id.harga_satuan * invoice_line_id.discount / 100
                if move.move_type == 'in_invoice':
                    # invoice_line_id.ati_price_unit = invoice_line_id.purchase_line_id.ati_price_unit
                    # invoice_line_id.harga_satuan = invoice_line_id.ati_price_unit
                    # ati_price_unit = invoice_line_id.ati_price_unit
                    if move.is_from_po != False:
                        invoice_line_id.ati_price_unit = invoice_line_id.purchase_line_id.ati_price_unit
                        invoice_line_id.harga_satuan = invoice_line_id.ati_price_unit
                        ati_price_unit = invoice_line_id.ati_price_unit
                        total_discount_1 = ati_price_unit * invoice_line_id.discount_1 / 100.0 if invoice_line_id.discount_1 else 0.0
                        ati_price_unit = ati_price_unit - total_discount_1

                        total_discount_2 = ati_price_unit * invoice_line_id.discount_2 / 100.0 if invoice_line_id.discount_2 else 0.0
                        ati_price_unit = ati_price_unit - total_discount_2

                        total_discount_3 = invoice_line_id.discount_3 if invoice_line_id.discount_3 else 0.0
                        ati_price_unit = ati_price_unit - total_discount_3

                        total_discount_4 = invoice_line_id.discount_4 if invoice_line_id.discount_4 else 0.0
                        ati_price_unit = ati_price_unit - total_discount_4

                        # total_discount_line= (total_discount_1 + total_discount_2 + total_discount_3 + total_discount_4) * invoice_line_id.quantity
                    elif move.is_from_po == False:
                        ati_price_unit = invoice_line_id.ati_price_unit
                        if len(invoice_line_id.product_id) > 0 and invoice_line_id.product_id.hna > 0 :
                            # invoice_line_id.ati_price_unit = invoice_line_id.product_id.hna
                            # invoice_line_id.harga_satuan = invoice_line_id.ati_price_unit
                            string_id_new = str(invoice_line_id.id)
                            count_underscore = string_id_new.count('_')
                            if count_underscore == 0:
                                self._cr.execute(
                                    """
                                        select ati_price_unit from account_move_line where id = {_id} 
                                    """.format(_id=invoice_line_id.id))
                                check_price = self._cr.dictfetchall()
                                invoice_line_id.ati_price_unit = check_price[0]['ati_price_unit']
                            invoice_line_id.harga_satuan = invoice_line_id.ati_price_unit
                            invoice_line_id.price_unit = invoice_line_id.ati_price_unit
                        else:
                            string_id_new = str(invoice_line_id.id)
                            count_underscore = string_id_new.count('_')
                            if count_underscore == 0:
                                self._cr.execute(
                                    """
                                        select ati_price_unit from account_move_line where id = {_id} 
                                    """.format(_id=invoice_line_id.id))
                                check_price = self._cr.dictfetchall()
                                invoice_line_id.ati_price_unit = check_price[0]['ati_price_unit']
                            invoice_line_id.harga_satuan = invoice_line_id.ati_price_unit
                            invoice_line_id.price_unit = invoice_line_id.ati_price_unit
                        for tax_id in invoice_line_id.tax_ids:
                            if 'ppn' in tax_id.name.lower():
                                check_tax_ppn = tax_id.id
                                total_tax_ppn += (invoice_line_id.price_subtotal - invoice_line_id.global_diskon_line) * tax_id.amount / 100
                            else:
                                check_tax_pph = tax_id.id
                                total_tax_pph += (invoice_line_id.price_subtotal - invoice_line_id.global_diskon_line) * tax_id.amount / 100
                        if total_tax_ppn > 0:
                            if move.tax_helper_flag == True and invoice_line_id.bantuan_ppn == False:
                                new_aml_vals = {
                                    'name': 'PPN - 11% (Beli)',
                                    'display_type': False,
                                    'quantity': 1,
                                    'account_id': int(self.env['account.account'].sudo().search(
                                        [('name', '=', 'VAT Purchase')]).id) or None,
                                    # 'product_uom_id': line.product_id.uom_id.id,
                                    'debit': total_tax_ppn,
                                    'credit': 0,
                                    'parent_state': 'draft',
                                    'company_id': invoice_line_id.company_id.id,
                                    'journal_id': invoice_line_id.journal_id.id,
                                    # 'analytic_account_id': self.analytic_account_id.id,
                                    'exclude_from_invoice_tab': True,
                                    # 'tax_tag_invert': invert,
                                    'partner_id': invoice_line_id.partner_id.id,
                                    'move_id': invoice_line_id.move_id.id,
                                    # 'tax_line_id': tax_id.id,
                                }
                                new_aml_id = self.env['account.move.line'].sudo().create(new_aml_vals)
                                invoice_line_id.bantuan_ppn = True
                        if total_tax_pph > 0:
                            if move.tax_helper_flag == True and invoice_line_id.bantuan_pph == False:
                                new_aml_vals = {
                                    'name': 'PPH 22 (0.3%)',
                                    'display_type': False,
                                    'quantity': 1,
                                    'account_id': int(self.env['account.account'].sudo().search(
                                        [('name', '=', 'Prepaid Tax Pph 22')]).id) or None,
                                    # 'product_uom_id': line.product_id.uom_id.id,
                                    'debit': total_tax_pph,
                                    'credit': 0,
                                    'parent_state': 'draft',
                                    'company_id': invoice_line_id.company_id.id,
                                    'journal_id': invoice_line_id.journal_id.id,
                                    # 'analytic_account_id': self.analytic_account_id.id,
                                    'exclude_from_invoice_tab': True,
                                    # 'tax_tag_invert': invert,
                                    'partner_id': invoice_line_id.partner_id.id,
                                    'move_id': invoice_line_id.move_id.id,
                                    # 'tax_line_id': tax_id.id,
                                }
                                new_aml_id = self.env['account.move.line'].sudo().create(new_aml_vals)
                                invoice_line_id.bantuan_pph = True
                        total_discount_1 = ati_price_unit * invoice_line_id.discount_1 / 100.0 if invoice_line_id.discount_1 else 0.0
                        ati_price_unit = ati_price_unit - total_discount_1

                        total_discount_2 = ati_price_unit * invoice_line_id.discount_2 / 100.0 if invoice_line_id.discount_2 else 0.0
                        ati_price_unit = ati_price_unit - total_discount_2

                        total_discount_3 = invoice_line_id.discount_3 if invoice_line_id.discount_3 else 0.0
                        ati_price_unit = ati_price_unit - total_discount_3

                        total_discount_4 = invoice_line_id.discount_4 if invoice_line_id.discount_4 else 0.0
                        ati_price_unit = ati_price_unit - total_discount_4
                total_discount_1_2_3_4 += (total_discount_1 + total_discount_2 + total_discount_3 + total_discount_4) * invoice_line_id.quantity
                total_discount_so_all += total_discount_so * invoice_line_id.quantity

            for line in move.line_ids:
                # if move.tax_helper_flag == True:
                #     for invoice_line_id in move.invoice_line_ids:
                #         for tax_id in invoice_line_id.tax_ids:
                #             line.tax_line_id = tax_id
                #             print(line.tax_line_id)
                if move._payment_state_matters():
                    # === Invoices ===
                    if not line.exclude_from_invoice_tab:
                        # Untaxed amount.
                        if move.move_type == 'out_invoice' and move.is_from_so:
                            line.harga_satuan = (line.sale_line_ids.price_subtotal / line.sale_line_ids.product_uom_qty) + line.sale_line_ids.discount_amount
                            if line.discount_type == 'fixed':
                                # discount_invoice = line.discount
                                discount_invoice = line.sale_line_ids.discount_amount
                            elif line.discount_type == 'percent':
                                # discount_invoice = line.harga_satuan * line.discount / 100
                                discount_invoice = line.sale_line_ids.discount_amount
                            line.credit = (line.harga_satuan - discount_invoice) * line.quantity
                            line.price_subtotal = line.credit
                            line.amount_currency = line.balance
                        if move.move_type == 'in_invoice' and move.is_from_po:
                            ati_harga_unit = line.ati_price_unit
                            line_discount_1 = ati_harga_unit * line.discount_1 / 100.0 if line.discount_1 else 0.0
                            ati_harga_unit = ati_harga_unit - line_discount_1
                            line_discount_2 = ati_harga_unit * line.discount_2 / 100.0 if line.discount_2 else 0.0
                            ati_harga_unit = ati_harga_unit - line_discount_2
                            line_discount_3 = line.discount_3 if line.discount_3 else 0.0
                            ati_harga_unit = ati_harga_unit - line_discount_3
                            line_discount_4 = line.discount_4 if line.discount_4 else 0.0
                            ati_harga_unit = ati_harga_unit - line_discount_4
                            total_discount_line = (line_discount_1 + line_discount_2 + line_discount_3 + line_discount_4)
                            line.debit = ati_harga_unit * line.quantity
                            line.price_subtotal = ati_harga_unit * line.quantity
                        if move.move_type == 'in_refund' and line.purchase_line_id.id > 0:
                            ati_harga_unit = line.ati_price_unit
                            line.credit = ati_harga_unit * line.quantity
                            line.price_subtotal = ati_harga_unit * line.quantity
                        if move.move_type == 'in_refund' and move.is_from_po == False and line.purchase_line_id.id==0:
                            if len(line.product_id) > 0 and line.product_id.hna > 0:
                                # line.ati_price_unit = line.product_id.hna
                                string_id_new = str(line.id)
                                count_underscore = string_id_new.count('_')
                                if count_underscore == 0:
                                    self._cr.execute(
                                        """
                                            select ati_price_unit from account_move_line where id = {_id} 
                                        """.format(_id=line.id))
                                    check_price = self._cr.dictfetchall()
                                    line.ati_price_unit = check_price[0]['ati_price_unit']
                                line.harga_satuan = line.ati_price_unit
                                line.price_unit = line.ati_price_unit
                            else:
                                string_id_new = str(line.id)
                                count_underscore = string_id_new.count('_')
                                if count_underscore == 0:
                                    self._cr.execute(
                                        """
                                            select ati_price_unit from account_move_line where id = {_id} 
                                        """.format(_id=line.id))
                                    check_price = self._cr.dictfetchall()
                                    line.ati_price_unit = check_price[0]['ati_price_unit']
                                line.harga_satuan = line.ati_price_unit
                                line.price_unit = line.ati_price_unit
                            line.harga_satuan = line.ati_price_unit
                            line.price_unit = line.ati_price_unit
                            discount_perline = line.discount if line.discount_type == 'fixed' else line.ati_price_unit * line.discount / 100.0
                            line.credit = (line.ati_price_unit - discount_perline) * line.quantity
                            line.price_subtotal = (line.ati_price_unit - discount_perline) * line.quantity

                        if move.move_type == 'out_invoice' and not move.is_from_so:
                            # discount_perline = line.discount if line.discount_type == 'fixed' else line.harga_satuan * line.discount / 100.0
                            discount_perline = line.discount_amount
                            line.credit = (line.harga_satuan - discount_perline) * line.quantity
                            line.price_subtotal = (line.harga_satuan - discount_perline) * line.quantity
                            if move.tax_helper_flag == True:
                                line.balance = line.price_subtotal + total_tax_ppn + total_tax_pph
                            # line.price_unit = line.ati_price_unit
                        if move.move_type == 'out_refund' and line.sale_line_ids.id != False:
                            discount_perline = line.discount if line.discount_type == 'fixed' else line.harga_satuan * line.discount / 100.0
                            line.debit = (line.harga_satuan - discount_perline) * line.quantity
                            line.price_subtotal = (line.harga_satuan - discount_perline) * line.quantity
                            line.price_unit = line.harga_satuan
                            if line.credit > 0:
                                line.credit = 0
                            if line.amount_currency < 0:
                                line.amount_currency = 0
                            if line.balance < 0 :
                                line.balance = 0
                        if move.move_type == 'out_refund' and line.sale_line_ids.id == False:
                            if len(line.product_id) > 0 and line.product_id.standard_price > 0:
                                # line.ati_price_unit = line.product_id.standard_price
                                string_id_new = str(line.id)
                                count_underscore = string_id_new.count('_')
                                if count_underscore == 0:
                                    self._cr.execute(
                                        """
                                            select ati_price_unit from account_move_line where id = {_id} 
                                        """.format(_id=line.id))
                                    check_price = self._cr.dictfetchall()
                                    line.ati_price_unit = check_price[0]['ati_price_unit']

                                    self._cr.execute(
                                        """
                                            select harga_satuan from account_move_line where id = {_id} 
                                        """.format(_id=line.id))
                                    check_harga_satuan = self._cr.dictfetchall()
                                    line.harga_satuan = check_harga_satuan[0]['harga_satuan']
                                # line.harga_satuan = line.ati_price_unit
                                # line.price_unit = line.harga_satuan
                            else:
                                string_id_new = str(line.id)
                                count_underscore = string_id_new.count('_')
                                if count_underscore == 0:
                                    self._cr.execute(
                                        """
                                            select ati_price_unit from account_move_line where id = {_id} 
                                        """.format(_id=line.id))
                                    check_price = self._cr.dictfetchall()
                                    line.ati_price_unit = check_price[0]['ati_price_unit']

                                    self._cr.execute(
                                        """
                                            select harga_satuan from account_move_line where id = {_id} 
                                        """.format(_id=line.id))
                                    check_harga_satuan = self._cr.dictfetchall()
                                    line.harga_satuan = check_harga_satuan[0]['harga_satuan']
                                # line.harga_satuan = line.ati_price_unit
                                # line.price_unit = line.harga_satuan
                            string_id_new = str(line.id)
                            count_underscore = string_id_new.count('_')
                            if count_underscore == 0:
                                # discount_perline = line.discount if line.discount_type == 'fixed' else line.harga_satuan * line.discount / 100.0
                                discount_perline = line.discount_amount
                                price_subtotal = (line.harga_satuan - discount_perline) * line.quantity
                                for tax_id in line.tax_ids:
                                    if 'ppn' in tax_id.name.lower():
                                        check_tax_ppn = tax_id.id
                                        # total_tax_ppn += invoice_line_id.price_subtotal * tax_id.amount / 100
                                        total_tax_ppn += price_subtotal * tax_id.amount / 100
                                    else:
                                        check_tax_pph = tax_id.id
                                        total_tax_pph += price_subtotal * tax_id.amount / 100
                            # discount_perline = line.discount if line.discount_type == 'fixed' else line.harga_satuan * line.discount / 100.0
                            discount_perline = line.discount_amount
                            line.debit = (line.harga_satuan - discount_perline) * line.quantity
                            line.price_subtotal = (line.harga_satuan - discount_perline) * line.quantity
                        if move.move_type == 'in_invoice' and not move.is_from_po:
                            ati_harga_unit = line.ati_price_unit
                            line_discount_1 = ati_harga_unit * line.discount_1 / 100.0 if line.discount_1 else 0.0
                            ati_harga_unit = ati_harga_unit - line_discount_1
                            line_discount_2 = ati_harga_unit * line.discount_2 / 100.0 if line.discount_2 else 0.0
                            ati_harga_unit = ati_harga_unit - line_discount_2
                            line_discount_3 = line.discount_3 if line.discount_3 else 0.0
                            ati_harga_unit = ati_harga_unit - line_discount_3
                            line_discount_4 = line.discount_4 if line.discount_4 else 0.0
                            ati_harga_unit = ati_harga_unit - line_discount_4
                            total_discount_line = (line_discount_1 + line_discount_2 + line_discount_3 + line_discount_4)
                            line.debit = ati_harga_unit * line.quantity
                            line.price_subtotal = ati_harga_unit * line.quantity
                            line.price_unit = line.ati_price_unit
                            if move.tax_helper_flag == True:
                                line.balance = line.price_subtotal + total_tax_ppn + total_tax_pph

                        total_untaxed += line.balance
                        total_untaxed_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                        total_discount += line.discount if line.discount_type == 'fixed' else line.quantity * line.price_unit * line.discount / 100.0

                        ''' #Putra Penambahan Discount 1, 2, 3, 4 untuk untuk total discount '''
                        # if move.move_type == 'in_invoice':
                        #     total_discount += line.quantity * line.price_unit * line.discount_1 / 100.0 if line.discount_1 else 0.0
                        #     total_discount += line.quantity * line.price_unit * line.discount_2 / 100.0 if line.discount_2 else 0.0
                        #     total_discount += line.discount_3 if line.discount_3 else 0.0
                        #     total_discount += line.discount_4 if line.discount_4 else 0.0
                    elif move.move_type == 'out_invoice' and move.is_from_so and line.exclude_from_invoice_tab and line.account_id.id == 851:
                        line.debit = total_discount_so_all
                    elif line.tax_line_id:
                        # Tax amount.
                        if move.move_type == 'in_invoice' and move.is_from_po:
                            po_origin = self.env['purchase.order'].search([('name', '=', move.invoice_origin)])
                            if po_origin:
                                for po in po_origin:
                                    if po.global_discount_type == 'percent':
                                        for po_line in po_origin.order_line:
                                            for tax_id in po_line.taxes_id:
                                                if tax_id.tax_group_id.name == 'PPN' and line.tax_group_id.id == tax_id.tax_group_id.id:
                                                    line.ati_amount_tax = total_untaxed * tax_id.amount / 100
                                                    line.price_unit = line.ati_amount_tax - (line.ati_amount_tax * po.global_order_discount / 100)
                                                if tax_id.tax_group_id.name == 'PPH 22' and line.tax_group_id.id == tax_id.tax_group_id.id:
                                                    line.ati_amount_tax = total_untaxed * tax_id.amount / 100
                                                    line.price_unit = line.ati_amount_tax - (line.ati_amount_tax * po.global_order_discount / 100)
                                            # line.ati_amount_tax = po.amount_untaxed * po_line.taxes_id.amount / 100
                                            # line.price_unit = line.ati_amount_tax - (line.ati_amount_tax*po.global_order_discount/100)
                                    elif po.global_discount_type == 'fixed':
                                        for po_line in po_origin.order_line:
                                            for tax_id in po_line.taxes_id:
                                                if tax_id.tax_group_id.name == 'PPN' and line.tax_group_id.id == tax_id.tax_group_id.id:
                                                    line.ati_amount_tax = (total_untaxed - po.global_order_discount) * tax_id.amount / 100
                                                    line.price_unit = line.ati_amount_tax
                                                if tax_id.tax_group_id.name == 'PPH 22' and line.tax_group_id.id == tax_id.tax_group_id.id:
                                                    line.ati_amount_tax = (total_untaxed - po.global_order_discount) * tax_id.amount / 100
                                                    line.price_unit = line.ati_amount_tax
                                            # line.ati_amount_tax = (po.amount_untaxed - po.global_order_discount) * po_line.taxes_id.amount / 100
                                            # line.price_unit = line.ati_amount_tax

                        elif move.move_type == 'out_invoice' and move.is_from_so:
                            if check_tax_ppn == line.tax_line_id.id:
                                line.price_unit = total_tax_ppn
                            elif check_tax_pph == line.tax_line_id.id:
                                line.price_unit = total_tax_pph
                            # so_origin = self.env['sale.order'].search([('name', '=', move.invoice_origin)])
                            # if so_origin:
                            #     for so in so_origin:
                            #         for so_line in so_origin.order_line:
                            #             total_tax_line = 0
                            #             for tax in so_line.tax_id:
                            #                 tax_line = tax.amount / 100
                            #                 total_tax_line += tax_line
                            #             if total_untaxed >= 0 :
                            #                 line.price_unit = (total_untaxed - so.global_discount) * total_tax_line
                            #             if total_untaxed < 0 :
                            #                 line.price_unit = ((-1 * total_untaxed) - so.global_discount) * total_tax_line

                        elif move.move_type == 'out_invoice' and not move.is_from_so:
                            if check_tax_ppn == line.tax_line_id.id:
                                line.price_unit = total_tax_ppn
                            elif check_tax_pph == line.tax_line_id.id:
                                line.price_unit = total_tax_pph
                        elif move.move_type == 'in_invoice' and not move.is_from_po:
                            if check_tax_ppn == line.tax_line_id.id:
                                line.price_unit = total_tax_ppn
                            elif check_tax_pph == line.tax_line_id.id:
                                line.price_unit = total_tax_pph
                        elif move.move_type == 'in_refund' and move.is_from_po == False and line.purchase_line_id.id==0:
                            # if check_tax_ppn == line.tax_line_id.id:
                            #     line.price_unit = total_tax_ppn
                            # elif check_tax_pph == line.tax_line_id.id:
                            #     line.price_unit = total_tax_pph
                            for tax_id in invoice_line_id.tax_ids:
                                if 'ppn' in tax_id.name.lower():
                                    check_tax_ppn = tax_id.id
                                    total_tax_ppn += invoice_line_id.price_subtotal * tax_id.amount / 100
                                else:
                                    check_tax_pph = tax_id.id
                                    total_tax_pph += invoice_line_id.price_subtotal * tax_id.amount / 100
                                if check_tax_ppn == line.tax_line_id.id:
                                    line.price_unit = total_tax_ppn
                                elif check_tax_pph == line.tax_line_id.id:
                                    line.price_unit = total_tax_pph
                        elif move.move_type == 'out_refund' and line.sale_line_ids.id == False:
                            for tax_id in line.tax_ids:
                                if 'ppn' in tax_id.name.lower():
                                    check_tax_ppn = tax_id.id
                                    total_tax_ppn += line.price_subtotal * tax_id.amount / 100
                                else:
                                    check_tax_pph = tax_id.id
                                    total_tax_pph += line.price_subtotal * tax_id.amount / 100
                            if check_tax_ppn == line.tax_line_id.id:
                                line.price_unit = total_tax_ppn
                            elif check_tax_pph == line.tax_line_id.id:
                                line.price_unit = total_tax_pph

                        # total_tax += line.balance
                        total_tax = line.price_unit
                        # total_tax_currency += line.amount_currency
                        total_tax_currency = line.price_unit
                        total += line.balance
                        # total = line.price_unit
                        total_currency += line.amount_currency
                        # total_currency = line.price_unit
                    elif line.is_global_line:
                        # Global Discount amount.
                        if move.move_type == 'in_invoice' and move.is_from_po:
                            po_origin = self.env['purchase.order'].search([('name', '=', move.invoice_origin)])
                            if po_origin:
                                for po in po_origin:
                                    if po.global_discount_type == 'percent':
                                        # line.price_unit = -1 * po.total_global_discount
                                        line.price_unit = -1 * (po.global_order_discount * total_untaxed / 100)
                                    elif po.global_discount_type == 'fixed':
                                        line.price_unit = -1 * (po.global_order_discount)

                        elif move.move_type == 'out_invoice' and move.is_from_so:
                            so_origin = self.env['sale.order'].search([('name', '=', move.invoice_origin)])
                            if so_origin:
                                for so in so_origin:
                                    line.price_unit = -1 * so.global_discount
                        # global_discount = line.balance
                        global_discount = line.price_unit
                        # global_discount_currency = line.amount_currency
                        global_discount_currency = line.price_unit
                        total += line.balance
                        # total = line.price_unit
                        total_currency += line.amount_currency
                        # total_currency = line.price_unit

                    elif line.account_id.user_type_id.type in ('receivable', 'payable'):

                        # Residual amount.
                        if move.move_type == 'in_invoice' and move.is_from_po:
                            line.price_unit = -1 * (round(total,2))

                        elif move.move_type == 'out_invoice' and move.is_from_so:
                            line.price_unit = round(total,2)


                            # so_origin = self.env['sale.order'].search([('name', '=', move.invoice_origin)])
                            # if so_origin:
                            #     for so in so_origin:
                            #         line.price_unit = -1 * so.amount_total

                        total_to_pay += line.balance
                        total_residual += line.amount_residual
                        total_residual_currency += line.amount_residual_currency
                else:
                    # === Miscellaneous journal entry ===
                    if line.debit:
                        total += line.balance
                        total_currency += line.amount_currency
            new_total_residual = False
            if move.tax_totals_json:
                json_object = json.loads(move.tax_totals_json)
                # changed by ibad
                for line in move.line_ids:
                    new_total_residual = -1 * line.amount_residual # json_object.get('amount_total')

            if move.move_type == 'entry' or move.is_outbound():
                sign = 1
            else:
                sign = -1
            total_global_discount = -1 * sign * (global_discount_currency if len(currencies) == 1 else global_discount)
            if total_global_discount:
                total_global_discount = total_global_discount
            else:
                total_global_discount = move.global_order_discount

            # total_discount += total_global_discount + total_discount_1_2_3_4
            total_discount += total_discount_1_2_3_4
            move.total_global_discount = total_global_discount

            if move.move_type == 'out_invoice' and move.is_from_so:
                move.total_discount = total_discount_so_all
            else:
                move.total_discount = total_discount
            move.amount_untaxed = sign * (total_untaxed_currency if len(currencies) == 1 else total_untaxed)
            move.amount_tax = sign * (total_tax_currency if len(currencies) == 1 else total_tax)
            # if move.tax_helper_flag == True:
            #     move.amount_tax = total_tax
            #     print(move.amount_tax)
            move.amount_total = sign * (total_currency if len(currencies) == 1 else total)
            new_amount_residual = 0
            if move.move_type == 'in_invoice':
                amount_residual = 0.0
                tax_totals_json = {}

                if move.tax_totals_json:
                    tax_totals_json = json.loads(move.tax_totals_json)

                # Cek jika ada PPH dalam groups_by_subtotal
                if 'groups_by_subtotal' in tax_totals_json:
                    untaxed_amount_group = tax_totals_json['groups_by_subtotal'].get('Untaxed Amount', [])

                    # Iterasi melalui grup PPH
                    for group in untaxed_amount_group:
                        if 'PPH' in group['tax_group_name']:
                            amount_residual += group['tax_group_amount']

                new_amount_residual = -1 * total_residual

                if amount_residual == 0.0:
                    move.amount_residual = new_amount_residual if new_amount_residual else 0
                elif amount_residual > 0.0:
                    if (new_amount_residual + amount_residual) != tax_totals_json.get('amount_total'):
                        move.amount_residual = tax_totals_json.get('amount_total')
                    else:
                        move.amount_residual = new_amount_residual + amount_residual if new_amount_residual else 0
                        move.amount_residual_signed = move.amount_residual
                        for line_ids in move.line_ids:
                            if move.partner_id.property_account_payable_id.id == line_ids.account_id.id:
                                line_ids.amount_residual = move.amount_residual
                                line_ids.amount_residual_currency = move.amount_residual
                                price_unit = line_ids.price_unit
                                price_unit = price_unit + (-1*amount_residual)
                                line_ids.write({'price_unit': price_unit})

            else:
                if move.move_type == 'out_invoice' and move.is_from_so != False:
                    move.amount_residual = -sign * (total_residual_currency if len(currencies) == 1 else total_residual) - move.global_order_discount
                else:
                    move.amount_residual = -sign * (total_residual_currency if len(currencies) == 1 else total_residual)

            move.amount_untaxed_signed = -total_untaxed
            move.amount_tax_signed = -total_tax
            move.amount_total_signed = abs(total) if move.move_type == 'entry' else -total
            move.amount_residual_signed = total_residual
            move.amount_total_in_currency_signed = abs(move.amount_total) if move.move_type == 'entry' else -(sign * move.amount_total)
            currency = currencies if len(currencies) == 1 else move.company_id.currency_id
            helper_amount_total = move.amount_total
            if move.tax_helper_flag == True and move.move_type == 'in_invoice':
                move.amount_total = helper_amount_total + total_tax_ppn + total_tax_pph

            # Compute 'payment_state'.
            new_pmt_state = 'not_paid' if move.move_type != 'entry' else False

            if move._payment_state_matters() and move.state == 'posted':
                if currency.is_zero(move.amount_residual):
                    reconciled_payments = move._get_reconciled_payments()
                    if not reconciled_payments or all(payment.is_matched for payment in reconciled_payments):
                        new_pmt_state = 'paid'
                    else:
                        new_pmt_state = move._get_invoice_in_payment_state()
                elif currency.compare_amounts(total_to_pay, total_residual) != 0:
                    new_pmt_state = 'partial'

            if new_pmt_state == 'paid' and move.move_type in ('in_invoice', 'out_invoice', 'entry'):
                reverse_type = move.move_type == 'in_invoice' and 'in_refund' or move.move_type == 'out_invoice' and 'out_refund' or 'entry'
                reverse_moves = self.env['account.move'].search([('reversed_entry_id', '=', move.id), ('state', '=', 'posted'), ('move_type', '=', reverse_type)])

                # We only set 'reversed' state in cas of 1 to 1 full reconciliation with a reverse entry; otherwise, we use the regular 'paid' state
                reverse_moves_full_recs = reverse_moves.mapped('line_ids.full_reconcile_id')
                if reverse_moves_full_recs.mapped('reconciled_line_ids.move_id').filtered(lambda x: x not in (reverse_moves + reverse_moves_full_recs.mapped('exchange_move_id'))) == move:
                    new_pmt_state = 'reversed'

            move.payment_state = new_pmt_state

            for line in move.line_ids:
                if move._payment_state_matters():
                    # === Invoices ===
                    if not line.exclude_from_invoice_tab:
                        # Untaxed amount.
                        if move.move_type == 'out_invoice' and move.is_from_so:
                            line.credit = line.harga_satuan * line.quantity
                            if line.discount_type == 'fixed':
                                # discount_invoice = line.discount
                                discount_invoice = line.sale_line_ids.discount_amount
                            elif line.discount_type == 'percent':
                                # discount_invoice = line.harga_satuan * line.discount / 100
                                discount_invoice = line.sale_line_ids.discount_amount
                            line.price_subtotal = (line.harga_satuan - discount_invoice) * line.quantity
                        if move.move_type == 'in_invoice' and move.is_from_po:
                            ati_harga_unit = line.ati_price_unit
                            line_discount_1 = ati_harga_unit * line.discount_1 / 100.0 if line.discount_1 else 0.0
                            ati_harga_unit = ati_harga_unit - line_discount_1
                            line_discount_2 = ati_harga_unit * line.discount_2 / 100.0 if line.discount_2 else 0.0
                            ati_harga_unit = ati_harga_unit - line_discount_2
                            line_discount_3 = line.discount_3 if line.discount_3 else 0.0
                            ati_harga_unit = ati_harga_unit - line_discount_3
                            line_discount_4 = line.discount_4 if line.discount_4 else 0.0
                            ati_harga_unit = ati_harga_unit - line_discount_4
                            total_discount_line = (line_discount_1 + line_discount_2 + line_discount_3 + line_discount_4)
                            line.debit = line.ati_price_unit * line.quantity
                            line.price_subtotal = ati_harga_unit * line.quantity
                            # line.debit = (line.ati_price_unit - total_discount_line) * line.quantity
                            # line.debit = line.ati_price_unit * line.quantity
                           # line.price_subtotal = (line.ati_price_unit - total_discount_line) * line.quantity
                if line.account_id.user_type_id.type in ('receivable', 'payable'):
                    if move.move_type == 'in_invoice' and move.is_from_po == False:
                        line.price_unit = move.amount_total_signed
                    elif move.move_type == 'in_refund' and line.purchase_line_id.id == 0:
                        if move.amount_total_signed > 0:
                            line.price_unit = -1 * move.amount_total_signed
                        else:
                            line.price_unit = move.amount_total_signed
                    elif move.move_type == 'out_invoice' and move.is_from_so == False:
                        if move.amount_total_signed > 0:
                            line.price_unit = -1 * move.amount_total_signed
                        else:
                            line.price_unit = move.amount_total_signed
                    elif move.move_type == 'out_refund' and line.sale_line_ids.id == False:
                        if move.amount_total_signed > 0:
                            line.price_unit = -1 * move.amount_total_signed
                        else:
                            line.price_unit = move.amount_total_signed
    total_global_discount = fields.Monetary(string='Total Global Discount',
        store=True, default=0, compute='_compute_amount')
    total_discount = fields.Monetary(string='Total Discount', store=True,
        default=0, compute='_compute_amount', tracking=True)
    global_discount_type = fields.Selection([('fixed', 'Fixed'),
                                             ('percent', 'Percent')],
                                            string="Discount Type", default="fixed", tracking=True)
    global_order_discount = fields.Float(string='Global Discount', store=True, tracking=True)
    amount_pph = fields.Monetary(string='PPH 22', tracking=True)
    is_from_po = fields.Boolean(string='Is From SO', default=False, copy=False)

    @api.onchange('global_discount_type', 'global_order_discount')
    def _onchange_global_order_discount(self):
        if not self.global_order_discount:
            global_discount_line = self.line_ids.filtered(lambda line: line.is_global_line)
            self.line_ids -= global_discount_line
        self._recompute_dynamic_lines()
        self._recompute_tax_lines()
        self._recompute_payment_terms_lines()

    def _recompute_global_discount_lines(self):
        ''' Compute the dynamic global discount lines of the journal entry.'''
        self.ensure_one()
        self = self.with_company(self.company_id)
        in_draft_mode = self != self._origin
        today = fields.Date.context_today(self)

        def _compute_payment_terms(self):
            sign = 1 if self.is_inbound() else -1

            IrConfigPrmtrSudo = self.env['ir.config_parameter'].sudo()
            discTax = IrConfigPrmtrSudo.get_param('account.global_discount_tax')
            if not discTax:
                discTax = 'untax'

            discount_balance = 0.0

            total = self.amount_untaxed
            if discTax == 'taxed':
                total += self.amount_tax

            if self.global_discount_type == 'fixed':
                discount_balance = sign * (self.global_order_discount or 0.0)
            else:
                discount_balance = sign * (total * (self.global_order_discount or 0.0) / 100)

            discount_amount_currency = discount_balance
            if self.currency_id != self.company_id.currency_id:
                discount_balance = self.currency_id._convert(
                    discount_amount_currency, self.company_id.currency_id, self.company_id, self.date)

            if self.invoice_payment_term_id:
                date_maturity = self.invoice_date or today
            else:
                date_maturity = self.invoice_date_due or self.invoice_date or today
            return [(date_maturity, discount_balance, discount_amount_currency)]

        def _compute_diff_global_discount_lines(self, existing_global_lines, account, to_compute):
            new_global_discount_lines = self.env['account.move.line']
            for date_maturity, balance, amount_currency in to_compute:
                if existing_global_lines:
                    candidate = existing_global_lines[0]
                    candidate.update({
                        'date_maturity': date_maturity,
                        'amount_currency': amount_currency,
                        'debit': balance > 0.0 and balance or 0.0,
                        'credit': balance < 0.0 and -balance or 0.0,
                    })
                else:
                    create_method = in_draft_mode and self.env['account.move.line'].new or self.env['account.move.line'].create
                    candidate = create_method({
                        'name': 'Global Discount',
                        'debit': balance > 0.0 and balance or 0.0,
                        'credit': balance < 0.0 and -balance or 0.0,
                        'quantity': 1.0,
                        'amount_currency': amount_currency,
                        'date_maturity': date_maturity,
                        'move_id': self.id,
                        'currency_id': self.currency_id.id if self.currency_id != self.company_id.currency_id else False,
                        'account_id': account.id,
                        'partner_id': self.commercial_partner_id.id,
                        'exclude_from_invoice_tab': True,
                        'is_global_line': True,
                    })
                new_global_discount_lines += candidate
                if in_draft_mode:
                    candidate.update(candidate._get_fields_onchange_balance())
            return new_global_discount_lines

        existing_global_lines = self.line_ids.filtered(lambda line: line.is_global_line)
        others_lines = self.line_ids.filtered(lambda line: not line.is_global_line)

        if not others_lines:
            self.line_ids -= existing_global_lines
            return

        if existing_global_lines:
            account = existing_global_lines[0].account_id
        else:
            IrConfigPrmtr = self.env['ir.config_parameter'].sudo()
            if self.move_type in ['out_invoice', 'out_refund', 'out_receipt']:
                account = self.env.company.discount_account_invoice
            else:
                account = self.env.company.discount_account_bill
            if not account:
                raise UserError(
                    _("Global Discount!\nPlease first set account for global discount in account setting."))

        to_compute = _compute_payment_terms(self)

        new_terms_lines = _compute_diff_global_discount_lines(self, existing_global_lines, account, to_compute)

        self.line_ids -= existing_global_lines - new_terms_lines

    def _recompute_dynamic_lines(self, recompute_all_taxes=False, recompute_tax_base_amount=False):
        ''' Recompute all lines that depend of others.

        For example, tax lines depends of base lines (lines having tax_ids set). This is also the case of cash rounding
        lines that depend of base lines or tax lines depending the cash rounding strategy. When a payment term is set,
        this method will auto-balance the move with payment term lines.

        :param recompute_all_taxes: Force the computation of taxes. If set to False, the computation will be done
                                    or not depending of the field 'recompute_tax_line' in lines.
        '''
        for invoice in self:
            if invoice.global_order_discount:
                invoice._recompute_global_discount_lines()
            # if invoice.global_order_discount:
                # Dispatch lines and pre-compute some aggregated values like taxes.
                for line in invoice.line_ids:
                    if line.recompute_tax_line:
                        recompute_all_taxes = True
                        line.recompute_tax_line = False

                # Compute taxes.
                if recompute_all_taxes:
                    invoice._recompute_tax_lines()
                if recompute_tax_base_amount:
                    invoice._recompute_tax_lines(recompute_tax_base_amount=True)

                if invoice.is_invoice(include_receipts=True):
                    # Compute cash rounding.
                    invoice._recompute_cash_rounding_lines()

                    # Compute global discount line.
                    # invoice._recompute_global_discount_lines()

                    # Compute payment terms.
                    invoice._recompute_payment_terms_lines()

                    # Only synchronize one2many in onchange.
                    if invoice != invoice._origin:
                        invoice.invoice_line_ids = invoice.line_ids.filtered(
                            lambda line: not line.exclude_from_invoice_tab)
            else:
                super(AccountMove, invoice)._recompute_dynamic_lines(
                    recompute_all_taxes=False, recompute_tax_base_amount=recompute_tax_base_amount)

    @api.depends('invoice_line_ids.total_tax')
    def _compute_total_tax(self):
        for this in self:
            total_tax = 0
            for line in this.invoice_line_ids:
                if line.total_tax:
                    total_tax += line.total_tax
            this.total_all_tax = round(total_tax,6)

    total_all_tax = fields.Float(string='Total Tax', compute=_compute_total_tax, store=True)

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    discount_type = fields.Selection([('fixed', 'Fixed'),
                                      ('percent', 'Percent')],
                                     string="Discount Type", default="percent")
    is_global_line = fields.Boolean(string='Global Discount Line',
        help="This field is used to separate global discount line.")

    @api.depends('move_id.global_order_discount','move_id.invoice_line_ids')
    def _compute_global_diskon_line(self):
        for this in self:
            # aml = self.env['stock.move.line'].sudo().search([('move_id', '=', this.id)
            if len(this.move_id.invoice_line_ids) > 0:
                global_diskon_line = this.move_id.global_order_discount / len(this.move_id.invoice_line_ids)
                this.global_diskon_line = global_diskon_line

    @api.depends('tax_ids','global_diskon_line')
    def _compute_tax_line(self):
        for this in self:
            tax_ids = []
            total_tax_perline = 0
            for tax in this.tax_ids:
                if tax.id not in tax_ids:
                    tax_per_line = (this.price_subtotal - this.global_diskon_line) * tax.amount / 100
                    total_tax_perline += tax_per_line
                    tax_ids.append(tax.id)
            this.total_tax = round(total_tax_perline,6)

    discount_1 = fields.Float(string='Discount 1 (Percent)')
    discount_2 = fields.Float(string='Discount 2 (Percent)')
    discount_3 = fields.Float(string='Discount 3 (Fixed Amount)')
    discount_4 = fields.Float(string='Discount 4 (Fixed Amount)')
    ati_price_unit = fields.Float(string='Unit Price', required=False, digits='Product Price')
    ati_amount_tax = fields.Float(string='Amount Tax')
    harga_satuan = fields.Float(string='Harga Satuan',digits='Product Price')
    price_unit_helper = fields.Float(default=0.0)
    harga_satuan_helper = fields.Float(default=0.0)
    tax_helper_ids = fields.Char(string='Taxes Helper')
    harga_ati = fields.Float(string='Harga Satuan', digits='Product Price')
    bantuan_ppn = fields.Boolean(string='Bantuan PPN',default=False)
    bantuan_pph = fields.Boolean(string='Bantuan PPN',default=False)
    total_tax = fields.Float(string='Total Tax', compute=_compute_tax_line, store=True)
    global_diskon_line = fields.Float(string='global_diskon_line', digits='Product Price', compute=_compute_global_diskon_line, store=True)
    # tax_helper_flag = fields.Boolean(string='Taxes Helper',default=False)

    @api.model_create_multi
    def create(self, vals_list):
        context = self._context.copy()
        res = super(AccountMoveLine, self).create(vals_list)
        context.update({'wk_vals_list': vals_list})

        # if context['import_file'] != True:
        if 'import_file' not in context:
            for rec in res:
                if rec.exclude_from_invoice_tab != True:
                    rec.price_subtotal = (rec.harga_satuan - rec.discount_amount) * rec.quantity
                if ((not rec.move_id.invoice_origin and not rec.move_id.is_from_so) or (not rec.move_id.invoice_origin and not rec.move_id.is_from_po)) and rec.exclude_from_invoice_tab != True:
                    price_unit = 0
                    new_list = []
                    for line in vals_list:
                        if 'exclude_from_invoice_tab' in line:
                            if line['exclude_from_invoice_tab'] !=True:
                                product_id = line['product_id']
                                price_unit = line['price_unit']
                                new_list.append({
                                    'product_id' : int(product_id),
                                    'price_unit' : price_unit
                                })
                    for item in new_list:
                        if rec.product_id.id == item['product_id']:
                            if ((rec.move_id.is_from_so == False and rec.move_id.move_type == 'out_invoice') or (rec.move_id.is_from_so == False and rec.move_id.move_type == 'out_refund')) and rec.exclude_from_invoice_tab != True:
                                if rec.product_id.standard_price:
                                    rec.price_unit = rec.product_id.standard_price
                                    rec.ati_price_unit = rec.product_id.standard_price
                                    if ((rec.move_id.is_from_so == False and rec.move_id.move_type == 'out_invoice') or (
                                            rec.move_id.is_from_so == False and rec.move_id.move_type == 'out_refund')) and rec.exclude_from_invoice_tab != True:
                                        rec.ati_price_unit = item['price_unit']
                                        if not rec.move_id.partner_id.margin_ids:
                                            if not rec.product_id.margin:
                                                rec.product_margin_percent = '0%'
                                            else:
                                                rec.product_margin_percent = str(rec.product_id.margin.name) + '%'
                                        else:
                                            margin_from_customer = 0
                                            for m_margin in rec.move_id.partner_id.margin_ids:
                                                margin_from_customer += m_margin.value
                                                rec.product_margin_percent = str(margin_from_customer) + '%'
                                        if rec.product_margin_percent:
                                            margin_percent = float(rec.product_margin_percent.strip('%'))
                                        else:
                                            margin_percent = 0
                                        rec.product_margin_amount = rec.ati_price_unit * margin_percent / 100

                                        harga_satuan = ((round(rec.ati_price_unit, 2)) + (
                                            round(rec.product_margin_amount, 2))) + \
                                                       (((round(rec.ati_price_unit, 2)) + (
                                                           round(rec.product_margin_amount, 2))) *
                                                        rec.additional_margin)

                                        pecahan = harga_satuan % 1
                                        satuan = harga_satuan - pecahan

                                        if pecahan > 0 or satuan > 0:
                                            harga_satuan_baru = math.ceil(harga_satuan / 50) * 50
                                            rec.harga_satuan = harga_satuan_baru
                                        else:
                                            harga_satuan_baru = harga_satuan
                                            rec.harga_satuan = harga_satuan_baru
                                else:
                                    rec.ati_price_unit = item['price_unit']
                                    rec.harga_satuan = rec.ati_price_unit
                            else:
                                rec.ati_price_unit = item['price_unit']
                                rec.harga_satuan = rec.ati_price_unit
                # if ((rec.move_id.is_from_so == False and rec.move_id.move_type == 'out_invoice') or (rec.move_id.is_from_so == False and rec.move_id.move_type == 'out_refund')) and rec.exclude_from_invoice_tab != True:
                #     # rec.ati_price_unit = item['price_unit']
                #     if not rec.move_id.partner_id.margin_ids:
                #         if not rec.product_id.margin:
                #             rec.product_margin_percent = '0%'
                #         else:
                #             rec.product_margin_percent = str(rec.product_id.margin.name) + '%'
                #     else:
                #         margin_from_customer = 0
                #         for m_margin in rec.move_id.partner_id.margin_ids:
                #             margin_from_customer += m_margin.value
                #             rec.product_margin_percent = str(margin_from_customer) + '%'
                #     if rec.product_margin_percent:
                #         margin_percent = float(rec.product_margin_percent.strip('%'))
                #     else:
                #         margin_percent = 0
                #     rec.product_margin_amount = rec.ati_price_unit * margin_percent / 100
                #
                #     harga_satuan = ((round(rec.ati_price_unit, 2)) + (round(rec.product_margin_amount, 2))) + \
                #                    (((round(rec.ati_price_unit, 2)) + (round(rec.product_margin_amount, 2))) *
                #                     rec.additional_margin)
                #
                #     pecahan = harga_satuan % 1
                #     satuan = harga_satuan - pecahan
                #
                #     if pecahan > 0 or satuan > 0:
                #         harga_satuan_baru = math.ceil(harga_satuan / 50) * 50
                #         rec.harga_satuan = harga_satuan_baru
                #     else:
                #         harga_satuan_baru = harga_satuan
                #         rec.harga_satuan = harga_satuan_baru
        else:
            for rec in res:
                if ((not rec.move_id.invoice_origin and not rec.move_id.is_from_so) or (not rec.move_id.invoice_origin and not rec.move_id.is_from_po)) and rec.exclude_from_invoice_tab != True:
                    price_unit = 0
                    new_list = []
                    for line in vals_list:
                        if 'exclude_from_invoice_tab' in line:
                            if line['exclude_from_invoice_tab'] !=True:
                                product_id = line['product_id']
                                price_unit = line['price_unit']
                                new_list.append({
                                    'product_id' : int(product_id),
                                    'price_unit' : price_unit
                                })
                    for item in new_list:
                        if rec.product_id.id == item['product_id']:
                            if ((rec.move_id.is_from_so == False and rec.move_id.move_type == 'out_invoice') or (rec.move_id.is_from_so == False and rec.move_id.move_type == 'out_refund')) and rec.exclude_from_invoice_tab != True:
                                if rec.product_id.standard_price:
                                    rec.price_unit = rec.product_id.standard_price
                                    rec.ati_price_unit = rec.product_id.standard_price
                                    if ((rec.move_id.is_from_so == False and rec.move_id.move_type == 'out_invoice') or (
                                            rec.move_id.is_from_so == False and rec.move_id.move_type == 'out_refund')) and rec.exclude_from_invoice_tab != True:
                                        rec.ati_price_unit = item['price_unit']
                                        if not rec.move_id.partner_id.margin_ids:
                                            if not rec.product_id.margin:
                                                rec.product_margin_percent = '0%'
                                            else:
                                                rec.product_margin_percent = str(rec.product_id.margin.name) + '%'
                                        else:
                                            margin_from_customer = 0
                                            for m_margin in rec.move_id.partner_id.margin_ids:
                                                margin_from_customer += m_margin.value
                                                rec.product_margin_percent = str(margin_from_customer) + '%'
                                        if rec.product_margin_percent:
                                            margin_percent = float(rec.product_margin_percent.strip('%'))
                                        else:
                                            margin_percent = 0
                                        rec.product_margin_amount = rec.ati_price_unit * margin_percent / 100

                                        harga_satuan = ((round(rec.ati_price_unit, 2)) + (
                                            round(rec.product_margin_amount, 2))) + \
                                                       (((round(rec.ati_price_unit, 2)) + (
                                                           round(rec.product_margin_amount, 2))) *
                                                        rec.additional_margin)

                                        pecahan = harga_satuan % 1
                                        satuan = harga_satuan - pecahan

                                        if pecahan > 0 or satuan > 0:
                                            harga_satuan_baru = math.ceil(harga_satuan / 50) * 50
                                            rec.harga_satuan = harga_satuan_baru
                                        else:
                                            harga_satuan_baru = harga_satuan
                                            rec.harga_satuan = harga_satuan_baru
                                else:
                                    rec.ati_price_unit = item['price_unit']
                                    rec.harga_satuan = rec.ati_price_unit
                            else:
                                rec.ati_price_unit = item['price_unit']
                                rec.harga_satuan = rec.ati_price_unit
            tax_helper = []
            total_tax_ppn = 0
            check_tax_ppn = 0
            total_tax_pph = 0
            check_tax_pph = 0
            for rec in res:
                rec.move_id.tax_helper_flag = True
                if rec.move_id.move_type == 'out_invoice' or rec.move_id.move_type == 'out_refund':
                    for tax_id in rec.tax_ids:
                        # discount_perline = rec.discount if rec.discount_type == 'fixed' else rec.harga_satuan * rec.discount / 100.0
                        discount_perline = rec.discount_amount
                        price_subtotal = (rec.harga_satuan - discount_perline) * rec.quantity
                        if 'ppn' in tax_id.name.lower():
                            check_tax_ppn = tax_id.id
                            total_tax_ppn += price_subtotal * tax_id.amount / 100
                        else:
                            check_tax_pph = tax_id.id
                            total_tax_pph += price_subtotal * tax_id.amount / 100
                # if rec.move_id.move_type == 'in_invoice':
                #     ati_harga_unit = rec.ati_price_unit
                #     line_discount_1 = ati_harga_unit * rec.discount_1 / 100.0 if rec.discount_1 else 0.0
                #     ati_harga_unit = ati_harga_unit - line_discount_1
                #     line_discount_2 = ati_harga_unit * rec.discount_2 / 100.0 if rec.discount_2 else 0.0
                #     ati_harga_unit = ati_harga_unit - line_discount_2
                #     line_discount_3 = rec.discount_3 if rec.discount_3 else 0.0
                #     ati_harga_unit = ati_harga_unit - line_discount_3
                #     line_discount_4 = rec.discount_4 if rec.discount_4 else 0.0
                #     ati_harga_unit = ati_harga_unit - line_discount_4
                #     total_discount_line = (line_discount_1 + line_discount_2 + line_discount_3 + line_discount_4)
                #     price_subtotal = ati_harga_unit * rec.quantity
                #     for tax_id in rec.tax_ids:
                #         if 'ppn' in tax_id.name.lower():
                #             check_tax_ppn = tax_id.id
                #             total_tax_ppn += price_subtotal * tax_id.amount / 100
                #         else:
                #             check_tax_pph = tax_id.id
                #             total_tax_pph += price_subtotal * tax_id.amount / 100

                    # tax_totals = json.loads(rec.move_id.tax_totals_json)
                    # for group in tax_totals['groups_by_subtotal']['Untaxed Amount']:
                    #     if total_tax_ppn > 0:
                    #         group['tax_group_amount'] = total_tax_ppn
                    #         group['formatted_tax_group_amount'] = "Rp\u00a0{:,.2f}".format(total_tax_ppn)
                    #         updated_tax_totals_json = json.dumps(tax_totals)
                    #         rec.move_id.write({'tax_totals_json': updated_tax_totals_json})
                    #         print(rec.move_id.tax_totals_json)
                    # for tax_id in rec.tax_ids:
                    #     if check_tax_ppn == tax_id.id:
                    #         credit = total_tax_ppn
                    #     else :
                    #         credit = total_tax_pph
                    #     new_aml_vals = {
                    #         'name': tax_id.name,
                    #         'display_type': False,
                    #         'quantity': 1,
                    #         'account_id': int(self.env['account.account'].sudo().search(
                    #             [('name', '=', 'VAT Sales')]).id) or None,
                    #         # 'product_uom_id': line.product_id.uom_id.id,
                    #         'debit': 0,
                    #         'credit': credit,
                    #         'parent_state': 'draft',
                    #         'company_id': rec.company_id.id,
                    #         'journal_id': rec.journal_id.id,
                    #         # 'analytic_account_id': self.analytic_account_id.id,
                    #         'exclude_from_invoice_tab': True,
                    #         # 'tax_tag_invert': invert,
                    #         'partner_id': rec.partner_id.id,
                    #         'move_id': rec.move_id.id,
                    #         'tax_line_id': tax_id.id,
                    #     }
                    #     new_aml_id = self.env['account.move.line'].sudo().create(new_aml_vals)
        return res

    def write(self, vals_list):
        context = self._context.copy()
        res = super(AccountMoveLine, self).write(vals_list)
        context.update({'wk_vals_list': vals_list})
        ati_price = ()
        for rec in self:
            if ((not rec.move_id.invoice_origin and not rec.move_id.is_from_so) or (not rec.move_id.invoice_origin and not rec.move_id.is_from_po)) and rec.exclude_from_invoice_tab != True:
                price_unit = 0
                new_list = []
                for line in vals_list:
                    if 'exclude_from_invoice_tab' in line:
                        if line['exclude_from_invoice_tab'] !=True:
                            product_id = line['product_id']
                            price_unit = line['price_unit']
                            new_list.append({
                                'product_id' : int(product_id),
                                'price_unit' : price_unit
                            })
                for item in new_list:
                    if rec.product_id.id == item['product_id']:
                        rec.price_unit = item['price_unit']
                        rec.ati_price_unit = item['price_unit']
                if rec.price_unit_helper != 0:
                    update = "update account_move_line set ati_price_unit = {_price}, price_unit_helper = 0 where id = {_id}".format(
                        _price=rec.price_unit_helper, _id=rec.id)
                    self._cr.execute(update)
                if rec.harga_satuan_helper != 0:
                    update = "update account_move_line set harga_satuan = {_harga}, harga_satuan_helper = 0 where id = {_id}".format(
                        _harga=rec.harga_satuan_helper, _id=rec.id)
                    self._cr.execute(update)
        return res

    @api.onchange('ati_price_unit')
    def func_onchange_ati_price_unit(self):
        if self._origin.id == False:
            self.price_unit_helper = self.ati_price_unit
        if self._origin.id != False:
            update = "update account_move_line set price_unit_helper = {_price} where id = {_id}".format(
                _price=self.ati_price_unit, _id=self._origin.id)
            self._cr.execute(update)
        if self.move_id.is_from_so == False and self.move_id.move_type == 'out_invoice':
            if not self.move_id.partner_id.margin_ids:
                if not self.product_id.margin:
                    self.product_margin_percent = '0%'
                else:
                    self.product_margin_percent = str(self.product_id.margin.name) + '%'
            else:
                margin_from_customer = 0
                for m_margin in self.move_id.partner_id.margin_ids:
                    margin_from_customer += m_margin.value
                    self.product_margin_percent = str(margin_from_customer) + '%'
            if self.product_margin_percent:
                margin_percent = float(self.product_margin_percent.strip('%'))
            else:
                margin_percent = 0
            self.product_margin_amount = self.ati_price_unit * margin_percent / 100

            if self._origin.id != False:
                update = "update account_move_line set product_margin_percent = '{_product_margin_percent}', product_margin_amount = {_product_margin_amount} where id = {_id}".format(
                    _product_margin_percent=self.product_margin_percent,_product_margin_amount=self.product_margin_amount, _id=self._origin.id)
                self._cr.execute(update)

            harga_satuan = ((round(self.ati_price_unit, 2)) + (round(self.product_margin_amount, 2))) + \
                           (((round(self.ati_price_unit, 2)) + (round(self.product_margin_amount, 2))) *
                            self.additional_margin)

            pecahan = harga_satuan % 1
            satuan = harga_satuan - pecahan

            if pecahan > 0 or satuan > 0:
                harga_satuan_baru = math.ceil(harga_satuan / 50) * 50
                self.harga_satuan = harga_satuan_baru
            else:
                harga_satuan_baru = harga_satuan
                self.harga_satuan = harga_satuan_baru
        elif self.move_id.is_from_so == False and self.move_id.move_type == 'out_refund':
            if not self.move_id.partner_id.margin_ids:
                if not self.product_id.margin:
                    self.product_margin_percent = '0%'
                else:
                    self.product_margin_percent = str(self.product_id.margin.name) + '%'
            else:
                margin_from_customer = 0
                for m_margin in self.move_id.partner_id.margin_ids:
                    margin_from_customer += m_margin.value
                    self.product_margin_percent = str(margin_from_customer) + '%'
            if self.product_margin_percent:
                margin_percent = float(self.product_margin_percent.strip('%'))
            else:
                margin_percent = 0
            self.product_margin_amount = self.ati_price_unit * margin_percent / 100

            if self._origin.id != False:
                update = "update account_move_line set product_margin_percent = '{_product_margin_percent}', product_margin_amount = {_product_margin_amount} where id = {_id}".format(
                    _product_margin_percent=self.product_margin_percent,_product_margin_amount=self.product_margin_amount, _id=self._origin.id)
                self._cr.execute(update)

            harga_satuan = ((round(self.ati_price_unit, 2)) + (round(self.product_margin_amount, 2))) + \
                           (((round(self.ati_price_unit, 2)) + (round(self.product_margin_amount, 2))) *
                            self.additional_margin)

            pecahan = harga_satuan % 1
            satuan = harga_satuan - pecahan

            if pecahan > 0 or satuan > 0:
                harga_satuan_baru = math.ceil(harga_satuan / 50) * 50
                self.harga_satuan = harga_satuan_baru
            else:
                harga_satuan_baru = harga_satuan
                self.harga_satuan = harga_satuan_baru

    @api.onchange('harga_satuan')
    def func_onchange_harga_satuan(self):
        if self._origin.id != False:
            update = "update account_move_line set harga_satuan_helper = {_harga} where id = {_id}".format(
                _harga=self.harga_satuan, _id=self._origin.id)
            self._cr.execute(update)

    @api.onchange('product_id')
    def func_onchange_product_id(self):
        if self.move_id.is_from_so == False and self.move_id.move_type == 'out_invoice':
            self.ati_price_unit = self.product_id.standard_price
        elif self.move_id.is_from_so == False and self.move_id.move_type == 'out_refund':
            self.ati_price_unit = self.product_id.standard_price
        elif self.move_id.is_from_po == False and self.move_id.move_type == 'in_invoice':
            self.ati_price_unit = self.product_id.hna
        elif self.move_id.is_from_po == False and self.move_id.move_type == 'in_refund':
            self.ati_price_unit = self.product_id.hna

        if self.move_id.is_from_so == False and self.move_id.move_type == 'out_invoice':
            if not self.move_id.partner_id.margin_ids:
                if not self.product_id.margin:
                    self.product_margin_percent = '0%'
                else:
                    self.product_margin_percent = str(self.product_id.margin.name) + '%'
            else:
                margin_from_customer = 0
                for m_margin in self.move_id.partner_id.margin_ids:
                    margin_from_customer += m_margin.value
                    self.product_margin_percent = str(margin_from_customer) + '%'
            if self.product_margin_percent:
                margin_percent = float(self.product_margin_percent.strip('%'))
            else:
                margin_percent = 0
            self.product_margin_amount = self.ati_price_unit * margin_percent / 100

            if self._origin.id != False:
                update = "update account_move_line set product_margin_percent = '{_product_margin_percent}', product_margin_amount = {_product_margin_amount} where id = {_id}".format(
                    _product_margin_percent=self.product_margin_percent,_product_margin_amount=self.product_margin_amount, _id=self._origin.id)
                self._cr.execute(update)
            harga_satuan = ((round(self.ati_price_unit, 2)) + (round(self.product_margin_amount, 2))) + \
                           (((round(self.ati_price_unit, 2)) + (round(self.product_margin_amount, 2))) *
                            self.additional_margin)

            pecahan = harga_satuan % 1
            satuan = harga_satuan - pecahan

            if pecahan > 0 or satuan > 0:
                harga_satuan_baru = math.ceil(harga_satuan / 50) * 50
                self.harga_satuan = harga_satuan_baru
            else:
                harga_satuan_baru = harga_satuan
                self.harga_satuan = harga_satuan_baru
        elif self.move_id.is_from_so == False and self.move_id.move_type == 'out_refund':
            if not self.move_id.partner_id.margin_ids:
                if not self.product_id.margin:
                    self.product_margin_percent = '0%'
                else:
                    self.product_margin_percent = str(self.product_id.margin.name) + '%'
            else:
                margin_from_customer = 0
                for m_margin in self.move_id.partner_id.margin_ids:
                    margin_from_customer += m_margin.value
                    self.product_margin_percent = str(margin_from_customer) + '%'
            if self.product_margin_percent:
                margin_percent = float(self.product_margin_percent.strip('%'))
            else:
                margin_percent = 0
            self.product_margin_amount = self.ati_price_unit * margin_percent / 100

            if self._origin.id != False:
                update = "update account_move_line set product_margin_percent = '{_product_margin_percent}', product_margin_amount = {_product_margin_amount} where id = {_id}".format(
                    _product_margin_percent=self.product_margin_percent,
                    _product_margin_amount=self.product_margin_amount, _id=self._origin.id)
                self._cr.execute(update)
            harga_satuan = ((round(self.ati_price_unit, 2)) + (round(self.product_margin_amount, 2))) + \
                           (((round(self.ati_price_unit, 2)) + (round(self.product_margin_amount, 2))) *
                            self.additional_margin)

            pecahan = harga_satuan % 1
            satuan = harga_satuan - pecahan

            if pecahan > 0 or satuan > 0:
                harga_satuan_baru = math.ceil(harga_satuan / 50) * 50
                self.harga_satuan = harga_satuan_baru
            else:
                harga_satuan_baru = harga_satuan
                self.harga_satuan = harga_satuan_baru



# class account_move_line(models.Model):
#     _inherit = 'account.move.line'
#
#     @api.onchange('ati_price_unit')
#     def func_onchange_ati_price_unit(self):
#         if self._origin.id != False:
#             update = "update account_move_line set price_unit_helper = {_price} where id = {_id}".format(_price=self.ati_price_unit,_id=self._origin.id)
#             self._cr.execute(update)
#
#     def write(self, vals):
#         res = super(account_move_line, self).write(vals)
#         if self.price_unit_helper != 0:
#             update = "update account_move_line set ati_price_unit = {_price}, harga_satuan = {_price}, price_unit_helper = 0 where id = {_id}".format(
#                 _price=self.price_unit_helper, _id=self.id)
#             self._cr.execute(update)
#
#         return res
#
#     price_unit_helper = fields.Float(default=0.0)

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"
    _description = "Sales Advance Payment Invoice"

    def _prepare_invoice_values(self, order, name, amount, so_line):
        invoice_vals = {
            'ref': order.client_order_ref,
            'move_type': 'out_invoice',
            'invoice_origin': order.name,
            'invoice_user_id': order.user_id.id,
            'narration': order.note,
            'partner_id': order.partner_invoice_id.id,
            'fiscal_position_id': (order.fiscal_position_id or order.fiscal_position_id.get_fiscal_position(order.partner_id.id)).id,
            'partner_shipping_id': order.partner_shipping_id.id,
            'currency_id': order.pricelist_id.currency_id.id,
            'payment_reference': order.reference,
            'invoice_payment_term_id': order.payment_term_id.id,
            'partner_bank_id': order.company_id.partner_id.bank_ids[:1].id,
            'team_id': order.team_id.id,
            'campaign_id': order.campaign_id.id,
            'medium_id': order.medium_id.id,
            'source_id': order.source_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': name,
                'price_unit': amount,
                'ati_price_unit': amount,
                'harga_satuan': amount,
                'quantity': 1.0,
                'product_id': self.product_id.id,
                'product_uom_id': so_line.product_uom.id,
                'tax_ids': [(6, 0, so_line.tax_id.ids)],
                'sale_line_ids': [(6, 0, [so_line.id])],
                'analytic_tag_ids': [(6, 0, so_line.analytic_tag_ids.ids)],
                'analytic_account_id': order.analytic_account_id.id or False,
            })],
        }

        return invoice_vals

    def _get_advance_details(self, order):
        context = {'lang': order.partner_id.lang}
        if self.advance_payment_method == 'percentage':
            # amount = order.amount_untaxed * self.amount / 100
            amount = order.amount_total * self.amount / 100
            name = _("Down payment of %s%%") % (self.amount)
        else:
            amount = self.fixed_amount
            name = _('Down Payment')
        del context

        return amount, name

    def create_invoices(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))

        if self.advance_payment_method == 'delivered':

            sale_orders._create_invoices(final=self.deduct_down_payments)

        else:
            # Create deposit product if necessary
            if not self.product_id:
                vals = self._prepare_deposit_product()
                self.product_id = self.env['product.product'].create(vals)
                self.env['ir.config_parameter'].sudo().set_param('sale.default_deposit_product_id', self.product_id.id)


            sale_line_obj = self.env['sale.order.line']
            for order in sale_orders:
                amount, name = self._get_advance_details(order)

                if self.product_id.invoice_policy != 'order':
                    raise UserError(_('The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
                if self.product_id.type != 'service':
                    raise UserError(_("The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
                taxes = self.product_id.taxes_id.filtered(lambda r: not order.company_id or r.company_id == order.company_id)
                tax_ids = order.fiscal_position_id.map_tax(taxes).ids
                analytic_tag_ids = []
                for line in order.order_line:
                    analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]

                so_line_values = self._prepare_so_line(order, analytic_tag_ids, tax_ids, amount)
                so_line = sale_line_obj.create(so_line_values)
                self._create_invoice(order, so_line, amount)


        # xxx
        if self._context.get('open_invoices', False):
            return sale_orders.action_view_invoice()
        return {'type': 'ir.actions.act_window_close'}

class sale_order(models.Model):
    _inherit = "sale.order"


    def _create_invoices(self, grouped=False, final=False, date=None):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        if not self.env['account.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                return self.env['account.move']

        # 1) Create invoices.
        invoice_vals_list = []
        invoice_item_sequence = 0 # Incremental sequencing to keep the lines order on the invoice.

        for order in self:
            order = order.with_company(order.company_id)
            current_section_vals = None
            down_payments = order.env['sale.order.line']

            invoice_vals = order._prepare_invoice()
            invoiceable_lines = order._get_invoiceable_lines(final)

            if not any(not line.display_type for line in invoiceable_lines):
                continue

            invoice_line_vals = []
            down_payment_section_added = False
            for line in invoiceable_lines:
                if not down_payment_section_added and line.is_downpayment:
                    # Create a dedicated section for the down payments
                    # (put at the end of the invoiceable_lines)
                    invoice_line_vals.append(
                        (0, 0, order._prepare_down_payment_section_line(
                            sequence=invoice_item_sequence,
                        )),
                    )
                    down_payment_section_added = True
                    invoice_item_sequence += 1
                invoice_line_vals.append(
                    (0, 0, line._prepare_invoice_line(
                        sequence=invoice_item_sequence,
                    )),
                )
                invoice_item_sequence += 1

            invoice_vals['invoice_line_ids'] += invoice_line_vals
            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise self._nothing_to_invoice_error()

        # 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
        if not grouped:
            new_invoice_vals_list = []
            invoice_grouping_keys = self._get_invoice_grouping_keys()
            invoice_vals_list = sorted(
                invoice_vals_list,
                key=lambda x: [
                    x.get(grouping_key) for grouping_key in invoice_grouping_keys
                ]
            )
            for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: [x.get(grouping_key) for grouping_key in invoice_grouping_keys]):
                origins = set()
                payment_refs = set()
                refs = set()
                ref_invoice_vals = None
                for invoice_vals in invoices:
                    if not ref_invoice_vals:
                        ref_invoice_vals = invoice_vals
                    else:
                        ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                    origins.add(invoice_vals['invoice_origin'])
                    payment_refs.add(invoice_vals['payment_reference'])
                    refs.add(invoice_vals['ref'])
                ref_invoice_vals.update({
                    'ref': ', '.join(refs)[:2000],
                    'invoice_origin': ', '.join(origins),
                    'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
                })
                new_invoice_vals_list.append(ref_invoice_vals)
            invoice_vals_list = new_invoice_vals_list

        if len(invoice_vals_list) < len(self):
            SaleOrderLine = self.env['sale.order.line']
            for invoice in invoice_vals_list:
                sequence = 1
                for line in invoice['invoice_line_ids']:
                    line[2]['sequence'] = SaleOrderLine._get_invoice_line_sequence(new=sequence, old=line[2]['sequence'])
                    sequence += 1

        # Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
        # sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.

        moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals_list)
        new_total_discount = 0
        # for line in moves.invoice_line_ids:
        #     if line.discount_type == 'fixed':
        #         new_discount = line.discount * line.quantity
        #     elif line.discount_type == 'percent':
        #         new_discount = (line.harga_satuan * line.discount / 100 ) * line.quantity
        #     new_total_discount += new_discount
        for line in self.order_line:
            new_discount = line.discount_amount * line.qty_delivered
            new_total_discount += new_discount
        if new_total_discount > 0:
            new_aml_vals = {
                'name': 'Sales Discount Item',
                'display_type': False,
                'quantity': 1,
                'account_id': int(self.env['ir.config_parameter'].sudo().search([('key', '=', 'discount_account_invoive.discount_item_account')]).value) or None,
                # 'product_uom_id': line.product_id.uom_id.id,
                'debit': new_total_discount,
                'credit': 0,
                'parent_state': 'draft',
                'company_id': self.company_id.id,
                'journal_id': self.env['account.journal'].sudo().search([('code', '=', 'INV'), ('type', '=', 'sale'), ('active','=',True)],
                                                                        limit=1).id,
                # 'analytic_account_id': self.analytic_account_id.id,
                'exclude_from_invoice_tab': True,
                # 'tax_tag_invert': invert,
                'partner_id': self.partner_id.id,
                'move_id': moves.id,
            }
            new_aml_id = self.env['account.move.line'].sudo().create(new_aml_vals)
        self._cr.execute("""
                           (select id from account_move order by id desc limit 1)
                           """)
        check_data1 = [x[0] for x in self._cr.fetchall()]

        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        if final:
            moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
        for move in moves:
            move.message_post_with_view('mail.message_origin_link',
                values={'self': move, 'origin': move.line_ids.mapped('sale_line_ids.order_id')},
                subtype_id=self.env.ref('mail.mt_note').id
            )
        # am_id = self.env['account.move'].sudo().search([('id','=',moves.id)])
        picking = self.env['stock.picking'].sudo().search([('sale_id', '=', self.id),('date_done', '!=', False)],order='id desc',limit=1)
        if picking.date_done:
            update_data = "update account_move set invoice_date = '{_effective_date}', date = '{_effective_date}' " \
                          "where move_type = 'out_invoice' and id = {_id}".format(_effective_date=picking.date_done,_id=moves.id)
            self._cr.execute(update_data)
            self._cr.commit()
        return moves

class res_config_settings(models.TransientModel):
    _inherit = 'res.config.settings'

    discount_item_account = fields.Many2one('account.account', string="Sales Discount Item", config_parameter='discount_account_invoive.discount_item_account')
    bill_discount_item_account = fields.Many2one('account.account', string="Purchase Discount Item",
                                            config_parameter='discount_account_invoive.bill_discount_item_account')

