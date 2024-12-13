from odoo import api, fields, models, _
from odoo.tools.misc import get_lang
import ast
import copy
import datetime
import io
import json
import logging
import markupsafe
from collections import defaultdict
from math import copysign, inf
import lxml.html
from babel.dates import get_quarter_names
from dateutil.relativedelta import relativedelta
from markupsafe import Markup

from odoo import models, fields, api, _
from odoo.addons.web.controllers.main import clean_action
from odoo.exceptions import RedirectWarning
from odoo.osv import expression
from odoo.tools import config, date_utils, get_lang
from odoo.tools.misc import formatLang, format_date
from odoo.tools.misc import xlsxwriter
import re

_logger = logging.getLogger(__name__)

class ReportAccountFinancialReport(models.Model):
    _inherit = 'account.financial.html.report'

    is_percentage = fields.Boolean(string='Percentage')


    # add header
    @api.model
    def _get_table(self, options):
        values = super(ReportAccountFinancialReport, self)._get_table(options)

        if self.is_percentage:
            values[0][0].insert(2, {
                'name': 'Percentage (%)',
                'class': 'number',
            })

        return values




    # add percent
    @api.model
    def _get_financial_line_report_line(self, options, financial_line, solver, groupby_keys):
        res = super(ReportAccountFinancialReport, self)._get_financial_line_report_line(options, financial_line, solver, groupby_keys)

        report_line = self.env['account.financial.html.report.line']

        if self.is_percentage:
            res['columns'].insert(1, {
                            'name': '', 
                            'divider': 0,
                            'class': 'number', 
                        })

            if financial_line.figure_type == 'float' and financial_line.divider_id:
                for line_div in solver._get_formula_results(financial_line.divider_id).values():
                    amount = res['columns'][0].get('no_format')
                    results = (amount / line_div) * 100
                    percentage = "{0:.2f}%".format(results)
                    res['columns'][1].update({
                        'name': percentage,
                        'divider': line_div
                    })

        return res


class inherit_account_cash_flow_reports(models.AbstractModel):
    _inherit = 'account.cash.flow.report'
    _description = 'Cash Flow Report'

    @api.model
    def _get_tags_per_account(self, options, tag_ids):
        ''' Compute a map account_id => tags used to dispatch the lines in the cash flow statement:
        operating, investing, financing or unclassified activities.

        This part is done in sql to avoid browsing and prefetching all account.account records.

        :param options: The report options.
        :param tag_ids: The ids of the 3 tags used by the cash flow: operating, investing and the financing tags.
        :return:        A map account_id => tag_ids set on this account.
        '''

        self._cr.execute("""(select a.id from account_account a
                                    where a.cashflow_report = True
                        )""")
        account_id_cashflow = [x[0] for x in self._cr.fetchall()]
        tags_per_accounts = {}

        query = '''
            SELECT
                DISTINCT account_account_id,
                ARRAY_AGG(account_account_tag_id)
            FROM account_account_account_tag
            WHERE account_account_tag_id IN %s
            GROUP BY account_account_id
        '''
        params = [tag_ids]

        self._cr.execute(query, params)
        for account_id, tags in self._cr.fetchall():
            if account_id in account_id_cashflow:
                tags_per_accounts[account_id] = tags
        return tags_per_accounts

    @api.model
    def _get_lines(self, options, line_id=None):

        def _insert_at_index(index, account_id, account_code, account_name, amount):
            ''' Insert the amount in the right section depending the line's index and the account_id. '''
            # Helper used to add some values to the report line having the index passed as parameter
            # (see _get_lines_to_compute).
            line = lines_to_compute[index]

            if self.env.company.currency_id.is_zero(amount):
                return

            line.setdefault('unfolded_lines', {})
            line['unfolded_lines'].setdefault(account_id, {
                'id': account_id,
                'name': '%s %s' % (account_code, account_name),
                'level': line['level'] + 1,
                'parent_id': line['id'],
                'columns': [{'name': 0.0, 'class': 'number'}],
                'caret_options': 'account.account',
            })
            line['columns'][0]['name'] += amount
            line['unfolded_lines'][account_id]['columns'][0]['name'] += amount

        def _dispatch_result(account_id, account_code, account_name, account_internal_type, amount):
            ''' Dispatch the newly fetched line inside the right section. '''
            self._cr.execute("""(select a.id from account_account a
                                    where a.cashflow_report = True
                                    )""")
            account_id_cashflow = [x[0] for x in self._cr.fetchall()]
            if account_id in account_id_cashflow:
                if account_internal_type == 'receivable':
                    # 'Advance Payments received from customers'                (index=3)
                    _insert_at_index(3, account_id, account_code, account_name, -amount)
                elif account_internal_type == 'payable':
                    # 'Advance Payments made to suppliers'                      (index=5)
                    _insert_at_index(5, account_id, account_code, account_name, -amount)
                elif amount < 0:
                    if tag_operating_id in tags_per_account.get(account_id, []):
                        # 'Cash received from operating activities'             (index=4)
                        _insert_at_index(4, account_id, account_code, account_name, -amount)
                    elif tag_investing_id in tags_per_account.get(account_id, []):
                        # 'Cash in for investing activities'                    (index=8)
                        _insert_at_index(8, account_id, account_code, account_name, -amount)
                    elif tag_financing_id in tags_per_account.get(account_id, []):
                        # 'Cash in for financing activities'                    (index=11)
                        _insert_at_index(11, account_id, account_code, account_name, -amount)
                    else:
                        # 'Cash in for unclassified activities'                 (index=14)
                        _insert_at_index(14, account_id, account_code, account_name, -amount)
                elif amount > 0:
                    if tag_operating_id in tags_per_account.get(account_id, []):
                        # 'Cash paid for operating activities'                  (index=6)
                        _insert_at_index(6, account_id, account_code, account_name, -amount)
                    elif tag_investing_id in tags_per_account.get(account_id, []):
                        # 'Cash out for investing activities'                   (index=9)
                        _insert_at_index(9, account_id, account_code, account_name, -amount)
                    elif tag_financing_id in tags_per_account.get(account_id, []):
                        # 'Cash out for financing activities'                   (index=12)
                        _insert_at_index(12, account_id, account_code, account_name, -amount)
                    else:
                        # 'Cash out for unclassified activities'                (index=15)
                        _insert_at_index(15, account_id, account_code, account_name, -amount)

        self.flush()

        unfold_all = self._context.get('print_mode') or options.get('unfold_all')
        currency_table_query = self.env['res.currency']._get_query_currency_table(options)
        lines_to_compute = self._get_lines_to_compute(options)

        tag_operating_id = self.env.ref('account.account_tag_operating').id
        tag_investing_id = self.env.ref('account.account_tag_investing').id
        tag_financing_id = self.env.ref('account.account_tag_financing').id
        tag_ids = (tag_operating_id, tag_investing_id, tag_financing_id)
        tags_per_account = self._get_tags_per_account(options, tag_ids)

        payment_move_ids, payment_account_ids = self._get_liquidity_move_ids(options)

        # Compute 'Cash and cash equivalents, beginning of period'      (index=0)
        beginning_period_options = self._get_options_beginning_period(options)
        for account_id, account_code, account_name, balance in self._compute_liquidity_balance(beginning_period_options,
                                                                                               currency_table_query,
                                                                                               payment_account_ids):
            _insert_at_index(0, account_id, account_code, account_name, balance)
            _insert_at_index(16, account_id, account_code, account_name, balance)

        # Compute 'Cash and cash equivalents, closing balance'          (index=16)
        for account_id, account_code, account_name, balance in self._compute_liquidity_balance(options,
                                                                                               currency_table_query,
                                                                                               payment_account_ids):
            _insert_at_index(16, account_id, account_code, account_name, balance)

        # ==== Process liquidity moves ====
        res = self._get_liquidity_move_report_lines(options, currency_table_query, payment_move_ids,
                                                    payment_account_ids)
        for account_id, account_code, account_name, account_internal_type, amount in res:
            _dispatch_result(account_id, account_code, account_name, account_internal_type, amount)

        # ==== Process reconciled moves ====
        res = self._get_reconciled_move_report_lines(options, currency_table_query, payment_move_ids,
                                                     payment_account_ids)
        for account_id, account_code, account_name, account_internal_type, balance in res:
            _dispatch_result(account_id, account_code, account_name, account_internal_type, balance)

        # 'Cash flows from operating activities'                            (index=2)
        lines_to_compute[2]['columns'][0]['name'] = \
            lines_to_compute[3]['columns'][0]['name'] + \
            lines_to_compute[4]['columns'][0]['name'] + \
            lines_to_compute[5]['columns'][0]['name'] + \
            lines_to_compute[6]['columns'][0]['name']
        # 'Cash flows from investing & extraordinary activities'            (index=7)
        lines_to_compute[7]['columns'][0]['name'] = \
            lines_to_compute[8]['columns'][0]['name'] + \
            lines_to_compute[9]['columns'][0]['name']
        # 'Cash flows from financing activities'                            (index=10)
        lines_to_compute[10]['columns'][0]['name'] = \
            lines_to_compute[11]['columns'][0]['name'] + \
            lines_to_compute[12]['columns'][0]['name']
        # 'Cash flows from unclassified activities'                         (index=13)
        lines_to_compute[13]['columns'][0]['name'] = \
            lines_to_compute[14]['columns'][0]['name'] + \
            lines_to_compute[15]['columns'][0]['name']
        # 'Net increase in cash and cash equivalents'                       (index=1)
        lines_to_compute[1]['columns'][0]['name'] = \
            lines_to_compute[2]['columns'][0]['name'] + \
            lines_to_compute[7]['columns'][0]['name'] + \
            lines_to_compute[10]['columns'][0]['name'] + \
            lines_to_compute[13]['columns'][0]['name']

        # ==== Compute the unexplained difference ====

        closing_ending_gap = lines_to_compute[16]['columns'][0]['name'] - lines_to_compute[0]['columns'][0]['name']
        computed_gap = sum(lines_to_compute[index]['columns'][0]['name'] for index in [2, 7, 10, 13])
        delta = closing_ending_gap - computed_gap
        if not self.env.company.currency_id.is_zero(delta):
            lines_to_compute.insert(16, {
                'id': 'cash_flow_line_unexplained_difference',
                'name': _('Unexplained Difference'),
                'level': 0,
                'columns': [{'name': delta, 'class': 'number'}],
            })

        # ==== Build final lines ====

        lines = []
        for line in lines_to_compute:
            unfolded_lines = line.pop('unfolded_lines', {})
            sub_lines = [unfolded_lines[k] for k in sorted(unfolded_lines)]

            line['unfoldable'] = len(sub_lines) > 0
            line['unfolded'] = line['unfoldable'] and (unfold_all or line['id'] in options['unfolded_lines'])

            # Header line.
            line['columns'][0]['name'] = self.format_value(line['columns'][0]['name'])
            lines.append(line)

            # Sub lines.
            for sub_line in sub_lines:
                sub_line['columns'][0]['name'] = self.format_value(sub_line['columns'][0]['name'])
                sub_line['style'] = '' if line['unfolded'] else 'display: none;'
                lines.append(sub_line)

            # Total line.
            if line['unfoldable']:
                lines.append({
                    'id': '%s_total' % line['id'],
                    'name': _('Total') + ' ' + line['name'],
                    'level': line['level'] + 1,
                    'parent_id': line['id'],
                    'columns': line['columns'],
                    'class': 'o_account_reports_domain_total',
                    'style': '' if line['unfolded'] else 'display: none;',
                })
        return lines


class ReportAccountFinancialReportLine(models.Model):
    _inherit = 'account.financial.html.report.line'

    divider_id = fields.Many2one(string='Divider', comodel_name='account.financial.html.report.line')
