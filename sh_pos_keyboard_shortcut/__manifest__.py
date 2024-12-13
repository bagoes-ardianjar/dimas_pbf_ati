# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
{
    "name": "Point Of Sale Keyboard Shortcut",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Point of Sale",
    "license": "OPL-1",
    "summary": "POS Keyboard Shortcut,Point Of Sale Keyboard Shortcuts,Custom POS Keyboard Shortcut,Default POS Keyboard Shortcut,Global POS Keyboard Shortcut,POS Shortcut Key Access,Set POS shortcut key,Short Cut Key Board,Point Of Sale Shortcut Odoo",
    "description": """Do you want to enhance POS with keyboard shortcuts? Using this module you can manage keyboard shortcuts for point of sale. You can create various keyboard shortcuts and use them in the running session of the POS. So POS users can perform operations effectively and quickly using keyboard shortcuts.""",
    "version": "15.0.2",
    "depends": ["point_of_sale"],
    "application": True,
    "data": [
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/pos_config.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'sh_pos_keyboard_shortcut/static/src/css/pos.css',
            'sh_pos_keyboard_shortcut/static/src/js/action_button.js',
            'sh_pos_keyboard_shortcut/static/src/js/popup.js',
            'sh_pos_keyboard_shortcut/static/src/js/pos_quick_order.js',
        ],
        'web.assets_qweb': [
            'sh_pos_keyboard_shortcut/static/src/xml/action_button.xml',
            'sh_pos_keyboard_shortcut/static/src/xml/popup.xml',
        ],
    },
    "images": ["static/description/background.png", ],
    "auto_install": False,
    "installable": True,
    "price": "25",
    "currency": "EUR"
}
