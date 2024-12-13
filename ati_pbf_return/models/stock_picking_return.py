from odoo import api, fields, models, _


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'


    # set value for return picking
    def _prepare_picking_default_values(self):
        res = super(ReturnPicking, self)._prepare_picking_default_values()
        res.update({
            'is_return': True,
            'delivery_status': False
        })
        return res

    def _create_returns(self):
        # TODO sle: the unreserve of the next moves could be less brutal
        for return_move in self.product_return_moves.mapped('move_id'):
            return_move.move_dest_ids.filtered(lambda m: m.state not in ('done', 'cancel'))._do_unreserve()

        # create new picking for returned products
        new_picking = self.picking_id.copy(self._prepare_picking_default_values())
        picking_type_id = new_picking.picking_type_id.id
        new_picking.message_post_with_view('mail.message_origin_link',
            values={'self': new_picking, 'origin': self.picking_id},
            subtype_id=self.env.ref('mail.mt_note').id)
        returned_lines = 0
        for return_line in self.product_return_moves:
            if not return_line.move_id:
                raise UserError(_("You have manually created product lines, please delete them to proceed."))
            # TODO sle: float_is_zero?
            if return_line.quantity:
                returned_lines += 1
                vals = self._prepare_move_default_values(return_line, new_picking)
                r = return_line.move_id.copy(vals)
                vals = {}

                # +--------------------------------------------------------------------------------------------------------+
                # |       picking_pick     <--Move Orig--    picking_pack     --Move Dest-->   picking_ship
                # |              | returned_move_ids              ↑                                  | returned_move_ids
                # |              ↓                                | return_line.move_id              ↓
                # |       return pick(Add as dest)          return toLink                    return ship(Add as orig)
                # +--------------------------------------------------------------------------------------------------------+
                move_orig_to_link = return_line.move_id.move_dest_ids.mapped('returned_move_ids')
                # link to original move
                move_orig_to_link |= return_line.move_id
                # link to siblings of original move, if any
                move_orig_to_link |= return_line.move_id\
                    .mapped('move_dest_ids').filtered(lambda m: m.state not in ('cancel'))\
                    .mapped('move_orig_ids').filtered(lambda m: m.state not in ('cancel'))
                move_dest_to_link = return_line.move_id.move_orig_ids.mapped('returned_move_ids')
                # link to children of originally returned moves, if any. Note that the use of
                # 'return_line.move_id.move_orig_ids.returned_move_ids.move_orig_ids.move_dest_ids'
                # instead of 'return_line.move_id.move_orig_ids.move_dest_ids' prevents linking a
                # return directly to the destination moves of its parents. However, the return of
                # the return will be linked to the destination moves.
                move_dest_to_link |= return_line.move_id.move_orig_ids.mapped('returned_move_ids')\
                    .mapped('move_orig_ids').filtered(lambda m: m.state not in ('cancel'))\
                    .mapped('move_dest_ids').filtered(lambda m: m.state not in ('cancel'))
                vals['move_orig_ids'] = [(4, m.id) for m in move_orig_to_link]
                vals['move_dest_ids'] = [(4, m.id) for m in move_dest_to_link]
                r.write(vals)

                po_line_obj = move_orig_to_link.purchase_line_id
                if po_line_obj:
                    po_qty_received = po_line_obj.qty_received - return_line.quantity
                    po_line = "update purchase_order_line set qty_received = {_po_qty} where id = {_id}".format(
                        _po_qty=po_qty_received,
                        _id=move_orig_to_link.purchase_line_id.id
                    )
                    self._cr.execute(po_line)
                    self._cr.commit()

        if not returned_lines:
            raise UserError(_("Please specify at least one non-zero quantity."))

        # self._cr.execute("""(
        #             select a.purchase_line_id ,
        #             a.sale_line_id
        #             from stock_move a
        #             join stock_return_picking_line b on b.move_id=a.id
        #             join stock_return_picking c on c.id=b.wizard_id
        #             where b.wizard_id = {_id}
        #         )""".format(_id=self.id))
        # data_return = self._cr.dictfetchall()
        self._cr.execute("""(
            select
            (select x.id from sale_order x where x.id = c.order_id) as so,
            (select y.id from purchase_order y where y.id = d.order_id) as po
            from stock_move b
            left join sale_order_line c on c.id = b.sale_line_id 
            left join purchase_order_line d on d.id = b.purchase_line_id 
            where b.picking_id = {_picking}
            group by so, po 
        )""".format(_picking=new_picking.id))
        fet_data_check = self._cr.dictfetchall()
        if fet_data_check[0]['so'] != None and fet_data_check[0]['po'] == None:
            self._cr.execute("""(
                                select
                                a.product_id,
                                b.location_id,
                                c.stock_production_lot_id,
                                a.quantity,
                                e.uom_id,
                                b.picking_id,
                                a.move_id
                                from stock_return_picking_line a
                                join stock_return_picking b on b.id=a.wizard_id 
                                left join stock_production_lot_stock_return_picking_line_rel c on c.stock_return_picking_line_id = a.id
                                join product_product d on d.id=a.product_id
                                join product_template e on e.id=d.product_tmpl_id
                                where a.wizard_id = {_id}
                            )""".format(_id=self.id))
            data_return_line = self._cr.dictfetchall()
            new_picking.with_context(is_return=True, line_return=data_return_line).action_confirm()
            new_picking.action_assign()
            delete_data = "delete from stock_move_line where picking_id={_new_picking}".format(
                _new_picking=new_picking.id)
            self._cr.execute(delete_data)
            self._cr.commit()
            dict_sml = {}
            for i in data_return_line:
                sm_return = self.env['stock.move'].search([('picking_id', '=', new_picking.id),
                                                           ('product_id', '=', i['product_id'])])
                sm_id = 0
                for sm in sm_return:
                    sm_id = sm.id
                vals_stock_move_line = {
                    'product_id': i['product_id'],
                    'location_id': new_picking.location_id.id,
                    'location_dest_id': i['location_id'],
                    'picking_id': new_picking.id,
                    'lot_id': i['stock_production_lot_id'],
                    'qty_done': i['quantity'],
                    'product_uom_id': i['uom_id'],
                    'move_id': sm_id,
                    # 'move_id': sm_return.id,
                    # 'product_uom_qty':i['quantity']
                    'state': 'assigned',
                }
                new_stock_move_line = self.env['stock.move.line'].sudo().create(vals_stock_move_line)
                if new_stock_move_line.id not in dict_sml:
                    dict_sml[new_stock_move_line.id] = i['quantity']
            delete_data = "delete from stock_move_line where picking_id={_new_picking} and qty_done=0".format(
                _new_picking=new_picking.id)
            self._cr.execute(delete_data)
            self._cr.commit()

            delete_data = "delete from stock_move where picking_id={_new_picking} and product_uom_qty = 0".format(
                _new_picking=new_picking.id)
            self._cr.execute(delete_data)
            self._cr.commit()

            for u in dict_sml:
                update_data = "update stock_move_line set qty_done = 0, product_uom_qty = {_product_uom_qty} " \
                              "where id = {_id}".format(_product_uom_qty=dict_sml[u], _id=u)
                self._cr.execute(update_data)

            return new_picking.id, picking_type_id
        elif fet_data_check[0]['so'] == None and fet_data_check[0]['po'] != None:
            self._cr.execute("""(
                            select
                            a.product_id,
                            b.location_id,
                            c.stock_production_lot_id,
                            a.quantity,
                            e.uom_id,
                            b.picking_id,
                            a.move_id
                            from stock_return_picking_line a
                            join stock_return_picking b on b.id=a.wizard_id
                            left join stock_production_lot_stock_return_picking_line_rel c on c.stock_return_picking_line_id = a.id
                            join product_product d on d.id=a.product_id
                            join product_template e on e.id=d.product_tmpl_id
                            where a.wizard_id = {_id}
                        )""".format(_id=self.id))
            data_return_line = self._cr.dictfetchall()
            new_picking.with_context(is_return=True, line_return=data_return_line).action_confirm()
            new_picking.action_assign()
            delete_m2m = "delete from batch_on_location_id_rel_move_line where stock_move_line_id in " \
                         "(select id from stock_move_line where picking_id = {_pick})".format(_pick=new_picking.id)
            self._cr.execute(delete_m2m)
            delete_data = "delete from stock_move_line where picking_id={_new_picking}".format(
                _new_picking=new_picking.id)
            self._cr.execute(delete_data)
            self._cr.commit()
            dict_sml = {}
            list_no_sm = []
            for i in data_return_line:
                sm_return = self.env['stock.move'].search([('picking_id', '=', new_picking.id),
                                                           ('product_id', '=', i['product_id'])])

                sm_id = 0
                for sm in sm_return:
                    sm_id = sm.id
                vals_stock_move_line = {
                    'product_id': i['product_id'],
                    'location_id': new_picking.location_id.id,
                    'location_dest_id': i['location_id'],
                    'picking_id': new_picking.id,
                    'lot_id': i['stock_production_lot_id'] or False,
                    'qty_done': i['quantity'],
                    'product_uom_id': i['uom_id'],
                    # 'move_id': sm_return.id,
                    'move_id': sm_id,
                    # 'product_uom_qty':i['quantity']
                    'state': 'assigned',
                }
                new_stock_move_line = self.env['stock.move.line'].sudo().create(vals_stock_move_line)
                if new_stock_move_line.id not in dict_sml:
                    dict_sml[new_stock_move_line.id] = i['quantity']
                    list_no_sm.append(new_stock_move_line.id)
            list_no_sm.append(0)
            list_no_sm.append(0)
            delete_m2m = "delete from batch_on_location_id_rel_move_line where stock_move_line_id in " \
                         "(select id from stock_move_line where picking_id = {_pick}) " \
                         "and stock_move_line_id not in {_no_sm}".format(_pick=new_picking.id,_no_sm=tuple(list_no_sm))
            self._cr.execute(delete_m2m)
            delete_data = "delete from stock_move_line where picking_id={_new_picking} and qty_done=0".format(
                _new_picking=new_picking.id)
            self._cr.execute(delete_data)
            self._cr.commit()

            delete_data = "delete from stock_move where picking_id={_new_picking} and product_uom_qty = 0".format(
                _new_picking=new_picking.id)
            self._cr.execute(delete_data)
            self._cr.commit()

            for u in dict_sml:
                update_data = "update stock_move_line set qty_done = 0, product_uom_qty = {_product_uom_qty} " \
                              "where id = {_id}".format(_product_uom_qty=dict_sml[u], _id=u)
                self._cr.execute(update_data)
            return new_picking.id, picking_type_id
        else:
            new_picking.action_confirm()
            new_picking.action_assign()
            return new_picking.id, picking_type_id
