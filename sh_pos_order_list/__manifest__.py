# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
{
    "name": "Point Of Sale Order List",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "point of sale",
    "license": "OPL-1",
    "summary": "POS Restaurant Sync Restaurant order POS Order List POS All Order List on POS screen POS Frontend Orders Management POS Order management POS Order List Management Manage point of sale order Current Session pos order reprint odoo",
    "description": """Currently, in odoo there is well designed and precisely managed POS system available. But one thing that everyone wanted in pos is the current session order list on POS Main Screen. The main reason behind this feature is you can easy to see previous orders, easy to do re-order, re-print orders without closing the current session.""",
    "version": "15.0.4",
    "depends": ["point_of_sale"],
    "application": True,
    "data": [
        'views/pos_config.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'sh_pos_order_list/static/src/js/action_button.js',
            'sh_pos_order_list/static/src/js/db.js',
            'sh_pos_order_list/static/src/js/models.js',
            'sh_pos_order_list/static/src/js/order_line.js',
            'sh_pos_order_list/static/src/js/screen.js',
            'sh_pos_order_list/static/src/js/jquery.simplePagination.js',
            'sh_pos_order_list/static/src/css/pos.css',
            'sh_pos_order_list/static/src/css/simplePagination.css',
        ],
        'web.assets_qweb': [
            'sh_pos_order_list/static/src/xml/action_button.xml',
            'sh_pos_order_list/static/src/xml/screen.xml',
        ],
    },
    "images": ["static/description/background.png", ],
    "auto_install": False,
    "price": 25,
    "installable": True,
}
