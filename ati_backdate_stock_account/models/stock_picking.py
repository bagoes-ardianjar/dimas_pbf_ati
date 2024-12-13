from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, AccessError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from collections import defaultdict
from itertools import groupby
from psycopg2 import OperationalError
from odoo.tools import OrderedSet
from odoo.tools.misc import formatLang, format_date, get_lang
import time
import calendar
import pytz
from datetime import datetime, timedelta, date


class Picking(models.Model):
    _inherit = 'stock.picking'
    

    def _action_done(self):
        """Call `_action_done` on the `stock.move` of the `stock.picking` in `self`.
        This method makes sure every `stock.move.line` is linked to a `stock.move` by either
        linking them to an existing one or a newly created one.

        If the context key `cancel_backorder` is present, backorders won't be created.

        :return: True
        :rtype: bool
        """
        self._check_company()

        todo_moves = self.mapped('move_lines').filtered(lambda self: self.state in ['draft', 'waiting', 'partially_available', 'assigned', 'confirmed'])
        for picking in self:
            if picking.owner_id:
                picking.move_lines.write({'restrict_partner_id': picking.owner_id.id})
                picking.move_line_ids.write({'owner_id': picking.owner_id.id})
        todo_moves._action_done(cancel_backorder=self.env.context.get('cancel_backorder'))
        for this in self:
            if not this.date_done:
                this.write({'date_done': fields.Datetime.now(), 'priority': '0'})

        # if incoming moves make other confirmed/partially_available moves available, assign them
        done_incoming_moves = self.filtered(lambda p: p.picking_type_id.code == 'incoming').move_lines.filtered(lambda m: m.state == 'done')
        done_incoming_moves._trigger_assign()

        for this in self:
            for stock_move_obj in this.move_lines:
                this.env.cr.execute(f"""UPDATE stock_move SET date = '{this.date_done}' WHERE id = {stock_move_obj.id}""")
                for stock_move_line_obj in stock_move_obj.move_line_ids:
                    this.env.cr.execute(f"""UPDATE stock_move_line SET date = '{this.date_done}' WHERE id = {stock_move_line_obj.id}""")
                for valuation in stock_move_obj.stock_valuation_layer_ids:
                    this.env.cr.execute(f"""UPDATE stock_valuation_layer SET create_date = '{this.date_done}' WHERE id = {valuation.id}""")

            for move_line in this.move_ids_without_package:
                for valuation_layer in move_line.stock_valuation_layer_ids:
                    if valuation_layer.account_move_id:
                        user_tz = this.env.user.tz or pytz.utc
                        local = pytz.timezone(user_tz)
                        display_date_result = datetime.strftime(pytz.utc.localize(datetime.strptime(str(this.date_done), DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local),"%Y-%m-%d")
                        valuation_layer.account_move_id.date = display_date_result or False

        self._send_confirmation_email()
        return True