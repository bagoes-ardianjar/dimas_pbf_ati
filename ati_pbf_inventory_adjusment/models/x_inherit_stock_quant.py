from email.policy import default
from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero

class X_inherit_stock_quant(models.Model):
    _inherit = 'stock.quant'
    _description = ''

    def _delete_double_sm(self):
        delete_data = "delete from stock_move where product_uom_qty = 0"
        self._cr.execute(delete_data)
        self._cr.commit()

    @api.depends()
    def _compute_current_user(self):
        for partner in self:
            partner.current_user = self.env.user

    def get_location_helper_ids(self):
        for this in self:
            if this.product_id:
                self._cr.execute("""(
                    select b.id from stock_putaway_rule a
                    join stock_location b on b.id = a.location_out_id
                    where a.product_id = {_product_id}
                )""".format(_product_id=this.product_id.id))
                fet = [x[0] for x in self._cr.fetchall()]
                this.location_helper_ids = [(6, 0, fet)]
    #
    @api.onchange('product_id')
    def func_onchange_product_id(self):
        self.get_location_helper_ids()
        for this in self:
            check_batch = self.env['stock.putaway.rule'].sudo().search(
                [('product_id', '=', this.product_id.id)], limit=1)
            if check_batch.location_out_id:
                this.location_id = check_batch.location_out_id
            # if len(self.location_helper_ids) == 1:
            #     this.location_id = this.location_helper_ids[0]
            check_batch = self.env['stock.production.lot'].sudo().search(
                [('product_id', '=', this.product_id.id)])
            if len(check_batch) == 1:
                this.lot_id = check_batch.id
    #
    @api.onchange('lot_id')
    def func_onchange_lot_id(self):
        for this in self:
            if this.lot_id:
                # if this.lot_id.expiration_date:
                this.sq_expiration_date = this.lot_id.expiration_date
    #
    @api.onchange('expiration_date_batch')
    def func_onchange_expiration_date_batch(self):
        for this in self:
            if this.expiration_date_batch:
                this.sq_expiration_date = this.expiration_date_batch
    #
    @api.onchange('sq_expiration_date')
    def func_onchange_sq_expiration_date(self):
        for this in self:
            if this.lot_id:
                check_batch = self.env['stock.production.lot'].sudo().search(
                    [('id', '=', this.lot_id.id)])
                check_batch.expiration_date = this.sq_expiration_date
                # if this.sq_expiration_date:
                #     update_data = "update stock_production_lot set expiration_date = '{_sq_expiration_date}' " \
                #                   "where id = {_id}".format(_id=this.lot_id.id,
                #                                             _sq_expiration_date=this.sq_expiration_date)
                #     self._cr.execute(update_data)
                #     self._cr.commit()

    @api.model
    def _get_inventory_fields_create(self):
        """ Returns a list of fields user can edit when he want to create a quant in `inventory_mode`.
        """
        return ['product_id', 'location_id', 'lot_id', 'package_id', 'owner_id',
                'sq_expiration_date'] + self._get_inventory_fields_write()

    @api.depends('current_user')
    def get_is_invisible_btn_approve(self):
        for this in self:
            self._cr.execute("""
                        select b.uid from res_groups a
                        join res_groups_users_rel b on b.gid = a.id 
                        where lower(a.name) = 'akses approve inventory adjustment'
                        """)
            fet_user = self._cr.fetchall()
            akses_approve = [uid[0] for uid in fet_user]
            if this.current_user.id in akses_approve:
                this.invisible_btn_approve = False
            else:
                this.invisible_btn_approve = True


    location_helper_ids = fields.Many2many('stock.location', 'stock_quant_location_id_rel',
                                          'stock_quant_id',
                                          'location_id',
                                          compute=get_location_helper_ids)
    current_user = fields.Many2one('res.users', string="Current User", compute='_compute_current_user')
    invisible_btn_approve = fields.Boolean(string='Invisible Button Approve', default=True, compute=get_is_invisible_btn_approve)
    sq_expiration_date = fields.Datetime(string='Expiration Date')
    x_adjustment_reason = fields.Char(string="Adjusment Reasons")
    expiration_date_batch = fields.Datetime(related="lot_id.expiration_date", string='Expiration Date', readonly=True,)
    riil_quantity = fields.Float(
        'Riil Quantity', digits='Product Unit of Measure',
        help="Quantity of products in this quant, in the default unit of measure of the product")
    cat_quantity = fields.Float(
        'Cat Quantity', digits='Product Unit of Measure',
        help="The product's counted quantity.")

    def _apply_inventory(self):
        for rec in self:
            onhand_before = rec.quantity
            user_before = rec.user_id
            res = super(X_inherit_stock_quant, self)._apply_inventory()
            user = user_before.id if user_before else self.env.user.id
            rec.write({'user_id': user, 'x_adjustment_reason': rec.x_adjustment_reason, 'riil_quantity': rec.quantity, 'cat_quantity': onhand_before})
        return res

    @api.onchange('inventory_quantity')
    def _onchange_inventory_quantity(self):
        for rec in self:
            if rec.inventory_quantity and rec.inventory_quantity_set:
                rec.riil_quantity = rec.inventory_quantity
            if rec.location_id and rec.location_id.usage == 'inventory':
                warning = {
                    'title': _('You cannot modify inventory loss quantity'),
                    'message': _(
                        'Editing quantities in an Inventory Adjustment location is forbidden,'
                        'those locations are used as counterpart when correcting the quantities.'
                    )
                }
                return {'warning': warning}

    @api.onchange('quantity')
    def _onchange_quantity(self):
        for rec in self:
            if rec.quantity and rec.inventory_quantity_set:
                rec.cat_quantity = rec.quantity

    @api.model
    def create(self, vals):
        res = super(X_inherit_stock_quant, self).create(vals)
        # print("vals", vals)
        if 'x_adjustment_reason' in vals:
            if vals['x_adjustment_reason']:
                res.x_adjustment_reason = vals['x_adjustment_reason']
        for rec in res:
            if rec.quantity and rec.inventory_quantity_set:
                rec.cat_quantity = rec.quantity
            if rec.inventory_quantity and rec.inventory_quantity_set:
                rec.riil_quantity = rec.inventory_quantity
        return res

    # @api.onchange('inventory_diff_quantity')
    # def _onchange_counted_quant(self):

    #     for q in self:
    #         if q.inventory_diff_quantity:
    #             q.inventory_quantity = q.quantity + q.inventory_diff_quantity
    #             adj_obj = self.env['stock.quant'].sudo().search([('id', '=', self._origin.id)])
    #             adj_obj.inventory_quantity = q.quantity + q.inventory_diff_quantity

    # @api.model
    # def create(self, vals):
    #     """ Override to handle the "inventory mode" and create a quant as
    #     superuser the conditions are met.
    #     """
    #     if self._is_inventory_mode() and any(f in vals for f in ['inventory_diff_quantity', 'inventory_quantity_auto_apply']):
    #         allowed_fields = self._get_inventory_fields_create()
    #         if any(field for field in vals.keys() if field not in allowed_fields):
    #             print(vals.keys())
    #             raise UserError(_("Quant's creation is restricted, you can't do this operation."))

    #         inventory_diff_quantity = vals.pop('inventory_diff_quantity', False) or 0
    #         # Create an empty quant or write on a similar one.
    #         product = self.env['product.product'].browse(vals['product_id'])
    #         location = self.env['stock.location'].browse(vals['location_id'])
    #         lot_id = self.env['stock.production.lot'].browse(vals.get('lot_id'))
    #         package_id = self.env['stock.quant.package'].browse(vals.get('package_id'))
    #         owner_id = self.env['res.partner'].browse(vals.get('owner_id'))
    #         quant = self._gather(product, location, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=True)

    #         if quant:
    #             quant = quant[0].sudo()
    #             print('tzzzzz')
    #         else:
    #             quant = self.sudo().create(vals)
    #         # Set the `inventory_quantity` field to create the necessary move.
    #         quant.inventory_quantity = inventory_diff_quantity
    #         quant.inventory_diff_quantity = inventory_diff_quantity
    #         print('tessss')
    #         quant.user_id = vals.get('user_id', self.env.user.id)
    #         quant.inventory_date = fields.Date.today()

    #         return quant
    #     res = super(X_inherit_stock_quant, self).create(vals)
    #     if self._is_inventory_mode():
    #         res._check_company()
    #     return res

    # def action_apply_inventory(self):
    #     products_tracked_without_lot = []
    #     for quant in self:
    #         rounding = quant.product_uom_id.rounding
    #         if fields.Float.is_zero(quant.inventory_diff_quantity, precision_rounding=rounding)\
    #                 and fields.Float.is_zero(quant.inventory_quantity, precision_rounding=rounding)\
    #                 and fields.Float.is_zero(quant.quantity, precision_rounding=rounding):
    #             continue
    #         if quant.product_id.tracking in ['lot', 'serial'] and\
    #                 not quant.lot_id and quant.inventory_quantity != quant.quantity:
    #             products_tracked_without_lot.append(quant.product_id.id)
    #     # for some reason if multi-record, env.context doesn't pass to wizards...
    #     ctx = dict(self.env.context or {})
    #     ctx['default_quant_ids'] = self.ids
    #     quants_outdated = self.filtered(lambda quant: quant.is_outdated)
    #     if quants_outdated:
    #         ctx['default_quant_to_fix_ids'] = quants_outdated.ids
    #         for quant in self:
    #             quant.inventory_quantity = quant.quantity + quant.inventory_diff_quantity
    #     if products_tracked_without_lot:
    #         ctx['default_product_ids'] = products_tracked_without_lot
    #         return {
    #             'name': _('Tracked Products in Inventory Adjustment'),
    #             'type': 'ir.actions.act_window',
    #             'view_mode': 'form',
    #             'views': [(False, 'form')],
    #             'res_model': 'stock.track.confirmation',
    #             'target': 'new',
    #             'context': ctx,
    #         }
    #     self._apply_inventory()
    #     self.inventory_quantity_set = False

    # def action_set_inventory_quantity(self):
    #     quants_already_set = self.filtered(lambda quant: quant.inventory_quantity_set)
    #     if quants_already_set:
    #         ctx = dict(self.env.context or {}, default_quant_ids=self.ids)
    #         view = self.env.ref('stock.inventory_warning_set_view', False)
    #         return {
    #             'name': _('Quantities Already Set'),
    #             'type': 'ir.actions.act_window',
    #             'view_mode': 'form',
    #             'views': [(view.id, 'form')],
    #             'view_id': view.id,
    #             'res_model': 'stock.inventory.warning',
    #             'target': 'new',
    #             'context': ctx,
    #         }
    #     for quant in self:
    #         quant.inventory_quantity = quant.quantity + quant.inventory_diff_quantity 
    #         # quant.inventory_quantity = quant.quantity
    #     self.user_id = self.env.user.id
    #     self.inventory_quantity_set = True
    #     self.inventory_quantity = quant.quantity + quant.inventory_diff_quantity

    @api.model
    def _get_inventory_fields_write(self):
        """ Returns a list of fields user can edit when he want to edit a quant in `inventory_mode`.
        """
        fields = ['inventory_quantity', 'inventory_quantity_auto_apply', 'inventory_diff_quantity', 'accounting_date',
                  'inventory_date', 'user_id', 'inventory_quantity_set', 'is_outdated', 'x_adjustment_reason', 'riil_quantity', 'cat_quantity']
        return fields
        # self.inventory_diff_quantity = 0
    # inventory_diff_quantity = fields.Float(
    #     'Difference', help="Indicates the gap between the product's theoretical quantity and its counted quantity.",
    #     digits='Product Unit of Measure')

    def _apply_inventory(self):
        move_vals = []
        if not self.user_has_groups('stock.group_stock_manager'):
            raise UserError(_('Only a stock manager can validate an inventory adjustment.'))
        for quant in self:
            # Create and validate a move so that the quant matches its `inventory_quantity`.
            if float_compare(quant.inventory_diff_quantity, 0, precision_rounding=quant.product_uom_id.rounding) > 0:
                move_vals.append(
                    quant._get_inventory_move_values(quant.inventory_diff_quantity,
                                                     quant.product_id.with_company(quant.company_id).property_stock_inventory,
                                                     quant.location_id))
            else:
                move_vals.append(
                    quant._get_inventory_move_values(-quant.inventory_diff_quantity,
                                                     quant.location_id,
                                                     quant.product_id.with_company(quant.company_id).property_stock_inventory,
                                                     out=True))
        filtered_data = [item for item in move_vals if item['product_uom_qty'] != 0 and item['product_uom_qty'] != -0.0]
        moves = self.env['stock.move'].with_context(inventory_mode=False).create(filtered_data)
        moves._action_done()
        self.location_id.write({'last_inventory_date': fields.Date.today()})
        date_by_location = {loc: loc._get_next_inventory_date() for loc in self.mapped('location_id')}
        for quant in self:
            quant.inventory_date = date_by_location[quant.location_id]
        self.write({'inventory_quantity': 0, 'user_id': False})
        self.write({'inventory_diff_quantity': 0})