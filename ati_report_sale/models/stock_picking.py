from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.addons import decimal_precision as dp


class StockPickingAdl(models.Model):
    _inherit = 'stock.picking'
    _description = 'Purchase Order'

    @api.model
    def create(self, vals):
        defaults = self.default_get(['name', 'picking_type_id'])
        picking_type = self.env['stock.picking.type'].browse(vals.get('picking_type_id', defaults.get('picking_type_id')))
        # print(picking_type, '=========================adel')
        if vals.get('name', '/') == '/' and defaults.get('name', '/') == '/' and vals.get('picking_type_id', defaults.get('picking_type_id')):
            if picking_type.name == 'Receipts':
                vals['name'] = self.env['ir.sequence'].next_by_code('x.self.re')
            if picking_type.name == 'Delivery Orders':
                vals['name'] = self.env['ir.sequence'].next_by_code('x.self.do')
            if picking_type.name == 'Returns':
                vals['name'] = self.env['ir.sequence'].next_by_code('x.self.rs')
            if picking_type.name == 'Return:Delivery Orders':
                vals['name'] = self.env['ir.sequence'].next_by_code('x.self.rc')
            if picking_type.name == 'Internal Transfers':
                vals['name'] = self.env['ir.sequence'].next_by_code('x.self.int.transfer')
            if picking_type.name == 'Receipts' and picking_type.warehouse_id.name == 'Karantina':
                vals['name'] = self.env['ir.sequence'].next_by_code('x.self.krn.receipts')
            if picking_type.name == 'Delivery Orders' and picking_type.warehouse_id.name == 'Karantina':
                vals['name'] = self.env['ir.sequence'].next_by_code('x.self.krn.do')
            if picking_type.name == 'Internal Transfers' and picking_type.warehouse_id.name == 'Karantina':
                vals['name'] = self.env['ir.sequence'].next_by_code('x.self.krn.int')

        # make sure to write `schedule_date` *after* the `stock.move` creation in
        # order to get a determinist execution of `_set_scheduled_date`
        scheduled_date = vals.pop('scheduled_date', False)
        res = super(StockPickingAdl, self).create(vals)
        if scheduled_date:
            res.with_context(mail_notrack=True).write({'scheduled_date': scheduled_date})
        res._autoconfirm_picking()

        # set partner as follower
        if vals.get('partner_id'):
            for picking in res.filtered(lambda p: p.location_id.usage == 'supplier' or p.location_dest_id.usage == 'customer'):
                picking.message_subscribe([vals.get('partner_id')])
        if vals.get('picking_type_id'):
            for move in res.move_lines:
                if not move.description_picking:
                    move.description_picking = move.product_id.with_context(lang=move._get_lang())._get_description(move.picking_id.picking_type_id)

        return res