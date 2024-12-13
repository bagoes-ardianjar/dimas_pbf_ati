# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
from odoo import fields, models, api


class ShKeyboardKey(models.Model):
    _name = 'sh.keyboard.key'
    _description = 'keyboard Key'

    name = fields.Char(string="Key")


class ShKeyboardKeyTemp(models.Model):
    _name = 'sh.keyboard.key.temp'
    _description = 'keyboard Key Temp'

    sh_key_ids = fields.Many2one('sh.keyboard.key', string="Keys ")
    name = fields.Char(string="Display Key")
    sh_pos_key_ids = fields.Many2one('sh.pos.keyboard.shortcut', string="Keys")

    @api.model
    def create(self, vals):
        res = super(ShKeyboardKeyTemp, self).create(vals)
        name = ""
        if res.sh_key_ids:
            for each_key in res.sh_key_ids:
                if name != "":
                    name = name + "+" + each_key.name
                else:
                    name = each_key.name
        res.write({'name': name})

        return res


class ShPosKeyboardShortcut(models.Model):
    _name = 'sh.pos.keyboard.shortcut'
    _description = 'keyboard Key Shortcut'

    payment_config_id = fields.Many2one('pos.config')
    config_id = fields.Many2one('pos.config')
    payment_method_id = fields.Many2one('pos.payment.method')
    sh_key_ids = fields.One2many(
        'sh.keyboard.key.temp', 'sh_pos_key_ids', string="Keys")
    sh_payment_shortcut_screen_type = fields.Selection(
        [('payment_screen', 'Payment Screen')], string="Shortcut Screen Type", default="payment_screen")
    sh_shortcut_screen_type = fields.Selection([('payment_screen', 'Payment Screen'), ('product_screen', 'Product Screen'), (
        'customer_screen', 'Customer Screen'), ('receipt_screen', 'Receipt Screen'), ('order_screen', 'Order Screen'), ('all', 'All')], string="Shortcut Screen Type ")
    sh_shortcut_screen = fields.Selection([('go_payment_screen', 'Go to Payment Screen'), ('go_customer_Screen', 'Go to Customer Screen'), ('go_order_Screen', 'Go to Order Screen'), ('validate_order', 'Validate Order'), ('next_order', 'Next Order'), ('go_to_previous_screen', 'Go to Previous Screen'), ('select_quantity_mode', 'Select Quantity Mode'), ('select_discount_mode', 'Select Discount Mode'), ('select_price_mode', 'Select Price Mode'), ('search_product', 'Search Product'), ('search_order', 'Search Order'), ('add_new_order', 'Add New Order'), ('destroy_current_order', 'Destroy Order'), ('delete_orderline', 'Delete OrderLine'), ('select_up_orderline', 'Select Up OrderLine'), ('select_down_orderline', 'Select Down OrderLine'), ('search_customer', 'Search Customer'), ('select_up_customer', 'Select Up Customer'), ('select_down_customer', 'Select Down Customer'), ('set_customer', 'Set Customer'), ('edit_customer', 'Edit Customer'), ('save_customer', 'Save Customer'), ('create_customer', 'Create Customer'), ('delete_payment_line', 'Delete Payment Line'), ('select_up_payment_line', 'Select Up Payment Line'), ('select_down_payment_line', 'Select Down Payment Line'), ('+10', '+10'), ('+20', '+20'), ('+50', '+50'), ('select_down_order', 'Select Down Order'), ('select_up_order', 'Select Up Order'), ('select_order', 'Select Order')],
                                          string="Shortcut Screen")


class PosConfig(models.Model):
    _inherit = 'pos.config'
#
    sh_enable_shortcut = fields.Boolean(string="Enable Shortcut Key")
    sh_shortcut_keys_screen = fields.One2many(
        'sh.pos.keyboard.shortcut', 'config_id', string="POS Shortcut Key")
    sh_payment_shortcut_keys_screen = fields.One2many(
        'sh.pos.keyboard.shortcut', 'payment_config_id', string="POS Payment Method Shortcut Key")

    @api.model
    def default_get(self, fields):
        res = super(PosConfig, self).default_get(fields)
        key_list = []
        vals = []

        key_id = self.env.ref('sh_pos_keyboard_shortcut.sh_keyboard_key_shift')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        key_id = self.env.ref('sh_pos_keyboard_shortcut.sh_keyboard_key_P')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': 'go_payment_screen',
                            'sh_shortcut_screen_type': 'payment_screen', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        key_id = self.env.ref(
            'sh_pos_keyboard_shortcut.sh_keyboard_key_control')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        key_id = self.env.ref('sh_pos_keyboard_shortcut.sh_keyboard_key_c')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': 'go_customer_Screen',
                            'sh_shortcut_screen_type': 'all', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        key_id = self.env.ref('sh_pos_keyboard_shortcut.sh_keyboard_key_shift')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        key_id = self.env.ref('sh_pos_keyboard_shortcut.sh_keyboard_key_G')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': 'go_order_Screen',
                            'sh_shortcut_screen_type': 'product_screen', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        key_id = self.env.ref('sh_pos_keyboard_shortcut.sh_keyboard_key_v')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': 'validate_order',
                            'sh_shortcut_screen_type': 'payment_screen', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        key_id = self.env.ref('sh_pos_keyboard_shortcut.sh_keyboard_key_n')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': 'next_order',
                            'sh_shortcut_screen_type': 'receipt_screen', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        key_id = self.env.ref(
            'sh_pos_keyboard_shortcut.sh_keyboard_key_escape')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': 'go_to_previous_screen',
                            'sh_shortcut_screen_type': 'all', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        key_id = self.env.ref('sh_pos_keyboard_shortcut.sh_keyboard_key_q')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': 'select_quantity_mode',
                            'sh_shortcut_screen_type': 'product_screen', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        key_id = self.env.ref('sh_pos_keyboard_shortcut.sh_keyboard_key_d')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': 'select_discount_mode',
                            'sh_shortcut_screen_type': 'product_screen', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        key_id = self.env.ref('sh_pos_keyboard_shortcut.sh_keyboard_key_p')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': 'select_price_mode',
                            'sh_shortcut_screen_type': 'product_screen', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        key_id = self.env.ref('sh_pos_keyboard_shortcut.sh_keyboard_key_f')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': 'search_product',
                            'sh_shortcut_screen_type': 'product_screen', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        key_id = self.env.ref('sh_pos_keyboard_shortcut.sh_keyboard_key_f')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': 'search_order',
                            'sh_shortcut_screen_type': 'order_screen', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        key_id = self.env.ref(
            'sh_pos_keyboard_shortcut.sh_keyboard_key_Insert')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': 'add_new_order',
                            'sh_shortcut_screen_type': 'all', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        key_id = self.env.ref(
            'sh_pos_keyboard_shortcut.sh_keyboard_key_control')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        key_id = self.env.ref(
            'sh_pos_keyboard_shortcut.sh_keyboard_key_delete')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': 'destroy_current_order',
                            'sh_shortcut_screen_type': 'all', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        key_id = self.env.ref(
            'sh_pos_keyboard_shortcut.sh_keyboard_key_delete')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': 'delete_orderline',
                            'sh_shortcut_screen_type': 'product_screen', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        key_id = self.env.ref(
            'sh_pos_keyboard_shortcut.sh_keyboard_key_arrow_up')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': 'select_up_orderline',
                            'sh_shortcut_screen_type': 'product_screen', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        key_id = self.env.ref(
            'sh_pos_keyboard_shortcut.sh_keyboard_key_arrow_down')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': 'select_down_orderline',
                            'sh_shortcut_screen_type': 'product_screen', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        key_id = self.env.ref('sh_pos_keyboard_shortcut.sh_keyboard_key_f')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': 'search_customer',
                            'sh_shortcut_screen_type': 'customer_screen', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        key_id = self.env.ref(
            'sh_pos_keyboard_shortcut.sh_keyboard_key_arrow_up')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': 'select_up_customer',
                            'sh_shortcut_screen_type': 'customer_screen', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        key_id = self.env.ref(
            'sh_pos_keyboard_shortcut.sh_keyboard_key_arrow_down')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': 'select_down_customer',
                            'sh_shortcut_screen_type': 'customer_screen', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        key_id = self.env.ref('sh_pos_keyboard_shortcut.sh_keyboard_key_Enter')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': 'set_customer',
                            'sh_shortcut_screen_type': 'customer_screen', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        key_id = self.env.ref('sh_pos_keyboard_shortcut.sh_keyboard_key_e')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': 'edit_customer',
                            'sh_shortcut_screen_type': 'customer_screen', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        key_id = self.env.ref('sh_pos_keyboard_shortcut.sh_keyboard_key_s')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': 'save_customer',
                            'sh_shortcut_screen_type': 'customer_screen', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        key_id = self.env.ref('sh_pos_keyboard_shortcut.sh_keyboard_key_+')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': 'create_customer',
                            'sh_shortcut_screen_type': 'customer_screen', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        key_id = self.env.ref('sh_pos_keyboard_shortcut.sh_keyboard_key_shift')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        key_id = self.env.ref(
            'sh_pos_keyboard_shortcut.sh_keyboard_key_delete')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': 'delete_payment_line',
                            'sh_shortcut_screen_type': 'payment_screen', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        key_id = self.env.ref(
            'sh_pos_keyboard_shortcut.sh_keyboard_key_arrow_up')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': 'select_up_payment_line',
                            'sh_shortcut_screen_type': 'payment_screen', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        key_id = self.env.ref(
            'sh_pos_keyboard_shortcut.sh_keyboard_key_arrow_down')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': 'select_down_payment_line',
                            'sh_shortcut_screen_type': 'payment_screen', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        key_id = self.env.ref('sh_pos_keyboard_shortcut.sh_keyboard_key_F10')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': '+10',
                            'sh_shortcut_screen_type': 'payment_screen', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        key_id = self.env.ref('sh_pos_keyboard_shortcut.sh_keyboard_key_F2')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': '+20',
                            'sh_shortcut_screen_type': 'payment_screen', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        key_id = self.env.ref('sh_pos_keyboard_shortcut.sh_keyboard_key_F5')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': '+50',
                            'sh_shortcut_screen_type': 'payment_screen', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        key_id = self.env.ref(
            'sh_pos_keyboard_shortcut.sh_keyboard_key_arrow_up')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': 'select_up_order',
                            'sh_shortcut_screen_type': 'order_screen', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        key_id = self.env.ref(
            'sh_pos_keyboard_shortcut.sh_keyboard_key_arrow_down')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': 'select_down_order',
                            'sh_shortcut_screen_type': 'order_screen', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        key_id = self.env.ref('sh_pos_keyboard_shortcut.sh_keyboard_key_Enter')
        temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
            {'sh_key_ids': key_id.id})
        key_list.append(temp_key_id.id)
        vals.append((0, 0, {'sh_shortcut_screen': 'select_order',
                            'sh_shortcut_screen_type': 'order_screen', 'sh_key_ids': [(6, 0, key_list)]}))
        key_list = []

        res.update({'sh_shortcut_keys_screen': vals})
        vals = []
        payment_method = self.env['pos.payment.method'].search([])
        if payment_method and len(payment_method) > 0:
            for each_payment_method in payment_method:
                name = each_payment_method.name[0]
                key_id = self.env['sh.keyboard.key'].search(
                    [('name', '=', name)])
                temp_key_id = self.env['sh.keyboard.key.temp'].sudo().create(
                    {'sh_key_ids': key_id.id})
                key_list.append(temp_key_id.id)
                vals.append((0, 0, {'payment_method_id': each_payment_method.id,
                                    'sh_payment_shortcut_screen_type': 'payment_screen', 'sh_key_ids': [(6, 0, key_list)]}))
                key_list = []

        res.update({'sh_payment_shortcut_keys_screen': vals})

        return res
