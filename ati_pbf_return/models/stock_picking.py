from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Picking(models.Model):
    _inherit = 'stock.picking'

    is_return = fields.Boolean(string='is return')
    is_approval = fields.Boolean(string='is approval', compute='_set_approval')
    is_invoice = fields.Boolean(string='is invoice', compute='_get_invoice')

    # def action_confirm(self):
    #     self._check_company()
    #     self.mapped('package_level_ids').filtered(lambda pl: pl.state == 'draft' and not pl.move_ids)._generate_moves()
    #     # call `_action_confirm` on every draft move
    #     # self._cr.execute("""(
    #     #               select id from stock_move_line order by id desc limit 1
    #     #               )""")
    #     # check_data = [x[0] for x in self._cr.fetchall()]
    #     # print('check_data', check_data)
    #     context=self._context.copy()
    #     is_return=context.get('is_return',False)
    #     print('context',context)
    #     # line_return=context.get('line_return',[])
    #     # if is_return == True and len(line_return) > 0:
    #     #     for i in line_return:
    #     #         vals_move_line={
    #     #             'product_id':i['product_id'],
    #     #             'picking_id':self.id,
    #     #             'location_desc_id':
    #     #         }
    #     # else:
    #     self.mapped('move_lines')\
    #         .filtered(lambda move: move.state == 'draft')\
    #         ._action_confirm()
    #
    #     # self._cr.execute("""(
    #     #               select id from stock_move_line order by id desc limit 1
    #     #               )""")
    #     # check_data = [x[0] for x in self._cr.fetchall()]
    #     # print('check_data222', check_data)
    #
    #     # run scheduler for moves forecasted to not have enough in stock
    #     self.mapped('move_lines').filtered(lambda move: move.state not in ('draft', 'cancel', 'done'))._trigger_scheduler()
    #     return True

    def func_new_return(self):
        self._cr.execute("""
            (select product_id ,
                qty_done ,
                product_uom_id ,
                lot_id,
                move_id from stock_move_line where picking_id={_picking_id})""".format(_picking_id=self.id))
        data_move_line=self._cr.dictfetchall()
        vals_line=[]
        for i in data_move_line:
            vals_line.append((0,0,{
                'product_id':i['product_id'],
                'quantity_done':i['qty_done'],
                'uom_id':i['product_uom_id'],
                'lot_id':[(6,0,[i['lot_id']])] if i['lot_id'] else False or None,
                'move_id':i['move_id'],
                'to_refund': True
            }))
        if len(vals_line)>0:
            new_return_picking = self.env['stock.return.picking'].sudo().create({
                'original_location_id':self.location_id.id,
                'location_id':self.env['stock.location'].sudo().search([('complete_name','=','KRN/Stock')],limit=1).id or None,
                'parent_location_id':self.location_id.location_id.id,
                'picking_id':self.id,
                'product_return_moves':vals_line
            })
            form_view_id=self.env['ir.model.data']._xmlid_to_res_id('stock.view_stock_return_picking_form')
            return {
                'name':'Reverse Transfer',
                'view_type':'form',
                'view_mode':'form',
                'type':'ir.actions.act_window',
                'res_model':'stock.return.picking',
                'res_id':new_return_picking.id,
                'target':'new',
                'views':[[form_view_id,'form']]
            }

    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('waiting_approval', 'Waiting Approval'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, tracking=True,
        help=" * Draft: The transfer is not confirmed yet. Reservation doesn't apply.\n"
             " * Waiting another operation: This transfer is waiting for another operation before being ready.\n"
             " * Waiting: The transfer is waiting for the availability of some products.\n(a) The shipping policy is \"As soon as possible\": no product could be reserved.\n(b) The shipping policy is \"When all products are ready\": not all the products could be reserved.\n"
             " * Ready: The transfer is ready to be processed.\n(a) The shipping policy is \"As soon as possible\": at least one product has been reserved.\n(b) The shipping policy is \"When all products are ready\": all product have been reserved.\n"
             " * Done: The transfer has been processed.\n"
             " * Cancelled: The transfer has been cancelled.")



    def _get_invoice(self):
        inv = False
        if self.is_return and self.state == 'done':
            model = False
            if self.picking_type_id.code == 'outgoing':
                model = self.env['sale.order']
            elif self.picking_type_id.code == 'incoming':
                model = self.env['purchase.order']

            if self.group_id:
                inv_ids = model.search([('name', '=', self.group_id.name)]).invoice_ids
                if inv_ids:
                    invs = inv_ids.filtered(lambda x: x.state != 'posted')
                    if not invs:
                        inv = True
        self.is_invoice = inv


    # button submit for user
    def action_submit(self):
        if self.state == 'assigned' and self.is_return:
            if not self.apj:
                raise UserError('Anda belum menginput "APJ"')
            else:
                self.state = 'waiting_approval'


    # compare current user with user apj
    def _set_approval(self):
        user_id = self.apj.user_id
        current_user = self.env.user

        # user general
        if user_id and self.state == 'waiting_approval':
            if user_id.id == current_user.id:
                self.is_approval = True
            else:
                self.is_approval = False

        # user admin
        elif current_user.id == self.env.ref('base.user_admin').id:
                self.is_approval = True

        else:
            self.is_approval = False


    # write delivery status to Cancelled
    def action_cancel(self):
        res = super(Picking, self).action_cancel()
        for rec in self:
            rec.delivery_status = 'Cancelled'
        return res


    # write delivery status to False
    def action_picking_set_draft(self):
        res = super(Picking, self).action_picking_set_draft()
        for rec in self:
            rec.delivery_status = False
        return res