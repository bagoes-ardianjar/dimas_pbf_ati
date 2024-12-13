# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd. - ©
# Technaureus Info Solutions Pvt. Ltd 2022. All rights reserved.
import json

from odoo import fields, models, api
from itertools import groupby


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _prepare_stock_move_vals_combo(self, first_line, order_lines, combo_line, qty):
        quantity = combo_line.qty * qty
        return {
            'name': first_line.name,
            'product_uom': combo_line.product_uom_id.id,
            'picking_id': self.id,
            'picking_type_id': self.picking_type_id.id,
            'product_id': combo_line.product_id.id,
            'product_uom_qty': quantity,
            'state': 'draft',
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'company_id': self.company_id.id,
        }

    def _create_move_from_pos_order_lines(self, lines):
        self.ensure_one()
        prdct = lines.mapped('combo_product_ids')
        if len(prdct):
            lines_by_product = groupby(sorted(lines, key=lambda l: l.product_id.id), key=lambda l: l.product_id.id)
            move_vals = []
            for dummy, olines in lines_by_product:
                order_lines = self.env['pos.order.line'].concat(*olines)
                if order_lines.combo_product_ids:
                    qty = order_lines.qty
                    for combo_line in order_lines.combo_product_ids:
                        move_vals.append(self._prepare_stock_move_vals_combo(order_lines[0], order_lines, combo_line, qty))
                else:
                    move_vals.append(self._prepare_stock_move_vals(order_lines[0], order_lines))
            moves = self.env['stock.move'].create(move_vals)
            confirmed_moves = moves._action_confirm()
            confirmed_moves._add_mls_related_to_order(lines, are_qties_done=True)

        else:
            return super(StockPicking, self)._create_move_from_pos_order_lines(lines)


