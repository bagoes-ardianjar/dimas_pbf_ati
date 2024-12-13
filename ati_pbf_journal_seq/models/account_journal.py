# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    sequence_id = fields.Many2one('ir.sequence', string='Entry Sequence', required=True, copy=False)
    refund_sequence_id = fields.Many2one('ir.sequence', string='Credit Note Entry Sequence', copy=False)


    @api.constrains("refund_sequence_id", "sequence_id")
    def _check_journal_sequence(self):
        for journal in self:
            if (
                    journal.refund_sequence_id
                    and journal.sequence_id
                    and journal.refund_sequence_id == journal.sequence_id
            ):
                raise ValidationError(
                    _(
                        "On journal '%s', the same sequence is used as "
                        "Entry Sequence and Credit Note Entry Sequence."
                    )
                    % journal.display_name
                )
            if journal.sequence_id and not journal.sequence_id.company_id:
                raise ValidationError(
                    _(
                        "The company is not set on sequence '%s' configured on "
                        "journal '%s'."
                    )
                    % (journal.sequence_id.display_name, journal.display_name)
                )
            if journal.refund_sequence_id and not journal.refund_sequence_id.company_id:
                raise ValidationError(
                    _(
                        "The company is not set on sequence '%s' configured as "
                        "credit note sequence of journal '%s'."
                    )
                    % (journal.refund_sequence_id.display_name, journal.display_name)
                )