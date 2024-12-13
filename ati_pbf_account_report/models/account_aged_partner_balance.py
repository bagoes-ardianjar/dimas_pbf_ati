from odoo import api, fields, models, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta




class ReportAccountAgedPartner(models.AbstractModel):
    _inherit = 'account.aged.partner'
    
    deadline = fields.Char(string='Deadline')


    # added new column
    @api.model
    def _get_column_details(self, options):
        columns = super(ReportAccountAgedPartner, self)._get_column_details(options)

        if self._name in ['account.aged.receivable', 'account.aged.payable']:
            columns[1:1] = [self._field_column('deadline')]

        return columns



    # inherit rewrite query
    @api.model
    def _get_sql(self):
        options = self.env.context['report_options']
        query = ("""
            SELECT
                {move_line_fields},
                account_move_line.amount_currency as amount_currency,
                account_move_line.partner_id AS partner_id,
                partner.name AS partner_name,
                COALESCE(trust_property.value_text, 'normal') AS partner_trust,
                COALESCE(account_move_line.currency_id, journal.currency_id) AS report_currency_id,
                account_move_line.payment_id AS payment_id,
                COALESCE(account_move_line.date_maturity, account_move_line.date) AS report_date,
                account_move_line.expected_pay_date AS expected_pay_date,
                move.move_type AS move_type,
                move.name AS move_name,
                move.ref AS move_ref,
                CASE 
                    WHEN account_move_line.date_maturity IS NOT NULL
                    THEN (account_move_line.date_maturity::date - CURRENT_DATE::date) || ' Hari'
                    ELSE (move.invoice_date_due::date - CURRENT_DATE::date) || ' Hari' END deadline,
                account.code || ' ' || account.name AS account_name,
                account.code AS account_code,""" + ','.join([("""
                CASE WHEN period_table.period_index = {i}
                THEN %(sign)s * ROUND((
                    account_move_line.balance - COALESCE(SUM(part_debit.amount), 0) + COALESCE(SUM(part_credit.amount), 0)
                ) * currency_table.rate, currency_table.precision)
                ELSE 0 END AS period{i}""").format(i=i) for i in range(6)]) + """
            FROM account_move_line
            JOIN account_move move ON account_move_line.move_id = move.id
            JOIN account_journal journal ON journal.id = account_move_line.journal_id
            JOIN account_account account ON account.id = account_move_line.account_id
            LEFT JOIN res_partner partner ON partner.id = account_move_line.partner_id
            LEFT JOIN ir_property trust_property ON (
                trust_property.res_id = 'res.partner,'|| account_move_line.partner_id
                AND trust_property.name = 'trust'
                AND trust_property.company_id = account_move_line.company_id
            )
            JOIN {currency_table} ON currency_table.company_id = account_move_line.company_id
            LEFT JOIN LATERAL (
                SELECT part.amount, part.debit_move_id
                FROM account_partial_reconcile part
                WHERE part.max_date <= %(date)s
            ) part_debit ON part_debit.debit_move_id = account_move_line.id
            LEFT JOIN LATERAL (
                SELECT part.amount, part.credit_move_id
                FROM account_partial_reconcile part
                WHERE part.max_date <= %(date)s
            ) part_credit ON part_credit.credit_move_id = account_move_line.id
            JOIN {period_table} ON (
                period_table.date_start IS NULL
                OR COALESCE(account_move_line.date_maturity, account_move_line.date) <= DATE(period_table.date_start)
            )
            AND (
                period_table.date_stop IS NULL
                OR COALESCE(account_move_line.date_maturity, account_move_line.date) >= DATE(period_table.date_stop)
            )
            WHERE account.internal_type = %(account_type)s
            AND account.exclude_from_aged_reports IS NOT TRUE
            GROUP BY account_move_line.id, partner.id, deadline, trust_property.id, journal.id, move.id, account.id, period_table.period_index, currency_table.rate, currency_table.precision
            HAVING ROUND(account_move_line.balance - COALESCE(SUM(part_debit.amount), 0) + COALESCE(SUM(part_credit.amount), 0), currency_table.precision) != 0
        """).format(
            move_line_fields=self._get_move_line_fields('account_move_line'),
            currency_table=self.env['res.currency']._get_query_currency_table(options),
            period_table=self._get_query_period_table(options),
        )
        params = {
            'account_type': options['filter_account_type'],
            'sign': 1 if options['filter_account_type'] == 'receivable' else -1,
            'date': options['date']['date_to'],
        }
        return self.env.cr.mogrify(query, params).decode(self.env.cr.connection.encoding)