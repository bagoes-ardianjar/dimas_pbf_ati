# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

{
    "name": "Point Of Sale Order Sync",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "point of sale",
    "license": "OPL-1",
    "summary": "POS Restaurant Sync Point Of Sale sync Order point of sale reprint POS Order Sync repeat order reorder reprint POS Order repeat point of sales reorder POS Sync eCommerce Orders POS Sync restaurant order pos order reprint Odoo",
    "description": """This module provide an amazing feature is sync pos order with multiple sessions. With this module you can send, receive, cancel, pay orders with other session. Let’s understand in a native example.
Restaurant: In the restaurant, there are three different people like one who take orders and send them to the kitchen(the kitchen is the second user) which is receive the order and the last one is the cashier, which pays the bills. basically, in this flow, there are one who send orders and another who receive orders.
Packing: In the packing business, there is more than one user like one who takes orders and sends them to another team who packs the order and ready for delivery to the cashier who pays the bill and serves the order to the customer.""",
    "version": "15.0.4",
    "depends": ["point_of_sale", "sh_pos_order_list"],
    "application": True,
    "data": [
        'views/pos_config.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'sh_pos_order_sync/static/src/js/action_button.js',
            'sh_pos_order_sync/static/src/js/chrome.js',
            'sh_pos_order_sync/static/src/js/db.js',
            'sh_pos_order_sync/static/src/js/models.js',
            'sh_pos_order_sync/static/src/js/popup.js',
            'sh_pos_order_sync/static/src/js/screen.js',
            'sh_pos_order_sync/static/src/css/pos.css',
        ],
        'web.assets_qweb': [
            'sh_pos_order_sync/static/src/xml/action_button.xml',
            'sh_pos_order_sync/static/src/xml/popup.xml',
            'sh_pos_order_sync/static/src/xml/screen.xml',
        ],
    },
    "images": ["static/description/background.png"],
    "auto_install": False,
    "installable": True,
    "price": 50,
    "currenecy": "EUR"
}
