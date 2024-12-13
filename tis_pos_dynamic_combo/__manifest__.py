# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd. - ©
# Technaureus Info Solutions Pvt. Ltd 2022. All rights reserved.

{
    'name': 'Pos Dynamic Combo Creation',
    'version': '15.0.0.4',
    'category': 'point_of_sale',
    'summary': 'POS Dynamic Combo/POS Combo Creation',
    'author': 'Technaureus Info Solutions Pvt. Ltd.',

    'description': """
    This module contains  the features of Pos Dynamic Combo.
    """,
    'sequence': 10,
    'price': 100,
    'currency': 'EUR',
    'website': 'http://www.technaureus.com',
    'depends': ['point_of_sale', 'product'],
    'images': ['images/main_screenshot.png'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
        'views/pos_order_line.xml',

    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'assets': {
        'point_of_sale.assets': [
            'tis_pos_dynamic_combo/static/src/css/style.css',
            'tis_pos_dynamic_combo/static/src/js/order.js',
            'tis_pos_dynamic_combo/static/src/js/ComboProduct.js',
            'tis_pos_dynamic_combo/static/src/js/ComboProductPopup.js',
            'tis_pos_dynamic_combo/static/src/js/ProductLists.js',
            'tis_pos_dynamic_combo/static/src/js/Models.js',
        ],
        'web.assets_qweb': [
            'tis_pos_dynamic_combo/static/src/xml/**/*',
        ],
    },
    'license': 'Other proprietary',
}
