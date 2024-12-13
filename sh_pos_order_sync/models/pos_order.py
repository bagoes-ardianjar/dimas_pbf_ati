# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields, models, api, _
import logging

_logger = logging.getLogger(__name__)


class PosConfig(models.Model):
    _inherit = "pos.config"

    sh_nick_name = fields.Char(string="Nick Name")
    user_type = fields.Selection(
        [('send', 'Send'), ('receive', 'Receive'), ('both', 'Send / Receive')], string="User Type ")
    sh_allow_payment = fields.Boolean(string="Allow To Pay Order")
    sh_allow_edit = fields.Boolean(string="Allow To Edit Order")
    sh_allow_cancel = fields.Boolean(string="Allow To Cancel Order")
    sh_allow_multiple_selection = fields.Boolean(
        string="Allow Multiple Selection of Validator")
    
    def get_tables_order_count(self):
        result = super(PosConfig, self).get_tables_order_count()
        
        tables = self.env['restaurant.table'].search([('floor_id.pos_config_id', 'in', self.ids)])
        domain = [('state', '=', 'draft'), ('table_id', 'in', tables.ids), ('assigned_config','=',False)]

        order_stats = self.env['pos.order'].read_group(domain, ['table_id'], 'table_id')
        orders_map = dict((s['table_id'][0], s['table_id_count']) for s in order_stats)
        result = []
        for table in tables:
            result.append({'id': table.id, 'orders': orders_map.get(table.id, 0)})
        
        return result

class PosOrder(models.Model):
    _inherit = 'pos.order'
    
    
    
    @api.model
    def get_table_draft_orders(self, table_id):
        table_orders = super(PosOrder, self).get_table_draft_orders(table_id)
        sh_table_orders = []
        if table_orders and len(table_orders) > 0:
            for each_table_order in table_orders:
                if not each_table_order.get('assigned_config'):
                    sh_table_orders.append(each_table_order)
        return sh_table_orders
    
    def _get_fields_for_draft_order(self):
        fields = super(PosOrder, self)._get_fields_for_draft_order()
        fields.append('assigned_config')
        return fields

    def action_pos_order_paid(self):
        res = super(PosOrder, self).action_pos_order_paid()
        notifications = []
        assigned_config = []
        if self.assigned_config:
            for each_assigned_config in self.assigned_config:
                assigned_config.append(int(each_assigned_config.id))

            session_obj = self.env['pos.session'].search(
                [('config_id', 'in', assigned_config), ('state', '=', 'opened')])

            for each_session_user in session_obj.user_id:
                # if each_session_user.id != self.env.user.id:
                    notifications.append(
                        [(self._cr.dbname, 'order.pos', each_session_user.id), "sh_order_notification", {'paid_pos_order': self.read()}])
        notifications.append(
            [(self._cr.dbname, 'order.pos', self.user_id.id), "sh_order_notification", {'paid_pos_order': self.read()}])
        self.env['bus.bus']._sendmany(notifications)
        return res

    @api.model
    def _process_order(self, order, draft, existing_order):
        if order.get('data') and not order.get('data').get('statement_ids'):
            draft = True
        order_id = super(PosOrder, self)._process_order(
            order, draft, existing_order)
        order_obj = self.search([('id', '=', order_id)])
        notifications = []
        assigned_config = []
        if existing_order:
            if existing_order.state == 'draft':

                if order_obj.assigned_config:

                    for each_assigned_config in order_obj.assigned_config:

                        assigned_config.append(int(each_assigned_config.id))

                    session_obj = self.env['pos.session'].search(
                        [('config_id', 'in', assigned_config), ('state', '=', 'opened')])

                    for each_session_user in session_obj.user_id:
                        if each_session_user.id != self.env.user.id:
                            notifications.append(
                                [(self._cr.dbname, 'order.pos', each_session_user.id), "sh_order_notification", {'edit_pos_order': order_obj.read()}])
                notifications.append(
                    [(self._cr.dbname, 'order.pos', order_obj.user_id.id), "sh_order_notification", {'edit_pos_order': order_obj.read()}])

        else:
            if order_obj.state != 'cancel':
                if order_obj.assigned_config:

                    for each_assigned_config in order_obj.assigned_config:

                        assigned_config.append(int(each_assigned_config.id))

                    session_obj = self.env['pos.session'].search(
                        [('config_id', 'in', assigned_config), ('state', '=', 'opened')])

                    for each_session_user in session_obj.user_id:
                        if each_session_user.id != order_obj.user_id.id:
                            notifications.append(
                                [(self._cr.dbname, 'order.pos', each_session_user.id), "sh_order_notification", {'new_pos_order': order_obj.read()}])
                notifications.append(
                    [(self._cr.dbname, 'order.pos', order_obj.user_id.id), "sh_order_notification", {'new_pos_order': order_obj.read()}])

        self.env['bus.bus']._sendmany(notifications)
        return order_id

    @ api.model
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        res['assigned_config'] = ui_order.get('assigned_config', False)
        res['sh_is_order_send'] = ui_order.get('sh_is_order_send', False)
        return res

    @ api.model
    def cancel_order(self, order_id):
        order_obj = self.search([('sh_uid', '=', order_id)])
        order_obj.write({'state': 'cancel'})
        notifications = []
        assigned_config = []
        if order_obj.assigned_config:
            for each_assigned_config in order_obj.assigned_config:

                assigned_config.append(int(each_assigned_config.id))

            session_obj = self.env['pos.session'].search(
                [('config_id', 'in', assigned_config), ('state', '=', 'opened')])

            for each_session_user in session_obj.user_id:
                if each_session_user.id != self.env.user.id:
                    notifications.append(
                        [(self._cr.dbname, 'order.pos', each_session_user.id), "sh_order_notification", {'cancel_pos_order': order_obj.read()}])
        notifications.append(
            [(self._cr.dbname, 'order.pos', order_obj.user_id.id), "sh_order_notification", {'cancel_pos_order': order_obj.read()}])
        self.env['bus.bus']._sendmany(notifications)
        return True

    assigned_config = fields.Many2many("pos.config", string="Assigned Config ")
    sh_is_order_send = fields.Boolean()
