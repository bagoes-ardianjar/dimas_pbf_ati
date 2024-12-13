# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = "account.move"

    name = fields.Char(compute="_compute_name_by_sequence")

    @api.depends("state", "journal_id", "date")
    def _compute_name_by_sequence(self):
        for move in self:
            name = move.name or "/"
            if (
                    move.state == "posted"
                    and (not move.name or move.name == "/")
                    and move.journal_id
                    and move.journal_id.sequence_id
            ):
                if (
                        move.move_type in ("out_refund", "in_refund")
                        and move.journal_id.type in ("sale", "purchase")
                        and move.journal_id.refund_sequence
                        and move.journal_id.refund_sequence_id
                ):
                    seq = move.journal_id.refund_sequence_id
                else:
                    seq = move.journal_id.sequence_id


                # new statement
                if move.invoice_date:
                    name = seq.next_by_id(sequence_date=move.invoice_date)

                    if name:
                        char_seq = name.split('/')

                        if len(char_seq) == 3:
                            name = f"{char_seq[0]}/{move.invoice_date.strftime('%m%y')}/{char_seq[-1]}"
                        else:
                            name = seq.next_by_id(sequence_date=move.date)    
                    else:
                        name = seq.next_by_id(sequence_date=move.date)
                        
                else:
                    name = seq.next_by_id(sequence_date=move.date)

            move.name = name

    def _constrains_date_sequence(self):
        return True